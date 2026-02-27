from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from api import serializer as api_serializer
from rest_framework.views import APIView
from rest_framework import status, generics
from collections import defaultdict
import requests
import xmlrpc.client
from rest_framework.permissions import AllowAny, IsAuthenticated
from useauth.models import User, Perfil
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken, TokenError 
from django.http import JsonResponse, HttpResponse
import pandas as pd 
from io import BytesIO 
import json

class MyTokenObtainPairView(TokenObtainPairView):

    serializer_class = api_serializer.MyTokenObtainPairSerializer

class UsersList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = api_serializer.UserSerializer

class RegistroUsuarioView(generics.CreateAPIView):
    serializer_class = api_serializer.RegistroUsuarioSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Esto lanzará un error 400 si no es válido
        self.perform_create(serializer)  # Guarda el nuevo usuario y tutor
        return Response(serializer.data, status=status.HTTP_201_CREATED)


"""
@api_view(['GET'])
def obtener_cxc_aromotor(request):
    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"
    url = "https://aromotor.com"
    db = "aromotor"

    # --- Autenticación ---
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    cliente_filtro = request.query_params.get('cliente', None)
    comercial_filtro = request.query_params.get('comercial', None)
    femision_desde = request.query_params.get('emision_desde', None)
    femision_hasta = request.query_params.get('emision_hasta', None)
    fvenci_desde = request.query_params.get('vencimiento_desde', None)
    fvenci_hasta = request.query_params.get('vencimiento_hasta', None)

    dominio_facturas = [
        ('move_type', '=', 'out_invoice'),
        ('payment_state', 'in', ['not_paid', 'partial']),
        ('state', '=', 'posted')
    ]
    
    dominio_cheques = [
        ('payment_method_id.name', 'ilike', 'cheque'),
        ('state', '=', 'custody'),
    ]
    
    if cliente_filtro:
        dominio_facturas.append(('partner_id.name', 'ilike', cliente_filtro)) 
        dominio_cheques.append(('partner_id.name', 'ilike', cliente_filtro))

    if comercial_filtro:
        dominio_facturas.append(('invoice_user_id.name', 'ilike', comercial_filtro))

    if femision_desde:
        dominio_facturas.append(('invoice_date', '>=', femision_desde))
    if femision_hasta:
        dominio_facturas.append(('invoice_date', '<=', femision_hasta))

    if fvenci_desde:
        dominio_facturas.append(('invoice_date_due', '>=', fvenci_desde))
    if fvenci_hasta:
        dominio_facturas.append(('invoice_date_due', '<=', fvenci_hasta))

    # --- Opciones para la consulta de facturas ---
    options_facturas = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'amount_residual',
            'x_retention_id',  # Campos agregados para acceder a la retención
            'invoice_user_id' 
        ], 
        'order': 'invoice_date ASC'
    }

    if not (cliente_filtro or comercial_filtro or femision_desde or femision_hasta or fvenci_desde or fvenci_hasta):
        options_facturas['limit'] = 20

    # --- Opciones para la consulta de cheques ---
    options_cheques = {'fields': ['id', 'name', 'amount', 'x_payment_invoice_ids', 'state', 'x_check_inbound_number']}
    
    if not (cliente_filtro or comercial_filtro):
        options_cheques['limit'] = 20

    # --- 1. Obtener facturas pendientes ---
    facturas = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_facturas],
        options_facturas
    )

    ids_facturas = [f['id'] for f in facturas]

    # --- Obtener valores de retención desde account.move.retention ---
    retention_ids = [f['x_retention_id'][0] for f in facturas if f.get('x_retention_id')]  # Extraer IDs únicos de retención
    retenciones = {}
    if retention_ids:
        retenciones_data = models.execute_kw(
            db, uid, contraseña,
            'account.move.retention', 'search_read',  # Consulta al modelo de retenciones
            [[('id', 'in', retention_ids)]],
            {'fields': ['id', 'retention_total', 'retention_number']}  # Campos del total y número de retención
        )
        retenciones = {r['id']: {'total': r['retention_total'], 'number': r['retention_number']} for r in retenciones_data}  # Diccionario: ID de retención -> dict con total y number

    # --- 2. Obtener líneas contables (cuotas) ---
    lineas = models.execute_kw(
        db, uid, contraseña,
        'account.move.line', 'search_read',
        [[
            ('move_id', 'in', ids_facturas),
            ('date_maturity', '!=', False),
        ]],
        {
            'fields': [
                'move_id', 'name', 'account_id',
                'debit', 'credit', 'balance',
                'amount_residual', 'date_maturity'
            ]
        }
    )

    # --- 3. Obtener cheques en custodia (optimizado: una sola consulta batch para facturas relacionadas) ---
    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_cheques],
        options_cheques
    )

    # Después de obtener 'pagos', recolecta todos los IDs de x_payment_invoice_ids
    all_invoice_ids = []
    for pago in pagos:
        all_invoice_ids.extend(pago.get('x_payment_invoice_ids', []))
    all_invoice_ids = list(set(all_invoice_ids))  # Eliminar duplicados

    # Una sola consulta para todas las facturas relacionadas
    facturas_relacionadas_dict = {}
    if all_invoice_ids:
        facturas_relacionadas_data = models.execute_kw(
            db, uid, contraseña,
            'account.payment.invoice', 'search_read',
            [[('id', 'in', all_invoice_ids), ('to_pay', '=', True)]],
            {'fields': ['id', 'move_name', 'invoice_date', 'amount_reconcile', 'to_pay']}
        )
        # Crea un dict para mapear: {id: data}
        facturas_relacionadas_dict = {fr['id']: fr for fr in facturas_relacionadas_data}

    # Ahora construye la lista de cheques usando el dict
    cheques = []
    for pago in pagos:
        ids_facturas = pago.get('x_payment_invoice_ids', [])
        facturas_relacionadas = [facturas_relacionadas_dict.get(fid) for fid in ids_facturas if fid in facturas_relacionadas_dict]
        cheques.append({
            "pago": {
                "id": pago['id'],
                "numero": pago['name'],
                "monto": pago['amount'],
                "estado": pago['state'],
                "ncheque": pago['x_check_inbound_number'],
                "facturas": facturas_relacionadas
            },
        })

    estado_cuentas = defaultdict(lambda: {'facturas': []})

    # Facturas
    for f in facturas:
        partner_id, partner_name = f['partner_id'] if f['partner_id'] else (None, 'Sin Cliente')
        comercial_id, comercial_name = f['invoice_user_id'] if f['invoice_user_id'] else (None, 'Sin Comercial')
        retention_id = f.get('x_retention_id', [None])[0] if f.get('x_retention_id') else None
        retention_value = retenciones.get(retention_id, {'total': 0, 'number': ''}) if retention_id else {'total': 0, 'number': ''}  # Obtener dict de retención
        estado_cuentas[partner_name]['facturas'].append({
            'id': f['id'],
            'numero': f['name'],
            'fecha': f['invoice_date'],
            'total': f['amount_total'],
            'pendiente': f['amount_residual'],
            'retencion_total': retention_value['total'],  # Total de la retención
            'retencion_numero': retention_value['number'],  # Número de la retención
            'comercial': comercial_name,
            'cuotas': [],
            'cheques': []
        })

    # Cuotas (líneas contables)
    for l in lineas:
        move_id = l['move_id'][0] if l['move_id'] else None
        for partner, datos in estado_cuentas.items():
            for factura in datos['facturas']:
                if factura['id'] == move_id:
                    factura['cuotas'].append({
                        'descripcion': l['name'],
                        'vencimiento': l.get('date_maturity'),
                        'residual': l.get('amount_residual', 0),
                        'debit': l.get('debit', 0),
                        'credit': l.get('credit', 0)
                    })
    try:
        for cheque in cheques:
            for fact_rel in cheque['pago'].get('facturas', []):
                move_name = fact_rel.get('move_name')
                if move_name:
                    for partner, datos in estado_cuentas.items():
                        for factura in datos['facturas']:
                            if str(factura['numero']) == str(move_name):
                                factura['cheques'].append(cheque['pago'])
    except Exception as e:
        print(f"    Error: {e}")

    cxc = [
        {
            'cliente': cliente,
            'facturas': datos['facturas']
        }
        for cliente, datos in estado_cuentas.items()
    ]
        
    return Response(cxc)
"""

