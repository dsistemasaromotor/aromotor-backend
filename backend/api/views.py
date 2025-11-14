from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import status
from collections import defaultdict
import requests
import xmlrpc.client


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

    # --- Opciones para la consulta de facturas ---
    options_facturas = {
        'fields': [
            'id', 'name', 'partner_id', 'invoice_date',
            'amount_total', 'amount_residual',
            'x_retention_id'  # Campos agregados para acceder a la retención
        ], 
        'order': 'invoice_date ASC'
    }
    # Limitar a 20 facturas si no hay filtro de cliente
    if not cliente_filtro:
        options_facturas['limit'] = 20

    # --- Opciones para la consulta de cheques ---
    options_cheques = {'fields': ['id', 'name', 'amount', 'x_payment_invoice_ids', 'state', 'x_check_inbound_number']}
    # Limitar a 20 cheques si no hay filtro de cliente
    if not cliente_filtro:
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

    # --- 3. Obtener cheques en custodia (usando lógica de filtros corregida) ---
    pagos = models.execute_kw(
        db, uid, contraseña,
        'account.payment', 'search_read',
        [dominio_cheques],
        options_cheques
    )

    cheques = []

    for pago in pagos:
        facturas_relacionadas = []
        ids_facturas = pago.get('x_payment_invoice_ids', [])

        if ids_facturas:
            facturas_relacionadas = models.execute_kw(
                db, uid, contraseña,
                'account.payment.invoice', 'search_read',
                [[
                    ('id', 'in', ids_facturas),
                    ('to_pay', '=', True)
                ]],
                {'fields': [
                    'move_name', 'invoice_date','amount_reconcile','to_pay'
                ]}
            )

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