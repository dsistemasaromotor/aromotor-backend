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
    


@api_view(['GET'])
def obtener_cartera_completa(request):
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

    # Cheques - Usar dict para acceso O(1)
    for cheque in cheques:
        for fact_rel in cheque['pago'].get('facturas', []):
            move_name = fact_rel.get('move_name')
            if move_name in numero_dict:
                numero_dict[move_name]['cheques'].append(cheque['pago'])

    cxc = [
        {
            'cliente': cliente,
            'facturas': datos['facturas']
        }
        for cliente, datos in estado_cuentas.items()
    ]
        
    return Response(cxc)


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

    # Cheques - Usar dict para acceso O(1)
    for cheque in cheques:
        for fact_rel in cheque['pago'].get('facturas', []):
            move_name = fact_rel.get('move_name')
            if move_name in numero_dict:
                numero_dict[move_name]['cheques'].append(cheque['pago'])

    cxc = [
        {
            'cliente': cliente,
            'facturas': datos['facturas']
        }
        for cliente, datos in estado_cuentas.items()
    ]
        
    return Response(cxc)