class EditarUsuarioView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = api_serializer.UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

class ListarPerfilesView(generics.ListAPIView):
    queryset = Perfil.objects.all()
    serializer_class = api_serializer.PerfilSerializer  # Necesitas este serializer
    # permission_classes = [IsAuthenticated]  # O ajusta según permisos


class CrearUsuarioSinPasswordView(generics.CreateAPIView):
    serializer_class = api_serializer.CrearUsuarioSinPasswordSerializer
    # permission_classes = [IsAuthenticated]  # Solo admins pueden crear usuarios
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generar token JWT para set password
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        token = refresh.access_token  # Obtener el access token como objeto (no string aún)
        
        # Agregar campos adicionales al token (ej. username y full_name)
        token['username'] = user.username
        token['full_name'] = user.full_name
        token['email'] = user.email  # Opcional, si lo quieres
        
        # Convertir a string para el enlace
        token_str = str(token)
        # Generar el enlace completo
        enlace = f"{settings.FRONTEND_URL}/set-password?token={token}"
        
        # Devolver el enlace en la respuesta (sin enviar email)
        return Response({
            'message': 'Usuario creado exitosamente',
            'enlace_cambiar_contraseña': enlace,
            'usuario': serializer.data
        }, status=status.HTTP_201_CREATED)
    
class SetPasswordView(generics.GenericAPIView):
    serializer_class = api_serializer.SetPasswordSerializer
    permission_classes = [AllowAny]  # Cualquiera con el token puede acceder
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Decodificar token para obtener user_id
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)
            
            # Actualizar contraseña
            user.set_password(new_password)
            user.save()
            
            return Response({'message': 'Contraseña actualizada exitosamente'}, status=status.HTTP_200_OK)
        except (TokenError, User.DoesNotExist):
            return Response({'error': 'Token inválido o expirado'}, status=status.HTTP_400_BAD_REQUEST)

class GenerarEnlaceResetView(APIView):
    # permission_classes = [IsAuthenticated]  # Solo admins pueden generar enlaces
    # serializer_class = api_serializer.GenerarEnlaceResetSerializer  # Opcional, si quieres validación
    
    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Generar token JWT para reset password
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        token = refresh.access_token
        
        # Agregar campos opcionales al token (ej. username para mostrar en frontend)
        token['username'] = user.username
        token['full_name'] = user.full_name
        
        token_str = str(token)
        
        # Generar el enlace
        enlace = f"{settings.FRONTEND_URL}/set-password?token={token_str}"
        
        return Response({
            'message': f'Enlace generado para {user.username}',
            'enlace_cambiar_contraseña': enlace,
            'usuario': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)
    
#FUNCION DE CONEXION CON ODOO
def odoo_connection():
    url = settings.ODOO_URL
    db = settings.ODOO_DB
    usuario = settings.ODOO_USER
    contraseña = settings.ODOO_PASSWORD

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    
    if not uid:
        return None, None, None, None
    
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    return uid, models, db, contraseña

@api_view(['GET'])
def obtener_cartera_completa(request):
    
    uid, models, db, contraseña = odoo_connection()
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    cliente_filtro = request.query_params.get('cliente', None)
    comercial_filtro = request.query_params.get('comercial', None)
    femision_desde = request.query_params.get('emision_desde', None)
    femision_hasta = request.query_params.get('emision_hasta', None)
    fvenci_desde = request.query_params.get('vencimiento_desde', None)
    fvenci_hasta = request.query_params.get('vencimiento_hasta', None)

    dominio_facturas = [
        ('move_type', '=', 'out_invoice'),
        ('payment_state', 'in', ['not_paid', 'partial']),
        ('state', '=', 'posted')
    ]
    
    dominio_cheques = [
        ('payment_method_id.name', 'ilike', 'cheque'),
        ('state', '=', 'custody'),
    ]
    
    if cliente_filtro:
        dominio_facturas.append(('partner_id.name', 'ilike', cliente_filtro)) 
        dominio_cheques.append(('partner_id.name', 'ilike', cliente_filtro))

    if comercial_filtro:
        dominio_facturas.append(('invoice_user_id.name', 'ilike', comercial_filtro))

    if femision_desde:
        dominio_facturas.append(('invoice_date', '>=', femision_desde))
    if femision_hasta:
        dominio_facturas.append(('invoice_date', '<=', femision_hasta))

    if fvenci_desde:
        dominio_facturas.append(('invoice_date_due', '>=', fvenci_desde))
    if fvenci_hasta:
        dominio_facturas.append(('invoice_date_due', '<=', fvenci_hasta))

    # --- Opciones para la consulta de facturas ---
    options_facturas = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'amount_residual',
            'x_retention_id',  # Campos agregados para acceder a la retención
            'invoice_user_id' 
        ],
        'order': 'invoice_date ASC'
    }

    # --- Opciones para la consulta de cheques ---
    options_cheques = {'fields': ['id', 'name', 'amount', 'x_payment_invoice_ids', 'state', 'x_check_inbound_number']}

    # --- 1. Obtener facturas pendientes ---
    facturas = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_facturas],
        options_facturas
    )

    ids_facturas = [f['id'] for f in facturas]

    # --- Obtener valores de retención desde account.move.retention ---
    retention_ids = [f['x_retention_id'][0] for f in facturas if f.get('x_retention_id')]  # Extraer IDs únicos de retención
    retenciones = {}
    if retention_ids:
        retenciones_data = models.execute_kw(
            db, uid, contraseña,
            'account.move.retention', 'search_read',  # Consulta al modelo de retenciones
            [[('id', 'in', retention_ids)]],
            {'fields': ['id', 'retention_total', 'retention_number']}  # Campos del total y número de retención
        )
        retenciones = {r['id']: {'total': r['retention_total'], 'number': r['retention_number']} for r in retenciones_data}  # Diccionario: ID de retención -> dict con total y number

    # --- 2. Obtener líneas contables (cuotas) ---
    lineas = models.execute_kw(
        db, uid, contraseña,
        'account.move.line', 'search_read',
        [[
            ('move_id', 'in', ids_facturas),
            ('date_maturity', '!=', False),
        ]],
        {
            'fields': [
                'move_id', 'name', 'account_id',
                'debit', 'credit', 'balance',
                'amount_residual', 'date_maturity'
            ]
        }
    )

    # --- 3. Obtener cheques en custodia (optimizado: una sola consulta batch para facturas relacionadas) ---
    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_cheques],
        options_cheques
    )

    # Después de obtener 'pagos', recolecta todos los IDs de x_payment_invoice_ids
    all_invoice_ids = []
    for pago in pagos:
        all_invoice_ids.extend(pago.get('x_payment_invoice_ids', []))
    all_invoice_ids = list(set(all_invoice_ids))  # Eliminar duplicados

    # Una sola consulta para todas las facturas relacionadas
    facturas_relacionadas_dict = {}
    if all_invoice_ids:
        facturas_relacionadas_data = models.execute_kw(
            db, uid, contraseña,
            'account.payment.invoice', 'search_read',
            [[('id', 'in', all_invoice_ids), ('to_pay', '=', True)]],
            {'fields': ['id', 'move_name', 'invoice_date', 'amount_reconcile', 'to_pay']}
        )
        # Crea un dict para mapear: {id: data}
        facturas_relacionadas_dict = {fr['id']: fr for fr in facturas_relacionadas_data}

    # Ahora construye la lista de cheques usando el dict
    cheques = []
    for pago in pagos:
        ids_facturas = pago.get('x_payment_invoice_ids', [])
        facturas_relacionadas = [facturas_relacionadas_dict.get(fid) for fid in ids_facturas if fid in facturas_relacionadas_dict]
        cheques.append({
            "pago": {
                "id": pago['id'],
                "numero": pago['name'],
                "monto": pago['amount'],
                "estado": pago['state'],
                "ncheque": pago['x_check_inbound_number'],
                "facturas": facturas_relacionadas
            },
        })

    estado_cuentas = defaultdict(lambda: {'facturas': []})

    # Facturas
    for f in facturas:
        partner_id, partner_name = f['partner_id'] if f['partner_id'] else (None, 'Sin Cliente')
        comercial_id, comercial_name = f['invoice_user_id'] if f['invoice_user_id'] else (None, 'Sin Comercial')
        retention_id = f.get('x_retention_id', [None])[0] if f.get('x_retention_id') else None
        retention_value = retenciones.get(retention_id, {'total': 0, 'number': ''}) if retention_id else {'total': 0, 'number': ''}  # Obtener dict de retención
        estado_cuentas[partner_name]['facturas'].append({
            'id': f['id'],
            'numero': f['name'],
            'fecha': f['invoice_date'],
            'total': f['amount_total'],
            'pendiente': f['amount_residual'],
            'retencion_total': retention_value['total'],  # Total de la retención
            'retencion_numero': retention_value['number'],  # Número de la retención
            'comercial': comercial_name,
            'cuotas': [],
            'cheques': []
        })

    # Crear diccionarios para acceso rápido (optimización para asignar cuotas y cheques)
    factura_dict = {f['id']: f for partner in estado_cuentas.values() for f in partner['facturas']}
    numero_dict = {f['numero']: f for partner in estado_cuentas.values() for f in partner['facturas']}

    # Cuotas (líneas contables) - Usar dict para acceso O(1)
    for l in lineas:
        move_id = l['move_id'][0] if l['move_id'] else None
        if move_id in factura_dict:
            factura_dict[move_id]['cuotas'].append({
                'descripcion': l['name'],
                'vencimiento': l.get('date_maturity'),
                'residual': l.get('amount_residual', 0),
                'debit': l.get('debit', 0),
                'credit': l.get('credit', 0)
            })

    for cheque in cheques:
        pago = cheque['pago']
        for fact_rel in pago.get('facturas', []):
            move_name = fact_rel.get('move_name')
            if move_name in numero_dict:
                # Verificar que el cheque no esté ya agregado (evitar duplicados)
                cheques_ids_existentes = [c['id'] for c in numero_dict[move_name]['cheques']]
                if pago['id'] not in cheques_ids_existentes:
                    # Crear una copia del cheque con SOLO las facturas de este número
                    cheque_filtrado = {
                        **pago,
                        'facturas': [
                            f for f in pago['facturas']
                            if f.get('move_name') == move_name
                        ]
                    }
                    numero_dict[move_name]['cheques'].append(cheque_filtrado)

    cxc = [
        {
            'cliente': cliente,
            'facturas': datos['facturas']
        }
        for cliente, datos in estado_cuentas.items()
    ]
        
    def total_cheques_factura(factura):
        total = 0
        for cheque in factura['cheques']:
            for f in cheque['facturas']:
                total += f['amount_reconcile']
        return total

    # Antes del return Response(cxc):
    for cliente in cxc:
        cliente['facturas'] = [
            f for f in cliente['facturas']
            if round(total_cheques_factura(f), 2) < round(f['pendiente'], 2)
        ]

    cxc = [c for c in cxc if c['facturas']]

    return Response(cxc)


