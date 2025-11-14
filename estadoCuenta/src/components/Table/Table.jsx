import { useState, useMemo, useEffect } from "react"
import { Search } from "lucide-react"
import { useSearch } from "../../hooks/useSearch"

const Table = ({data}) => {
    const cxc = data
    const {isLoading} = useSearch()
    
    const stats = useMemo(() => {
        let totalBalance = 0
        let totalPaid = 0
        let overdueCount = 0
        let totalInvoices = 0

        cxc.forEach((item) => {
        item.facturas.forEach((factura) => {
            totalInvoices++
            totalBalance += factura.pendiente || 0
            factura.cuotas.forEach((cuota) => {
            totalPaid += cuota.credit || 0
            const vencimiento = new Date(cuota.vencimiento)
            const hoy = new Date()
            const diasDiferencia = Math.floor((vencimiento - hoy) / (1000 * 60 * 60 * 24))
            if (diasDiferencia < 0) overdueCount++
            })
        })
        })

        return {
        totalBalance: totalBalance.toFixed(2),
        totalPaid: totalPaid.toFixed(2),
        overdueCount,
        totalInvoices,
        }
    }, [cxc])

    const getDaysOverdue = (vencimiento) => {
  const MS_PER_DAY = 24 * 60 * 60 * 1000;

  // función para convertir string DD/MM/YYYY o YYYY-MM-DD a milisegundos UTC a medianoche
  const parseToUtcMidnight = (s) => {
      if (!s) return NaN;

      // si viene DD/MM/YYYY
      const ddmmyyyy = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
      if (ddmmyyyy) {
        const day = parseInt(ddmmyyyy[1], 10);
        const month = parseInt(ddmmyyyy[2], 10) - 1; // meses 0-11
        const year = parseInt(ddmmyyyy[3], 10);
        return Date.UTC(year, month, day); // UTC midnight
      }

      // si viene YYYY-MM-DD (ISO) o Date.parse lo entiende, lo convertimos seguro:
      const iso = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
      if (iso) {
        const year = parseInt(iso[1], 10);
        const month = parseInt(iso[2], 10) - 1;
        const day = parseInt(iso[3], 10);
        return Date.UTC(year, month, day);
      }

      // fallback: intentar con constructor Date y llevar a UTC midnight del resultado
      const d = new Date(s);
      if (isNaN(d)) return NaN;
      return Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
    };

    const vencUtc = parseToUtcMidnight(vencimiento);
    if (isNaN(vencUtc)) throw new Error('Fecha de vencimiento inválida. Usa "DD/MM/YYYY" o "YYYY-MM-DD".');

    const now = new Date();
    const todayUtcMidnight = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());

    const diffDays = Math.floor((vencUtc - todayUtcMidnight) / MS_PER_DAY);
    return diffDays;
  };

    
  const getStatusColor = (daysOverdue, residual) => {
    if (residual === 0) return "text-gray-600 font-bold"
    if (daysOverdue < 0) return "text-red-600 font-bold"
    if (daysOverdue === 0) return "text-gray-600 font-bold"
    return "text-gray-600 font-bold"
  }

  const getStatusText = (daysOverdue, residual) => {
    if (residual === 0) return "Pagada"
    if (daysOverdue < 0) return "Vencido"
    if (daysOverdue === 0) return "Vence Hoy"
    return "Al Día"
  }

  const getStatusBgColor = (daysOverdue, residual) => {
    if (residual === 0) return "bg-gray-100 border-gray-300"
    if (daysOverdue < 0) return "bg-red-100 border-red-300"
    if (daysOverdue === 0) return "bg-amber-100 border-amber-300"
    return "bg-gray-100 border-gray-300"
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <main className="max-w-7xl mx-auto px-6 py-8">
          <div className="h-96 flex flex-col items-center justify-center">
            <div className="relative mb-8">
              <div className="w-16 h-16 border-4 border-gray-200 rounded-full"></div>
              <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-red-600 border-r-red-600 rounded-full animate-spin"></div>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Cargando estado de cuenta...</h3>
            <p className="text-gray-600">Conectando con el servidor</p>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      <div className="overflow-x-auto">
        <table className="w-full">
          {/* Table Header */}
          <thead className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-48">Factura</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-40">Fecha de Emisión</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-24">Cuotas</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-28">Fecha máxima</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-28">Valor cuota</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-24">Abono</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-24">Retención</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-24">Saldo</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-28">Valor sin custodia</th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wide w-20">Días</th>
            </tr>
          </thead>

          {/* Table Body */}
          <tbody className="divide-y divide-gray-200">
            {cxc.length > 0 ? (
              cxc.flatMap((clienteData) => {
                const clientRows = []

                // Calcular totales por cliente
                const totalCuotasCliente = clienteData.facturas.reduce((sum, factura) => sum + factura.cuotas.reduce((subSum, cuota) => subSum + cuota.debit, 0), 0).toFixed(2)
                const totalAbonoCliente = clienteData.facturas.reduce((sum, factura) => sum + factura.cuotas.reduce((subSum, cuota) => subSum + (cuota.debit - cuota.residual), 0), 0).toFixed(2)
                const totalSaldoCliente = clienteData.facturas.reduce((sum, factura) => sum + factura.cuotas.reduce((subSum, cuota) => subSum + cuota.residual, 0), 0).toFixed(2)
                const totalChequesValorCliente = clienteData.facturas.reduce((sum, factura) => {
                  const totalChequesFactura = factura.cheques && factura.cheques.length > 0 
                    ? factura.cheques.reduce((subSum, cheque) => {
                        const facturaEnCheque = cheque.facturas.find(f => f.move_name === factura.numero);
                        return subSum + (facturaEnCheque ? facturaEnCheque.amount_reconcile : 0);
                      }, 0)
                    : 0
                  return sum + totalChequesFactura
                }, 0).toFixed(2)
                const valorSinCustodiaCliente = (parseFloat(totalCuotasCliente) - parseFloat(totalAbonoCliente) - parseFloat(totalChequesValorCliente)).toFixed(2)
                const totalRetencionCliente = clienteData.facturas.reduce((sum, factura) => sum + (factura.retencion_total || 0), 0).toFixed(2)

                clientRows.push(
                  <tr key={`client-${clienteData.cliente}`} className="bg-gray-200 font-bold">
                    <td colSpan="4" className="px-6 py-4 text-sm text-gray-900 uppercase">{clienteData.cliente}</td>
                    <td className="px-6 py-4 text-sm font-bold text-gray-900">$ {totalCuotasCliente}</td>
                    <td className="px-6 py-4 text-sm font-bold text-gray-900"></td>
                    <td className="px-6 py-4 text-sm font-bold text-gray-900"></td>
                    <td className="px-6 py-4 text-sm font-bold text-gray-900">$ {totalSaldoCliente}</td>
                    <td className="px-6 py-4 text-sm font-bold text-gray-900">$ {valorSinCustodiaCliente}</td>
                    <td className="px-6 py-4"></td>
                  </tr>,
                )

                clienteData.facturas.forEach((factura) => {
                  // Calcular totales para la fila de total
                  const totalAbono = factura.cuotas.reduce((sum, cuota) => sum + (cuota.debit - cuota.residual), 0).toFixed(2)
                  const totalSaldo = factura.cuotas.reduce((sum, cuota) => sum + cuota.residual, 0).toFixed(2)
                  const totalFactura = factura.total.toFixed(2)
                  const totalCuotas = factura.cuotas.reduce((sum, cuota) => sum + cuota.debit, 0).toFixed(2)
                  const totalChequesValor = factura.cheques && factura.cheques.length > 0 
                    ? factura.cheques.reduce((sum, cheque) => {
                        const facturaEnCheque = cheque.facturas.find(f => f.move_name === factura.numero);
                        return sum + (facturaEnCheque ? facturaEnCheque.amount_reconcile : 0);
                      }, 0).toFixed(2)
                    : "0.00"
                  const valorSinCustodia = (parseFloat(totalCuotas) - parseFloat(totalAbono) - parseFloat(totalChequesValor)).toFixed(2)

                  clientRows.push(
                    <tr key={`factura-${factura.id}`} className="bg-gray-100">
                      <td className="px-6 py-3 text-sm font-bold text-gray-900 truncate">{factura.numero}</td>
                      <td className="px-6 py-3 text-xs font-bold text-gray-700">{factura.fecha}</td>
                      <td className="px-6 py-3 text-xs text-gray-700">-</td>
                      <td className="px-6 py-3 text-sm text-gray-700">-</td>
                      <td className="px-6 py-3 text-sm font-semibold text-gray-900">-</td>
                      <td className="px-6 py-3 text-sm font-bold text-gray-900">-</td>
                      <td className="px-6 py-3 text-sm">-</td>
                      <td className="px-6 py-3 text-sm font-bold text-gray-900">-</td>
                      <td className="px-6 py-3 text-sm">-</td>
                      <td className="px-6 py-3 text-sm">-</td>
                    </tr>,
                  )
                  factura.cuotas.forEach((cuota, index) => {
                    const daysOverdue = getDaysOverdue(cuota.vencimiento)
                    const statusText = getStatusText(daysOverdue, cuota.residual)
                    const statusBgColor = getStatusBgColor(daysOverdue, cuota.residual)
                    const isOverdue = daysOverdue < 0 && cuota.residual > 0
                    clientRows.push(
                      <tr key={`cuota-${factura.id}-${index}`} className="group">
                        <td className={`px-6 py-3 text-sm font-medium text-gray-700 ${isOverdue ? 'text-red-600 font-bold' : ''}`}>-</td>
                        <td className={`px-6 py-3 text-sm text-gray-600 ${isOverdue ? 'text-red-600 font-bold' : ''}`}>-</td>
                        <td className={`px-5 py-3 text-sm text-gray-700 ${isOverdue ? 'text-red-600 font-bold' : ''}`}>Cuota {index + 1}</td>
                        <td className={`px-6 py-3 text-sm text-gray-700 ${isOverdue ? 'text-red-600 font-bold' : ''}`}>{cuota.vencimiento}</td>
                        <td className={`px-6 py-3 text-sm font-semibold text-gray-900 ${isOverdue ? 'text-red-600 font-bold' : ''}`}>
                          $ {cuota.debit?.toFixed(2) || "0.00"}
                        </td>
                        <td className={`px-6 py-3 text-sm font-semibold text-gray-900 ${isOverdue ? 'text-red-600 font-bold' : ''}`}>
                          $ {(cuota.debit - cuota.residual).toFixed(2)}
                        </td>
                        <td className={`px-6 py-3 text-sm ${isOverdue ? 'text-red-600 font-bold' : ''}`}>-</td>
                        <td className={`px-6 py-3 text-sm font-semibold text-gray-900 ${isOverdue ? 'text-red-600 font-bold' : ''}`}>
                          $ {cuota.residual?.toFixed(2) || "0.00"}
                        </td>
                        <td className={`px-6 py-3 text-sm ${isOverdue ? 'text-red-600 font-bold' : ''}`}>-</td>
                        <td className={`px-6 py-3 text-sm ${getStatusColor(daysOverdue, cuota.residual)} whitespace-nowrap`}>
                          {cuota.residual === 0 ? "0 días" : daysOverdue < 0 ? `${Math.abs(daysOverdue)} días` : "0 días"}
                        </td>
                      </tr>,
                    )
                  })
                  // Nueva fila para totales después de las cuotas y cheques
                  clientRows.push(
                    <tr key={`total-${factura.id}`} className="bg-blue-50 font-bold">
                      <td colSpan="4" className="px-6 py-3 text-sm text-gray-900">Total</td>
                      <td className="px-6 py-3 text-sm font-bold text-gray-900">$ {totalCuotas}</td>
                      <td className="px-6 py-3 text-sm font-bold text-gray-900">$ {totalAbono}</td>
                      <td className="px-6 py-3 text-sm font-bold text-gray-900">$ {factura.retencion_total?.toFixed(2) || "0.00"}</td>
                      <td className="px-6 py-3 text-sm font-bold text-gray-900">$ {totalSaldo}</td>
                      <td className="px-6 py-3 text-sm font-bold text-gray-900">$ {valorSinCustodia}</td>
                      <td className="px-6 py-3 text-sm"></td>
                    </tr>,
                  )
                })

                return clientRows
              })
            ) : (
              <tr>
                <td colSpan="10" className="px-6 py-12 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <Search className="w-8 h-8 text-gray-300" />
                    <p className="text-gray-600 font-semibold">No se encontraron facturas</p>
                    <p className="text-gray-400 text-sm">Intenta otro término de búsqueda</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Table
