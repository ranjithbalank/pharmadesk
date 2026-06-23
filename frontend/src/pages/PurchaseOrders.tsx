import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Sparkles, Plus, Send, PackageCheck, FileText } from 'lucide-react'
import { api, inr } from '../lib/api'
import { PageHeader, Empty, Modal } from '../components/ui'

interface POLine { id?: number; medicine: number; medicine_name?: string; quantity: number; unit_cost: number; received_qty?: number; outstanding_qty?: number }
interface PO {
  id: number; number: string; supplier: number; supplier_name: string
  status: string; status_display: string; total_value: string; lines: POLine[]; created_at: string
  bill_to?: string; ship_to?: string
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

      {view && <PoDetail po={view} onClose={() => setView(null)} />}
    </div>
  )
}

interface ReceiptRow { batch_number: string; expiry_date: string; mfg_date: string; quantity: string; purchase_cost: string; mrp: string }

function PoDetail({ po, onClose }: { po: PO; onClose: () => void }) {
  const qc = useQueryClient()
  const [receiving, setReceiving] = useState(false)
  const [rows, setRows] = useState<Record<number, ReceiptRow>>({})

  // Live copy so received quantities refresh after a goods receipt.
  const { data } = useQuery({
    queryKey: ['purchase-order', po.id],
    queryFn: async () => (await api.get<PO>(`/purchase-orders/${po.id}/`)).data,
    initialData: po,
  })
  const current = data ?? po

  const place = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${po.id}/place/`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['purchase-orders'] }); qc.invalidateQueries({ queryKey: ['purchase-order', po.id] }) },
  })
  const receive = useMutation({
    mutationFn: () => api.post(`/purchase-orders/${po.id}/receive/`, {
      lines: current.lines
        .filter((l) => Number(rows[l.id!]?.quantity) > 0)
        .map((l) => ({
          line: l.id,
          quantity: Number(rows[l.id!].quantity),
          batch_number: rows[l.id!].batch_number,
          expiry_date: rows[l.id!].expiry_date,
          mfg_date: rows[l.id!].mfg_date || null,
          purchase_cost: Number(rows[l.id!].purchase_cost || l.unit_cost),
          mrp: Number(rows[l.id!].mrp || 0),
        })),
    }),
    onSuccess: () => {
      setReceiving(false); setRows({})
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
      qc.invalidateQueries({ queryKey: ['purchase-order', po.id] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['medicines'] })
    },
  })
  const setRow = (id: number, field: keyof ReceiptRow, val: string) =>
    setRows((p) => ({ ...p, [id]: { ...(p[id] ?? { batch_number: '', expiry_date: '', mfg_date: '', quantity: '', purchase_cost: '', mrp: '' }), [field]: val } }))

  const canReceive = current.status !== 'received' && current.status !== 'draft'
  const receiptValid = current.lines.some((l) => {
    const r = rows[l.id!]
    return r && Number(r.quantity) > 0 && r.batch_number && r.expiry_date
  })

  return (
    <Modal title={`${current.number} · ${current.supplier_name}`} onClose={onClose} wide>
      <div className="flex items-center justify-between mb-3">
        <span className={`text-[11px] font-semibold rounded-md px-2 py-0.5 ${STATUS_TONE[current.status]}`}>
          {current.status_display}
        </span>
        <div className="flex gap-2">
          <a className="btn-ghost !py-1.5" href={`/api/purchase-orders/${po.id}/pdf/`} target="_blank" rel="noreferrer">
            <FileText size={14} /> PDF
          </a>
          {current.status === 'draft' && (
            <button className="btn-ghost !py-1.5" disabled={place.isPending} onClick={() => place.mutate()}>
              <Send size={14} /> Place order
            </button>
          )}
          {canReceive && !receiving && (
            <button className="btn-primary !py-1.5" onClick={() => setReceiving(true)}>
              <PackageCheck size={14} /> Receive goods
            </button>
          )}
        </div>
      </div>

      {(current.bill_to || current.ship_to) && (
        <div className="grid grid-cols-2 gap-3 mb-3 text-[12px]">
          <div className="card p-2.5"><div className="text-muted font-semibold mb-0.5">Bill to</div><div className="whitespace-pre-line">{current.bill_to || '—'}</div></div>
          <div className="card p-2.5"><div className="text-muted font-semibold mb-0.5">Ship to</div><div className="whitespace-pre-line">{current.ship_to || '—'}</div></div>
        </div>
      )}

      {!receiving ? (
        <table className="w-full text-[13px]">
          <thead className="bg-canvas text-muted text-[11px] uppercase">
            <tr>
              <th className="text-left px-3 py-2">Medicine</th>
              <th className="text-right px-2">Ordered</th>
              <th className="text-right px-2">Received</th>
              <th className="text-right px-2">Pending</th>
              <th className="text-right px-3">Unit cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {current.lines.map((l) => (
              <tr key={l.id}>
                <td className="px-3 py-2">{l.medicine_name}</td>
                <td className="px-2 text-right">{l.quantity}</td>
                <td className="px-2 text-right">{l.received_qty ?? 0}</td>
                <td className="px-2 text-right font-semibold">{l.outstanding_qty ?? (l.quantity - (l.received_qty ?? 0))}</td>
                <td className="px-3 text-right font-mono">{inr(l.unit_cost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="space-y-3">
          <p className="text-[12px] text-muted">Enter received batches. Stock updates automatically on receipt.</p>
          {current.lines.filter((l) => (l.outstanding_qty ?? (l.quantity - (l.received_qty ?? 0))) > 0).map((l) => (
            <div key={l.id} className="card p-3">
              <div className="font-semibold text-[13px] mb-2">{l.medicine_name}
                <span className="text-muted font-normal"> · {l.outstanding_qty ?? (l.quantity - (l.received_qty ?? 0))} pending</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                <input placeholder="Batch no *" className="input !py-2" value={rows[l.id!]?.batch_number ?? ''} onChange={(e) => setRow(l.id!, 'batch_number', e.target.value)} />
                <input type="date" title="Expiry *" className="input !py-2" value={rows[l.id!]?.expiry_date ?? ''} onChange={(e) => setRow(l.id!, 'expiry_date', e.target.value)} />
                <input type="date" title="Mfg date" className="input !py-2" value={rows[l.id!]?.mfg_date ?? ''} onChange={(e) => setRow(l.id!, 'mfg_date', e.target.value)} />
                <input type="number" placeholder="Qty *" className="input !py-2" value={rows[l.id!]?.quantity ?? ''} onChange={(e) => setRow(l.id!, 'quantity', e.target.value)} />
                <input type="number" placeholder="Cost" className="input !py-2" value={rows[l.id!]?.purchase_cost ?? ''} onChange={(e) => setRow(l.id!, 'purchase_cost', e.target.value)} />
                <input type="number" placeholder="MRP" className="input !py-2" value={rows[l.id!]?.mrp ?? ''} onChange={(e) => setRow(l.id!, 'mrp', e.target.value)} />
              </div>
            </div>
          ))}
          <div className="flex justify-end gap-2">
            <button className="btn-ghost" onClick={() => setReceiving(false)}>Cancel</button>
            <button className="btn-primary" disabled={!receiptValid || receive.isPending} onClick={() => receive.mutate()}>
              {receive.isPending ? 'Receiving…' : 'Confirm receipt'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}