@api_view(['GET'])
def obtener_cxc_aromotor(request):
    
    uid, models, db, contraseña = odoo_connection()
    
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)
    
    cliente_filtro = request.query_params.get('cliente', None)
    comercial_filtro = request.query_params.get('comercial', None)
    femision_desde = request.query_params.get('emision_desde', None)
    femision_hasta = request.query_params.get('emision_hasta', None)
    fvenci_desde = request.query_params.get('vencimiento_desde', None)
    fvenci_hasta = request.query_params.get('vencimiento_hasta', None)

    dominio_facturas = [
        ('move_type', '=', 'out_invoice'),
        ('payment_state', 'in', ['not_paid', 'partial']),
        ('state', '=', 'posted')
    ]
    
    dominio_cheques = [
        ('payment_method_id.name', 'ilike', 'cheque'),
        ('state', '=', 'custody'),
    ]
    
    if cliente_filtro:
        dominio_facturas.append(('partner_id.name', 'ilike', cliente_filtro)) 
        dominio_cheques.append(('partner_id.name', 'ilike', cliente_filtro))

    if comercial_filtro:
        dominio_facturas.append(('invoice_user_id.name', 'ilike', comercial_filtro))

    if femision_desde:
        dominio_facturas.append(('invoice_date', '>=', femision_desde))

    if femision_hasta:
        dominio_facturas.append(('invoice_date', '<=', femision_hasta))

    if fvenci_desde:
        dominio_facturas.append(('invoice_date_due', '>=', fvenci_desde))

    if fvenci_hasta:
        dominio_facturas.append(('invoice_date_due', '<=', fvenci_hasta))

    # --- Opciones para la consulta de facturas ---
    options_facturas = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'amount_residual',
            'x_retention_id',  
            'invoice_user_id' 
        ],
        'order': 'invoice_date ASC'
    }

    if not (cliente_filtro or comercial_filtro or femision_desde or femision_hasta or fvenci_desde or fvenci_hasta):
        options_facturas['limit'] = 20

    # --- Opciones para la consulta de cheques ---
    options_cheques = {'fields': ['id', 'name', 'amount', 'x_payment_invoice_ids', 'state', 'x_check_inbound_number']}
    
    if not (cliente_filtro or comercial_filtro):
        options_cheques['limit'] = 20

    # --- 1. Obtener facturas pendientes ---
    facturas = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_facturas],
        options_facturas
    )

    ids_facturas = [f['id'] for f in facturas]

    # --- Obtener valores de retención desde account.move.retention ---
    retention_ids = [f['x_retention_id'][0] for f in facturas if f.get('x_retention_id')]  # Extraer IDs únicos de retención
    retenciones = {}
    if retention_ids:
        retenciones_data = models.execute_kw(
            db, uid, contraseña,
            'account.move.retention', 'search_read',  # Consulta al modelo de retenciones
            [[('id', 'in', retention_ids)]],
            {'fields': ['id', 'retention_total', 'retention_number']}  # Campos del total y número de retención
        )
        retenciones = {r['id']: {'total': r['retention_total'], 'number': r['retention_number']} for r in retenciones_data}  # Diccionario: ID de retención -> dict con total y number

    # --- 2. Obtener líneas contables (cuotas) ---
    lineas = models.execute_kw(
        db, uid, contraseña,
        'account.move.line', 'search_read',
        [[
            ('move_id', 'in', ids_facturas),
            ('date_maturity', '!=', False),
        ]],
        {
            'fields': [
                'move_id', 'name', 'account_id',
                'debit', 'credit', 'balance',
                'amount_residual', 'date_maturity'
            ]
        }
    )

    # --- 3. Obtener cheques en custodia ---
    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_cheques],
        options_cheques
    )

    # Después de obtener 'pagos', recolecta todos los IDs de x_payment_invoice_ids
    all_invoice_ids = []
    for pago in pagos:
        all_invoice_ids.extend(pago.get('x_payment_invoice_ids', []))
    all_invoice_ids = list(set(all_invoice_ids))  # Eliminar duplicados

    # Una sola consulta para todas las facturas relacionadas
    facturas_relacionadas_dict = {}
    if all_invoice_ids:
        facturas_relacionadas_data = models.execute_kw(
            db, uid, contraseña,
            'account.payment.invoice', 'search_read',
            [[('id', 'in', all_invoice_ids), ('to_pay', '=', True)]],
            {'fields': ['id', 'move_name', 'invoice_date', 'amount_reconcile', 'to_pay']}
        )
        # Crea un dict para mapear: {id: data}
        facturas_relacionadas_dict = {fr['id']: fr for fr in facturas_relacionadas_data}

    # Ahora construye la lista de cheques usando el dict
    cheques = []
    for pago in pagos:
        ids_facturas = pago.get('x_payment_invoice_ids', [])
        facturas_relacionadas = [facturas_relacionadas_dict.get(fid) for fid in ids_facturas if fid in facturas_relacionadas_dict]
        cheques.append({
            "pago": {
                "id": pago['id'],
                "numero": pago['name'],
                "monto": pago['amount'],
                "estado": pago['state'],
                "ncheque": pago['x_check_inbound_number'],
                "facturas": facturas_relacionadas
            },
        })

    estado_cuentas = defaultdict(lambda: {'facturas': []})

    # Facturas
    for f in facturas:
        partner_id, partner_name = f['partner_id'] if f['partner_id'] else (None, 'Sin Cliente')
        comercial_id, comercial_name = f['invoice_user_id'] if f['invoice_user_id'] else (None, 'Sin Comercial')
        retention_id = f.get('x_retention_id', [None])[0] if f.get('x_retention_id') else None
        retention_value = retenciones.get(retention_id, {'total': 0, 'number': ''}) if retention_id else {'total': 0, 'number': ''}  # Obtener dict de retención
        estado_cuentas[partner_name]['facturas'].append({
            'id': f['id'],
            'numero': f['name'],
            'fecha': f['invoice_date'],
            'total': f['amount_total'],
            'pendiente': f['amount_residual'],
            'retencion_total': retention_value['total'],  # Total de la retención
            'retencion_numero': retention_value['number'],  # Número de la retención
            'comercial': comercial_name,
            'cuotas': [],
            'cheques': []
        })

    # Crear diccionarios para acceso rápido (optimización para asignar cuotas y cheques)
    factura_dict = {f['id']: f for partner in estado_cuentas.values() for f in partner['facturas']}
    numero_dict = {f['numero']: f for partner in estado_cuentas.values() for f in partner['facturas']}

    # Cuotas (líneas contables) - Usar dict para acceso O(1)
    for l in lineas:
        move_id = l['move_id'][0] if l['move_id'] else None
        if move_id in factura_dict:
            factura_dict[move_id]['cuotas'].append({
                'descripcion': l['name'],
                'vencimiento': l.get('date_maturity'),
                'residual': l.get('amount_residual', 0),
                'debit': l.get('debit', 0),
                'credit': l.get('credit', 0)
            })

    # # Cheques - Usar dict para acceso O(1)
    # for cheque in cheques:
    #     for fact_rel in cheque['pago'].get('facturas', []):
    #         move_name = fact_rel.get('move_name')
    #         if move_name in numero_dict:
    #             numero_dict[move_name]['cheques'].append(cheque['pago'])

    # Cheques - Filtrar solo las facturas relevantes para cada factura
    for cheque in cheques:
        pago = cheque['pago']
        for fact_rel in pago.get('facturas', []):
            move_name = fact_rel.get('move_name')
            if move_name in numero_dict:
                # Verificar que el cheque no esté ya agregado (evitar duplicados)
                cheques_ids_existentes = [c['id'] for c in numero_dict[move_name]['cheques']]
                if pago['id'] not in cheques_ids_existentes:
                    # Crear una copia del cheque con SOLO las facturas de este número
                    cheque_filtrado = {
                        **pago,
                        'facturas': [
                            f for f in pago['facturas']
                            if f.get('move_name') == move_name
                        ]
                    }
                    numero_dict[move_name]['cheques'].append(cheque_filtrado)

    cxc = [
        {
            'cliente': cliente,
            'facturas': datos['facturas']
        }
        for cliente, datos in estado_cuentas.items()
    ]

    def total_cheques_factura(factura):
        total = 0
        for cheque in factura['cheques']:
            for f in cheque['facturas']:
                total += f['amount_reconcile']
        return total

    # Antes del return Response(cxc):
    for cliente in cxc:
        cliente['facturas'] = [
            f for f in cliente['facturas']
            if round(total_cheques_factura(f), 2) < round(f['pendiente'], 2)
        ]

    cxc = [c for c in cxc if c['facturas']]

    return Response(cxc)
        


