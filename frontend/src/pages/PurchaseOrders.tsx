import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Sparkles, Plus } from 'lucide-react'
import { api, inr } from '../lib/api'
import { PageHeader, Empty, Modal } from '../components/ui'

interface POLine { id?: number; medicine: number; medicine_name?: string; quantity: number; unit_cost: number; received_qty?: number; outstanding_qty?: number }
interface PO {
  id: number; number: string; supplier: number; supplier_name: string
  status: string; status_display: string; total_value: string; lines: POLine[]; created_at: string
}
interface Suggestion { supplier: number | null; lines: POLine[] }

const STATUS_TONE: Record<string, string> = {
  draft: 'bg-canvas text-muted', placed: 'bg-accent-soft text-accent',
  partial: 'bg-[#fdf3e7] text-warn', received: 'bg-[#eaf6ee] text-ok',
}

export default function PurchaseOrders() {
  const qc = useQueryClient()
  const [suggestions, setSuggestions] = useState<Suggestion[] | null>(null)
  const [view, setView] = useState<PO | null>(null)

  const { data } = useQuery({
    queryKey: ['purchase-orders'],
    queryFn: async () => (await api.get<{ results: PO[] }>('/purchase-orders/')).data.results,
  })
  const suggest = useMutation({
    mutationFn: async () => (await api.post<Suggestion[]>('/purchase-orders/suggest/', {})).data,
    onSuccess: (d) => setSuggestions(d),
  })
  const createPO = useMutation({
    mutationFn: (s: Suggestion) => api.post('/purchase-orders/', {
      supplier: s.supplier,
      lines: s.lines.map((l) => ({ medicine: l.medicine, quantity: l.quantity, unit_cost: l.unit_cost })),
    }),
    onSuccess: () => { setSuggestions(null); qc.invalidateQueries({ queryKey: ['purchase-orders'] }) },
  })

  return (
    <div>
      <PageHeader
        title="Purchase Orders"
        subtitle="Auto-suggest reorders from items at or below reorder level"
        actions={
          <button className="btn-primary" onClick={() => suggest.mutate()} disabled={suggest.isPending}>
            <Sparkles size={16} /> {suggest.isPending ? 'Building…' : 'Suggest reorder'}
          </button>
        }
      />

      <div className="card overflow-hidden">
        <table className="w-full text-[13px]">
          <thead className="bg-canvas text-muted text-[11.5px] uppercase tracking-wide">
            <tr>
              <th className="text-left font-semibold px-4 py-2.5">PO number</th>
              <th className="text-left font-semibold px-2">Supplier</th>
              <th className="text-left font-semibold px-2">Status</th>
              <th className="text-right font-semibold px-2">Items</th>
              <th className="text-right font-semibold px-4">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data?.length === 0 && <tr><td colSpan={5}><Empty>No purchase orders yet — try “Suggest reorder”.</Empty></td></tr>}
            {data?.map((po) => (
              <tr key={po.id} className="hover:bg-canvas/60 cursor-pointer" onClick={() => setView(po)}>
                <td className="px-4 py-2.5 font-mono font-semibold">{po.number}</td>
                <td className="px-2">{po.supplier_name}</td>
                <td className="px-2">
                  <span className={`text-[11px] font-semibold rounded-md px-2 py-0.5 ${STATUS_TONE[po.status]}`}>
                    {po.status_display}
                  </span>
                </td>
                <td className="px-2 text-right">{po.lines.length}</td>
                <td className="px-4 text-right font-mono">{inr(po.total_value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {suggestions && (
        <Modal title="Suggested reorder" onClose={() => setSuggestions(null)} wide>
          {suggestions.length === 0 && <Empty>Nothing to reorder — all items above reorder level.</Empty>}
          <div className="space-y-4">
            {suggestions.map((s, i) => (
              <div key={i} className="card p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="font-semibold text-[14px]">
                    {s.supplier ? `Supplier #${s.supplier}` : 'No preferred supplier'}
                  </div>
                  <button className="btn-primary !py-1.5" disabled={!s.supplier || createPO.isPending}
                    onClick={() => createPO.mutate(s)}>
                    <Plus size={14} /> Create draft PO
                  </button>
                </div>
                <table className="w-full text-[12.5px]">
                  <tbody className="divide-y divide-line">
                    {s.lines.map((l, j) => (
                      <tr key={j}>
                        <td className="py-1.5">{l.medicine_name}</td>
                        <td className="py-1.5 text-right text-muted">qty {l.quantity}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!s.supplier && <p className="text-[11.5px] text-warn mt-2">Set a preferred supplier on these medicines to create a PO.</p>}
              </div>
            ))}
          </div>
        </Modal>
      )}

      {view && (
        <Modal title={`${view.number} · ${view.supplier_name}`} onClose={() => setView(null)} wide>
          <table className="w-full text-[13px]">
            <thead className="bg-canvas text-muted text-[11px] uppercase">
              <tr>
                <th className="text-left px-3 py-2">Medicine</th>
                <th className="text-right px-2">Ordered</th>
                <th className="text-right px-2">Received</th>
                <th className="text-right px-3">Unit cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {view.lines.map((l) => (
                <tr key={l.id}>
                  <td className="px-3 py-2">{l.medicine_name}</td>
                  <td className="px-2 text-right">{l.quantity}</td>
                  <td className="px-2 text-right">{l.received_qty ?? 0}</td>
                  <td className="px-3 text-right font-mono">{inr(l.unit_cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Modal>
      )}
    </div>
  )
}