@api_view(['GET'])
def reporte_cobranzas(request):
    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"
    url = "https://aromotor.com"
    db = "aromotor"

    # --- Autenticación ---
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    dominio_facturas = [
        ('move_type', '=', 'out_invoice'),
        ('store_id', '=', 1),
        ('state', '=', 'posted'),
        ('invoice_user_id', '!=', 'ALMACEN'),
        ('invoice_user_id', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('invoice_user_id', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('invoice_user_id', '!=', 'RELACIONADOS'),
        ('invoice_user_id', '!=', 'SANDOVAL GAMBOA GENESIS GABRIELA'),
        ('invoice_user_id', '!=', False),
        ('invoice_date', '>=', '2025-05-01')
    ]

    options_facturas = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'amount_residual', 'store_id',
            'x_retention_id', 'invoice_user_id'
        ],
        'order': 'invoice_date DESC',
    }

    facturas = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_facturas],
        options_facturas
    )

    if not facturas:
        return Response({"error": "No se encontraron facturas"}, status=404)

    # Crear un diccionario para mapear id de factura a su comercial y nombre
    facturas_dict = {
        f['id']: {
            'name': f['name'], 
            'comercial': f['invoice_user_id'][1] if f['invoice_user_id'] else "Sin comercial"
        } 
        for f in facturas
    }

    ids_facturas = list(facturas_dict.keys())

    lineas = models.execute_kw(
        db, uid, contraseña,
        'account.move.line', 'search_read',
        [[
            ('move_id', 'in', ids_facturas),
            ('date_maturity', '!=', False),
        ]],
        {
            'fields': [
                'move_id', 'name',
                'debit', 'credit', 'balance',
                'amount_residual', 'date_maturity'
            ]
        }
    )

    # Procesar y agrupar las líneas
    comerciales_temp = {}
    for linea in lineas:
        if linea['date_maturity']:
            move_id = linea['move_id'][0]
            if move_id in facturas_dict:
                comercial = facturas_dict[move_id]['comercial']
                año = linea['date_maturity'][:4]
                mes = linea['date_maturity'][5:7]
                valor = linea['debit']
                
                if comercial not in comerciales_temp:
                    comerciales_temp[comercial] = {}
                if año not in comerciales_temp[comercial]:
                    comerciales_temp[comercial][año] = {}
                if mes not in comerciales_temp[comercial][año]:
                    comerciales_temp[comercial][año][mes] = {"esperado": 0}
                
                comerciales_temp[comercial][año][mes]["esperado"] += valor

    # Reconstruir con orden: comerciales -> años -> meses ordenados
    comerciales = {}

    for comercial in sorted(comerciales_temp.keys()):
        comerciales[comercial] = {}
        total_vendedor = 0
        
        for año in sorted(comerciales_temp[comercial].keys()):
            comerciales[comercial][año] = {}
            
            # Ordenar meses e insertar en orden
            for mes in sorted(comerciales_temp[comercial][año].keys()):
                comerciales[comercial][año][mes] = comerciales_temp[comercial][año][mes]
                
                total_mes = comerciales[comercial][año][mes]["esperado"]
                comerciales[comercial][año][mes]["esperado"] = round(total_mes, 2)
                total_vendedor += total_mes
        
        comerciales[comercial]["total_vendedor"] = round(total_vendedor, 2)

    return Response(comerciales)


@api_view(['GET'])
def reporte_pagos(request):
    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"
    url = "https://aromotor.com"
    db = "aromotor"

    # --- Autenticación ---
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # Obtener pagos de account.payment con filtros
    dominio_pagos = [
        ('payment_type', '=', 'inbound'),  # Pagos recibidos (cobranzas)
        ('store_id', '=', 1),
        ('state', '!=', 'draft'),
        ('state', '!=', 'cancel'),
        ('x_collector_id', '!=', False),
        ('x_collector_id.name', '!=', 'RELACIONADOS'),
        ('x_collector_id.name', '!=', 'ALMACEN'),
        ('x_collector_id.name', '!=', 'ZAPATA ALAVA MELL FABIANA'),
        ('x_collector_id.name', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('x_collector_id.name', '!=', 'GARCIA GILER MELANI CINDY'),
        ('x_collector_id.name', '!=', 'PANEZO MENOSCAL EDUARDO LUIS'),
        ('x_collector_id.name', '!=', 'IMPORTADORA BRAVO GUTIERREZ BRAVGUT CIA LTDA'),
        ('x_collector_id.name', '!=', 'DAVILA CAMPOZANO LIVINGTONE EMILIO'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO PAMELA STEFANIA'),
        ('x_collector_id.name', '!=', 'LALANGUI LOPEZ MARIA JOSE'),
        ('x_collector_id.name', '!=', 'GUANIN YANCHAPAXI JANETH GABRIELA'),
        ('x_collector_id.name', '!=', 'IMPOR EXPORT AROMOTOR CIA. LTDA.'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO YERSON JAVIER'),
        ('x_collector_id.name', '!=', 'PARRA YEPEZ VICTORIA ANTONIETA'),
        ('x_collector_id.name', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('x_collector_id.name', '!=', 'CONTRERAS CORONADO LEIDY LORENA'),
        ('date', '>=', '2025-01-01')
    ]

    options_pagos = {
        'fields': [
            'id', 'name', 'partner_id', 'date',
            'amount', 'store_id', 
            'x_retention_id', 'x_collector_id'
        ],
        'order': 'date DESC',
    }

    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_pagos],
        options_pagos
    )

    if not pagos:
        return Response({"error": "No se encontraron pagos"}, status=404)

    # Procesar y agrupar pagos por cobrador, año, mes
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'cobrado': 0})))

    for pago in pagos:
        cobrador = pago['x_collector_id'][1] if pago['x_collector_id'] else "Sin cobrador"
        fecha = pago['date']
        año = fecha[:4]
        mes = fecha[5:7]
        monto = pago['amount']
        
        # Sumar directamente al total cobrado
        grouped[cobrador][año][mes]['cobrado'] += monto

    # Convertir a dict normal para salida, ordenando cobradores, años y meses alfabéticamente/numericamente
    resultado = {}
    for cobrador in sorted(grouped.keys()):
        resultado[cobrador] = {}
        for año in sorted(grouped[cobrador].keys()):
            resultado[cobrador][año] = {}
            for mes in sorted(grouped[cobrador][año].keys()):
                resultado[cobrador][año][mes] = grouped[cobrador][año][mes]

    return Response(resultado)



@api_view(['GET'])
def reporte_notas_credito(request):
    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"
    url = "https://aromotor.com"
    db = "aromotor"

    # --- Autenticación ---
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # Obtener notas de crédito (out_refund) con filtros
    dominio_nc = [
        ('move_type', '=', 'out_refund'),  # Notas de crédito
        ('store_id', '=', 1),
        ('state', '=', 'posted'),
        ('invoice_user_id', '!=', 'ALMACEN'),
        ('invoice_user_id', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('invoice_user_id', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('invoice_user_id', '!=', 'RELACIONADOS'),
        ('invoice_user_id', '!=', 'SANDOVAL GAMBOA GENESIS GABRIELA'),
        ('invoice_user_id', '!=', False),
        ('invoice_date', '>=', '2025-01-01')
    ]

    options_nc = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'store_id', 'invoice_user_id'
        ],
        'order': 'invoice_date DESC',
    }

    notas_credito = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_nc],
        options_nc
    )

    if not notas_credito:
        return Response({"error": "No se encontraron notas de crédito"}, status=404)

    # Procesar y agrupar NC por comercial, año, mes
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'total_nc': 0})))

    for nc in notas_credito:
        comercial = nc['invoice_user_id'][1] if nc['invoice_user_id'] else "Sin comercial"
        fecha = nc['invoice_date']
        año = fecha[:4]
        mes = fecha[5:7]
        monto = nc['amount_total']
        
        # Sumar directamente al total de NC
        grouped[comercial][año][mes]['total_nc'] += monto

    # Reconstruir con orden: comerciales -> años -> meses ordenados
    resultado = {}
    
    for comercial in sorted(grouped.keys()):
        resultado[comercial] = {}
        total_vendedor = 0
        
        for año in sorted(grouped[comercial].keys()):
            resultado[comercial][año] = {}
            
            # Ordenar meses e insertar en orden
            for mes in sorted(grouped[comercial][año].keys()):
                resultado[comercial][año][mes] = grouped[comercial][año][mes]
                
                total_mes = resultado[comercial][año][mes]['total_nc']
                total_vendedor += total_mes
        
        resultado[comercial]["total_vendedor"] = round(total_vendedor, 2)

    return Response(resultado)




@api_view(['GET'])
def reporte_combinado(request):
    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"
    url = "https://aromotor.com"
    db = "aromotor"

    # --- Autenticación ---
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # --- Reporte Cobranzas (Esperado) ---
    dominio_facturas = [
        ('move_type', '=', 'out_invoice'),
        ('store_id', '=', 1),
        ('state', '=', 'posted'),
        ('invoice_user_id', '!=', 'ALMACEN'),
        ('invoice_user_id', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('invoice_user_id', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('invoice_user_id', '!=', 'RELACIONADOS'),
        ('invoice_user_id', '!=', 'SANDOVAL GAMBOA GENESIS GABRIELA'),
        ('invoice_user_id', '!=', False),
        ('invoice_date', '>=', '2025-05-01'),
        ('invoice_date', '<=', '2026-01-31'),
    ]

    options_facturas = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'amount_residual', 'store_id',
            'x_retention_id', 'invoice_user_id'
        ],
        'order': 'invoice_date DESC',
    }

    facturas = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_facturas],
        options_facturas
    )

    facturas_dict = {}
    if facturas:
        facturas_dict = {
            f['id']: {
                'name': f['name'], 
                'comercial': f['invoice_user_id'][1] if f['invoice_user_id'] else "Sin comercial"
            } 
            for f in facturas
        }

        ids_facturas = list(facturas_dict.keys())

        lineas = models.execute_kw(
            db, uid, contraseña,
            'account.move.line', 'search_read',
            [[
                ('move_id', 'in', ids_facturas),
                ('date_maturity', '!=', False),
            ]],
            {
                'fields': [
                    'move_id', 'name',
                    'debit', 'credit', 'balance',
                    'amount_residual', 'date_maturity'
                ]
            }
        )

        esperado_temp = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'esperado': 0})))
        for linea in lineas:
            if linea['date_maturity']:
                move_id = linea['move_id'][0]
                if move_id in facturas_dict:
                    comercial = facturas_dict[move_id]['comercial']
                    año = linea['date_maturity'][:4]
                    mes = linea['date_maturity'][5:7]
                    valor = linea['debit']
                    esperado_temp[comercial][año][mes]['esperado'] += valor

    # --- Reporte Pagos (Cobrado) ---
    dominio_pagos = [
        ('payment_type', '=', 'inbound'),
        ('store_id', '=', 1),
        ('state', '!=', 'draft'),
        ('state', '!=', 'cancel'),
        ('x_collector_id', '!=', False),
        ('x_collector_id.name', '!=', 'RELACIONADOS'),
        ('x_collector_id.name', '!=', 'ALMACEN'),
        ('x_collector_id.name', '!=', 'ZAPATA ALAVA MELL FABIANA'),
        ('x_collector_id.name', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('x_collector_id.name', '!=', 'GARCIA GILER MELANI CINDY'),
        ('x_collector_id.name', '!=', 'PANEZO MENOSCAL EDUARDO LUIS'),
        ('x_collector_id.name', '!=', 'IMPORTADORA BRAVO GUTIERREZ BRAVGUT CIA LTDA'),
        ('x_collector_id.name', '!=', 'DAVILA CAMPOZANO LIVINGTONE EMILIO'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO PAMELA STEFANIA'),
        ('x_collector_id.name', '!=', 'LALANGUI LOPEZ MARIA JOSE'),
        ('x_collector_id.name', '!=', 'GUANIN YANCHAPAXI JANETH GABRIELA'),
        ('x_collector_id.name', '!=', 'IMPOR EXPORT AROMOTOR CIA. LTDA.'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO YERSON JAVIER'),
        ('x_collector_id.name', '!=', 'PARRA YEPEZ VICTORIA ANTONIETA'),
        ('x_collector_id.name', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('x_collector_id.name', '!=', 'CONTRERAS CORONADO LEIDY LORENA'),
        ('date', '>=', '2025-05-01'),
        ('date', '<=', '2026-01-31')
    ]

    options_pagos = {
        'fields': [
            'id', 'name', 'partner_id', 'date',
            'amount', 'store_id', 
            'x_retention_id', 'x_collector_id'
        ],
        'order': 'date DESC',
    }

    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_pagos],
        options_pagos
    )

    cobrado_temp = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'cobrado': 0})))
    if pagos:
        for pago in pagos:
            cobrador = pago['x_collector_id'][1] if pago['x_collector_id'] else "Sin cobrador"
            fecha = pago['date']
            año = fecha[:4]
            mes = fecha[5:7]
            monto = pago['amount']
            cobrado_temp[cobrador][año][mes]['cobrado'] += monto

    # --- Reporte Notas de Crédito (Total NC) ---
    dominio_nc = [
        ('move_type', '=', 'out_refund'),
        ('store_id', '=', 1),
        ('state', '=', 'posted'),
        ('invoice_user_id', '!=', 'ALMACEN'),
        ('invoice_user_id', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('invoice_user_id', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('invoice_user_id', '!=', 'RELACIONADOS'),
        ('invoice_user_id', '!=', 'SANDOVAL GAMBOA GENESIS GABRIELA'),
        ('invoice_user_id', '!=', False),
        ('invoice_date', '>=', '2025-05-01'),
        ('invoice_date', '>=', '2026-01-31')
    ]

    options_nc = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'store_id', 'invoice_user_id'
        ],
        'order': 'invoice_date DESC',
    }

    notas_credito = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_nc],
        options_nc
    )

    nc_temp = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'total_nc': 0})))
    if notas_credito:
        for nc in notas_credito:
            comercial = nc['invoice_user_id'][1] if nc['invoice_user_id'] else "Sin comercial"
            fecha = nc['invoice_date']
            año = fecha[:4]
            mes = fecha[5:7]
            monto = nc['amount_total']
            nc_temp[comercial][año][mes]['total_nc'] += monto

    # --- Combinar todos los datos ---
    # Usar un set para recopilar todos los comerciales únicos
    all_comerciales = set(esperado_temp.keys()) | set(cobrado_temp.keys()) | set(nc_temp.keys())

    resultado = {}
    for comercial in sorted(all_comerciales):
        resultado[comercial] = {}
        total_esperado = 0
        total_cobrado = 0
        total_nc = 0
        
        # Recopilar todos los años para este comercial
        all_years = set(esperado_temp[comercial].keys()) | set(cobrado_temp[comercial].keys()) | set(nc_temp[comercial].keys())
        
        for año in sorted(all_years):
            resultado[comercial][año] = {}
            
            # Recopilar todos los meses para este año
            all_months = set(esperado_temp[comercial][año].keys()) | set(cobrado_temp[comercial][año].keys()) | set(nc_temp[comercial][año].keys())
            
            for mes in sorted(all_months):
                esperado = esperado_temp[comercial][año][mes]['esperado']
                cobrado = cobrado_temp[comercial][año][mes]['cobrado']
                total_nc_mes = nc_temp[comercial][año][mes]['total_nc']
                
                resultado[comercial][año][mes] = {
                    'esperado': round(esperado, 2),
                    'cobrado': round(cobrado, 2),
                    'total_nc': round(total_nc_mes, 2)
                }
                
                total_esperado += esperado
                total_cobrado += cobrado
                total_nc += total_nc_mes
        
        # Agregar totales por vendedor (opcional, basado en códigos originales)
        resultado[comercial]["total_esperado"] = round(total_esperado, 2)
        resultado[comercial]["total_cobrado"] = round(total_cobrado, 2)
        resultado[comercial]["total_nc"] = round(total_nc, 2)

    return Response(resultado)
    

@api_view(['GET'])
def reporte_combinado_detalle(request):
    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"
    url = "https://aromotor.com"
    db = "aromotor"

    # --- Autenticación ---
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # --- Reporte Cobranzas (Esperado) ---
    dominio_facturas = [
        ('move_type', '=', 'out_invoice'),
        ('store_id', '=', 1),
        ('state', '=', 'posted'),
        ('invoice_user_id', '!=', 'ALMACEN'),
        ('invoice_user_id', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('invoice_user_id', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('invoice_user_id', '!=', 'RELACIONADOS'),
        ('invoice_user_id', '!=', 'SANDOVAL GAMBOA GENESIS GABRIELA'),
        ('invoice_user_id', '!=', False),
        ('invoice_date', '>=', '2025-05-01'),
        ('invoice_date', '<=', '2026-01-31'),
    ]

    options_facturas = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'amount_residual', 'store_id',
            'x_retention_id', 'invoice_user_id'
        ],
        'order': 'invoice_date DESC',
    }

    facturas = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_facturas],
        options_facturas
    )

    facturas_dict = {f['id']: f for f in facturas}
    ids_facturas = list(facturas_dict.keys())

    lineas = models.execute_kw(
        db, uid, contraseña,
        'account.move.line', 'search_read',
        [[
            ('move_id', 'in', ids_facturas),
            ('date_maturity', '!=', False),
        ]],
        {
            'fields': [
                'move_id', 'name',
                'debit', 'credit', 'balance',
                'amount_residual', 'date_maturity'
            ]
        }
    )

    esperado_por_vendedor = defaultdict(lambda: {'total_esperado': 0, 'facturas': []})
    for linea in lineas:
        if linea['date_maturity']:
            move_id = linea['move_id'][0]
            if move_id in facturas_dict:
                comercial = facturas_dict[move_id]['invoice_user_id'][1] if facturas_dict[move_id]['invoice_user_id'] else "Sin comercial"
                valor = linea['debit']
                esperado_por_vendedor[comercial]['total_esperado'] += valor
                esperado_por_vendedor[comercial]['facturas'].append({
                    'id': facturas_dict[move_id]['id'],
                    'name': facturas_dict[move_id]['name'],
                    'partner': facturas_dict[move_id]['partner_id'][1] if facturas_dict[move_id]['partner_id'] else "Sin partner",
                    'invoice_date': facturas_dict[move_id]['invoice_date'],
                    'amount_total': facturas_dict[move_id]['amount_total'],
                    'amount_residual': facturas_dict[move_id]['amount_residual'],
                    'date_maturity': linea['date_maturity'],
                    'debit': linea['debit']
                })

    # --- Reporte Pagos (Cobrado) ---
    dominio_pagos = [
        ('payment_type', '=', 'inbound'),
        ('store_id', '=', 1),
        ('state', '!=', 'draft'),
        ('state', '!=', 'cancel'),
        ('x_collector_id', '!=', False),
        ('x_collector_id.name', '!=', 'RELACIONADOS'),
        ('x_collector_id.name', '!=', 'ALMACEN'),
        ('x_collector_id.name', '!=', 'ZAPATA ALAVA MELL FABIANA'),
        ('x_collector_id.name', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('x_collector_id.name', '!=', 'GARCIA GILER MELANI CINDY'),
        ('x_collector_id.name', '!=', 'PANEZO MENOSCAL EDUARDO LUIS'),
        ('x_collector_id.name', '!=', 'IMPORTADORA BRAVO GUTIERREZ BRAVGUT CIA LTDA'),
        ('x_collector_id.name', '!=', 'DAVILA CAMPOZANO LIVINGTONE EMILIO'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO PAMELA STEFANIA'),
        ('x_collector_id.name', '!=', 'LALANGUI LOPEZ MARIA JOSE'),
        ('x_collector_id.name', '!=', 'GUANIN YANCHAPAXI JANETH GABRIELA'),
        ('x_collector_id.name', '!=', 'IMPOR EXPORT AROMOTOR CIA. LTDA.'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO YERSON JAVIER'),
        ('x_collector_id.name', '!=', 'PARRA YEPEZ VICTORIA ANTONIETA'),
        ('x_collector_id.name', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('x_collector_id.name', '!=', 'CONTRERAS CORONADO LEIDY LORENA'),
        ('date', '>=', '2025-05-01'),
        ('date', '<=', '2026-01-31')
    ]

    options_pagos = {
        'fields': [
            'id', 'name', 'partner_id', 'date',
            'amount', 'store_id', 
            'x_retention_id', 'x_collector_id',
            'x_payment_invoice_ids', 'reconciled_invoice_ids' 
        ],
        'order': 'date DESC',
    }

    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_pagos],
        options_pagos
    )

    # --- Recopilar IDs de x_payment_invoice_ids ---
    all_invoice_ids = []
    for pago in pagos:
        all_invoice_ids.extend(pago.get('x_payment_invoice_ids', []))
    all_invoice_ids = list(set(all_invoice_ids))

    # --- Recopilar IDs de reconciled_invoice_ids ---
    all_facturas_ids = []
    for pago in pagos:
        all_facturas_ids.extend(pago.get('reconciled_invoice_ids', []))
    all_facturas_ids = list(set(all_facturas_ids))

    # --- Consultar account.payment.invoice (para x_payment_invoice_ids) ---
    facturas_payment_dict = {}
    if all_invoice_ids:
        facturas_payment_data = models.execute_kw(
            db, uid, contraseña,
            'account.payment.invoice', 'search_read',
            [[('id', 'in', all_invoice_ids), ('to_pay', '=', True)]],
            {'fields': ['id', 'move_name', 'invoice_date', 'amount_reconcile', 'to_pay']}
        )
        facturas_payment_dict = {fr['id']: fr for fr in facturas_payment_data}

    # --- Consultar account.move (para reconciled_invoice_ids) ---
    facturas_move_dict = {}
    if all_facturas_ids:
        facturas_move_data = models.execute_kw(
            db, uid, contraseña,
            'account.move', 'search_read',
            [[('id', 'in', all_facturas_ids)]],
            {'fields': ['id', 'name', 'invoice_date', 'amount_total', 'amount_residual', 'state', 'partner_id']}
        )
        facturas_move_dict = {f['id']: f for f in facturas_move_data}

    # --- Armar cobrado por vendedor ---
    cobrado_por_vendedor = defaultdict(lambda: {'total_cobrado': 0, 'pagos': []})
    for pago in pagos:
        cobrador = pago['x_collector_id'][1] if pago['x_collector_id'] else "Sin cobrador"
        cobrado_por_vendedor[cobrador]['total_cobrado'] += pago['amount']

        facturas_del_pago = []

        # ✅ Primero intentar reconciled_invoice_ids
        if pago.get('reconciled_invoice_ids'):
            for inv_id in pago['reconciled_invoice_ids']:
                if inv_id in facturas_move_dict:
                    f = facturas_move_dict[inv_id]
                    facturas_del_pago.append({
                        'move_name': f.get('name', ''),
                        'invoice_date': f.get('invoice_date', ''),
                        'amount_reconcile': f.get('amount_total', 0),
                    })

        # ✅ Si no había nada, usar x_payment_invoice_ids como fallback
        elif pago.get('x_payment_invoice_ids'):
            for inv_id in pago['x_payment_invoice_ids']:
                if inv_id in facturas_payment_dict:
                    fr = facturas_payment_dict[inv_id]
                    facturas_del_pago.append({
                        'move_name': fr.get('move_name', ''),
                        'invoice_date': fr.get('invoice_date', ''),
                        'amount_reconcile': fr.get('amount_reconcile', 0),
                    })

        cobrado_por_vendedor[cobrador]['pagos'].append({
            'id': pago['id'],
            'name': pago['name'],
            'partner': pago['partner_id'][1] if pago['partner_id'] else "Sin partner",
            'date': pago['date'],
            'amount': pago['amount'],
            'facturas_relacionadas': facturas_del_pago
        })

    # --- Reporte Notas de Crédito (Total NC) ---
    dominio_nc = [
        ('move_type', '=', 'out_refund'),
        ('store_id', '=', 1),
        ('state', '=', 'posted'),
        ('invoice_user_id', '!=', 'ALMACEN'),
        ('invoice_user_id', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('invoice_user_id', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('invoice_user_id', '!=', 'RELACIONADOS'),
        ('invoice_user_id', '!=', 'SANDOVAL GAMBOA GENESIS GABRIELA'),
        ('invoice_user_id', '!=', False),
        ('invoice_date', '>=', '2025-05-01'),
        ('invoice_date', '<=', '2026-01-31')
    ]

    options_nc = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'store_id', 'invoice_user_id'
        ],
        'order': 'invoice_date DESC',
    }

    notas_credito = models.execute_kw(
        db, uid, contraseña,
        'account.move', 'search_read',
        [dominio_nc],
        options_nc
    )

    nc_por_vendedor = defaultdict(lambda: {'total_nc': 0, 'notas_credito': []})
    if notas_credito:
        for nc in notas_credito:
            comercial = nc['invoice_user_id'][1] if nc['invoice_user_id'] else "Sin comercial"
            monto = nc['amount_total']
            nc_por_vendedor[comercial]['total_nc'] += monto
            nc_por_vendedor[comercial]['notas_credito'].append({
                'id': nc['id'],
                'name': nc['name'],
                'partner': nc['partner_id'][1] if nc['partner_id'] else "Sin partner",
                'invoice_date': nc['invoice_date'],
                'amount_total': nc['amount_total']
            })

    # --- Combinar todos los datos por vendedor ---
    all_vendedores = set(esperado_por_vendedor.keys()) | set(cobrado_por_vendedor.keys()) | set(nc_por_vendedor.keys())

    resultado = {}
    for vendedor in sorted(all_vendedores):
        resultado[vendedor] = {
            'esperado': {
                'total': round(esperado_por_vendedor[vendedor]['total_esperado'], 2),
                'detalle': esperado_por_vendedor[vendedor]['facturas']
            },
            'cobrado': {
                'total': round(cobrado_por_vendedor[vendedor]['total_cobrado'], 2),
                'detalle': cobrado_por_vendedor[vendedor]['pagos']
            },
            'notas_credito': {
                'total': round(nc_por_vendedor[vendedor]['total_nc'], 2),
                'detalle': nc_por_vendedor[vendedor]['notas_credito']
            }
        }

    # --- Verificar si se solicita exportación a Excel ---
    if request.GET.get('export') == 'excel':
        data_esperado = []
        data_cobrado = []
        data_nc = []

        for vendedor, data in resultado.items():
            for factura in data['esperado']['detalle']:
                data_esperado.append({
                    'Vendedor': vendedor,
                    'ID Factura': factura['id'],
                    'Nombre': factura['name'],
                    'Cliente': factura['partner'],
                    'Fecha Factura': factura['invoice_date'],
                    'Monto Total': factura['amount_total'],
                    'Residual': factura['amount_residual'],
                    'Fecha Vencimiento': factura['date_maturity'],
                    'Débito': factura['debit']
                })

            # ← MODIFICADO: Ahora expande las facturas relacionadas en el Excel
            for pago in data['cobrado']['detalle']:
                base = {
                    'Vendedor': vendedor,
                    'ID Pago': pago['id'],
                    'Nombre': pago['name'],
                    'Cliente': pago['partner'],
                    'Fecha': pago['date'],
                    'Monto': pago['amount'],
                }
                if pago.get('facturas_relacionadas'):
                    for fr in pago['facturas_relacionadas']:
                        data_cobrado.append({
                            **base,
                            'Factura Relacionada': fr['move_name'],
                            'Fecha Factura': fr['invoice_date'],
                            'Monto Reconciliado': fr['amount_reconcile'],
                        })
                else:
                    data_cobrado.append({
                        **base,
                        'Factura Relacionada': '',
                        'Fecha Factura': '',
                        'Monto Reconciliado': '',
                    })

            for nc in data['notas_credito']['detalle']:
                data_nc.append({
                    'Vendedor': vendedor,
                    'ID NC': nc['id'],
                    'Nombre': nc['name'],
                    'Cliente': nc['partner'],
                    'Fecha': nc['invoice_date'],
                    'Monto Total': nc['amount_total']
                })

        df_esperado = pd.DataFrame(data_esperado)
        df_cobrado = pd.DataFrame(data_cobrado)
        df_nc = pd.DataFrame(data_nc)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_esperado.to_excel(writer, sheet_name='Esperado', index=False)
            df_cobrado.to_excel(writer, sheet_name='Cobrado', index=False)
            df_nc.to_excel(writer, sheet_name='Notas de Crédito', index=False)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=reporte_combinado.xlsx'
        return response

    return Response(resultado)




@api_view(['GET'])
def reporte_pagos_test(request):
    usuario = "steevenandresmaila@gmail.com"
    contraseña = "Vasodeagua11"
    url = "https://aromotor.com"
    db = "aromotor"

    # --- Autenticación ---
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, usuario, contraseña, {})
    if not uid:
        return Response({"error": "❌ Error de autenticación con Odoo"}, status=401)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    dominio_pagos = [
        ('payment_type', '=', 'inbound'),
        ('store_id', '=', 1),
        ('state', '!=', 'draft'),
        ('state', '!=', 'cancel'),
        ('x_collector_id', '!=', False),
        ('x_collector_id.name', '!=', 'RELACIONADOS'),
        ('x_collector_id.name', '!=', 'ALMACEN'),
        ('x_collector_id.name', '!=', 'ZAPATA ALAVA MELL FABIANA'),
        ('x_collector_id.name', '!=', 'MANCILLA MORENO DAX FELIPE'),
        ('x_collector_id.name', '!=', 'GARCIA GILER MELANI CINDY'),
        ('x_collector_id.name', '!=', 'PANEZO MENOSCAL EDUARDO LUIS'),
        ('x_collector_id.name', '!=', 'IMPORTADORA BRAVO GUTIERREZ BRAVGUT CIA LTDA'),
        ('x_collector_id.name', '!=', 'DAVILA CAMPOZANO LIVINGTONE EMILIO'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO PAMELA STEFANIA'),
        ('x_collector_id.name', '!=', 'LALANGUI LOPEZ MARIA JOSE'),
        ('x_collector_id.name', '!=', 'GUANIN YANCHAPAXI JANETH GABRIELA'),
        ('x_collector_id.name', '!=', 'IMPOR EXPORT AROMOTOR CIA. LTDA.'),
        ('x_collector_id.name', '!=', 'FARIAS SOLORZANO YERSON JAVIER'),
        ('x_collector_id.name', '!=', 'PARRA YEPEZ VICTORIA ANTONIETA'),
        ('x_collector_id.name', '!=', 'CALDERON CORNEJO SANDRA JOHANA'),
        ('x_collector_id.name', '!=', 'CONTRERAS CORONADO LEIDY LORENA'),
        ('date', '>=', '2025-01-01')
    ]

    options_pagos = {
        'fields': [
            'id', 'name', 'partner_id', 'date',
            'amount', 'store_id',
            'x_retention_id', 'x_collector_id',
            'x_payment_invoice_ids', 'reconciled_invoice_ids'
        ],
        'order': 'date DESC',
    }

    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_pagos],
        options_pagos
    )

    # --- Recopilar IDs de ambas fuentes por separado ---
    all_invoice_ids = []
    for pago in pagos:
        all_invoice_ids.extend(pago.get('x_payment_invoice_ids', []))
    all_invoice_ids = list(set(all_invoice_ids))

    all_facturas_ids = []
    for pago in pagos:
        all_facturas_ids.extend(pago.get('reconciled_invoice_ids', []))
    all_facturas_ids = list(set(all_facturas_ids))

    # --- Consultar account.payment.invoice (para x_payment_invoice_ids) ---
    facturas_payment_dict = {}
    if all_invoice_ids:
        facturas_payment_data = models.execute_kw(
            db, uid, contraseña,
            'account.payment.invoice', 'search_read',
            [[('id', 'in', all_invoice_ids), ('to_pay', '=', True)]],
            {'fields': ['id', 'move_name', 'invoice_date', 'amount_reconcile', 'to_pay']}
        )
        facturas_payment_dict = {fr['id']: fr for fr in facturas_payment_data}

    # --- Consultar account.move (para reconciled_invoice_ids) ---
    facturas_move_dict = {}
    if all_facturas_ids:
        facturas_move_data = models.execute_kw(
            db, uid, contraseña,
            'account.move', 'search_read',
            [[('id', 'in', all_facturas_ids)]],  # ✅ CORREGIDO: antes usaba all_invoice_ids
            {'fields': ['id', 'name', 'invoice_date', 'amount_total', 'amount_residual', 'state', 'partner_id']}
        )
        facturas_move_dict = {f['id']: f for f in facturas_move_data}

    # --- Armar resultado ---
    cobrado_por_vendedor = defaultdict(lambda: {'total_cobrado': 0, 'pagos': []})
    for pago in pagos:
        cobrador = pago['x_collector_id'][1] if pago['x_collector_id'] else "Sin cobrador"
        cobrado_por_vendedor[cobrador]['total_cobrado'] += pago['amount']

        facturas_del_pago = []

        # ✅ Primero intentar x_payment_invoice_ids
        if pago.get('x_payment_invoice_ids'):
            for inv_id in pago['x_payment_invoice_ids']:
                if inv_id in facturas_payment_dict:
                    fr = facturas_payment_dict[inv_id]
                    facturas_del_pago.append({
                        'move_name': fr.get('move_name', ''),
                        'invoice_date': fr.get('invoice_date', ''),
                        'amount_reconcile': fr.get('amount_reconcile', 0),
                    })

        # ✅ Si no había nada, usar reconciled_invoice_ids
        elif pago.get('reconciled_invoice_ids'):
            for inv_id in pago['reconciled_invoice_ids']:
                if inv_id in facturas_move_dict:
                    f = facturas_move_dict[inv_id]
                    facturas_del_pago.append({
                        'move_name': f.get('name', ''),
                        'invoice_date': f.get('invoice_date', ''),
                        'amount_reconcile': f.get('amount_total', 0),
                    })

        cobrado_por_vendedor[cobrador]['pagos'].append({
            'id': pago['id'],
            'name': pago['name'],
            'partner': pago['partner_id'][1] if pago['partner_id'] else "Sin partner",
            'date': pago['date'],
            'amount': pago['amount'],
            'facturas_relacionadas': facturas_del_pago
        })

    resultado = dict(cobrado_por_vendedor)

    # ✅ EXPORTAR A JSON
    exportar = request.query_params.get('export', None)
    if exportar == 'json':
        response = HttpResponse(
            json.dumps(resultado, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_pagos.json"'
        return response

    return Response(resultado)