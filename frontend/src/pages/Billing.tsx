import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Search, Plus, Trash2, Printer, Check, FileClock, CalendarCheck,
  FileSpreadsheet, FileText,
} from 'lucide-react'
import { api, inr, downloadFile } from '../lib/api'
import type { Customer, DayClose, Invoice, Medicine, Paginated, Prescription } from '../lib/types'
import { PageHeader, ScheduleBadge, Empty, Modal } from '../components/ui'

interface CartLine {
  medicine: Medicine
  quantity: number
  discount: number
  unitMode: 'pack' | 'loose'
}
type RxMap = Record<number, Omit<Prescription, 'medicine'>>

export default function Billing() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [cart, setCart] = useState<CartLine[]>([])
  const [customerId, setCustomerId] = useState<number | ''>('')
  const [paymentMode, setPaymentMode] = useState('cash')
  const [billDiscount, setBillDiscount] = useState(0)
  const [rx, setRx] = useState<RxMap>({})
  const [saved, setSaved] = useState<Invoice | null>(null)
  const [showDayClose, setShowDayClose] = useState(false)
  const [showBills, setShowBills] = useState(false)
  const [custQuery, setCustQuery] = useState('')
  const [custErr, setCustErr] = useState('')
  const searchRef = useRef<HTMLInputElement>(null)

  const { data: meds } = useQuery({
    queryKey: ['medicines', 'search', search],
    queryFn: async () =>
      (await api.get<Paginated<Medicine>>('/medicines/', {
        params: { search, is_active: true },
      })).data.results,
    enabled: search.length > 0,
  })
  const { data: customers, refetch: refetchCustomers } = useQuery({
    queryKey: ['customers', 'all'],
    queryFn: async () => (await api.get<Paginated<Customer>>('/customers/')).data.results,
  })

  // Item 3: fetch a customer at the counter by exact customer ID or phone.
  const lookupCustomer = useMutation({
    mutationFn: async () => (await api.get<Customer>('/customers/lookup/', { params: { q: custQuery.trim() } })).data,
    onSuccess: async (c) => {
      await refetchCustomers()
      setCustomerId(c.id)
      setCustQuery('')
    },
    onError: () => setCustErr(`No customer found for "${custQuery.trim()}".`),
  })

  const scheduledLines = cart.filter((c) => c.medicine.schedule !== 'OTC')

  const save = useMutation({
    mutationFn: async () => {
      const payload = {
        customer: customerId || null,
        payment_mode: paymentMode,
        discount: billDiscount,
        items: cart.map((c) => ({
          medicine: c.medicine.id, quantity: c.quantity, discount: c.discount,
          unit_mode: c.unitMode,
        })),
        prescriptions: scheduledLines.map((c) => ({
          medicine: c.medicine.id,
          patient_name: rx[c.medicine.id]?.patient_name ?? '',
          prescriber_name: rx[c.medicine.id]?.prescriber_name ?? '',
          prescriber_reg_no: rx[c.medicine.id]?.prescriber_reg_no ?? '',
          quantity: c.quantity,
        })),
      }
      return (await api.post<Invoice>('/invoices/', payload)).data
    },
    onSuccess: (inv) => {
      setSaved(inv)
      setCart([]); setBillDiscount(0); setCustomerId(''); setSearch(''); setRx({})
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  function addToCart(m: Medicine) {
    setSearch('')
    searchRef.current?.focus()
    setCart((prev) => {
      const existing = prev.find((c) => c.medicine.id === m.id)
      if (existing)
        return prev.map((c) => c.medicine.id === m.id ? { ...c, quantity: c.quantity + 1 } : c)
      return [...prev, { medicine: m, quantity: 1, discount: 0, unitMode: 'pack' }]
    })
  }
  const setQty = (id: number, q: number) =>
    setCart((prev) => prev.map((c) => c.medicine.id === id ? { ...c, quantity: Math.max(1, q) } : c))
  const setMode = (id: number, mode: 'pack' | 'loose') =>
    setCart((prev) => prev.map((c) => c.medicine.id === id ? { ...c, unitMode: mode } : c))
  const remove = (id: number) => setCart((prev) => prev.filter((c) => c.medicine.id !== id))
  // F3 focuses the medicine search (counter shortcut).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'F3') { e.preventDefault(); searchRef.current?.focus() }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])
  const setRxField = (id: number, field: keyof Omit<Prescription, 'medicine'>, val: string) =>
    setRx((prev) => ({ ...prev, [id]: { ...(prev[id] ?? { patient_name: '', prescriber_name: '', prescriber_reg_no: '', quantity: 1 }), [field]: val } }))

  const rxComplete = scheduledLines.every(
    (c) => rx[c.medicine.id]?.patient_name && rx[c.medicine.id]?.prescriber_name
  )

  const unitRate = (c: CartLine) =>
    c.unitMode === 'loose'
      ? Number(c.medicine.unit_price ?? 0)
      : Number(c.medicine.sell_mrp ?? 0)

  const totals = useMemo(() => {
    let gross = 0, taxable = 0, gst = 0
    for (const c of cart) {
      const mrp = unitRate(c)
      const rate = Number(c.medicine.gst_rate)
      const lineGross = mrp * c.quantity - c.discount
      const lineTaxable = lineGross / (1 + rate / 100)
      gross += lineGross
      taxable += lineTaxable
      gst += lineGross - lineTaxable
    }
    const total = gross - billDiscount
    return { taxable, gst, total: total > 0 ? total : 0 }
  }, [cart, billDiscount])

  if (saved) {
    return (
      <div className="max-w-xl mx-auto">
        <div className="card p-8 text-center">
          <div className="w-14 h-14 rounded-full bg-[#eaf6ee] text-ok grid place-items-center mx-auto mb-4">
            <Check size={28} />
          </div>
          <h2 className="text-[20px] font-bold">Bill saved</h2>
          <p className="text-muted mt-1">{saved.number} · {inr(saved.total)}</p>
          <div className="grid grid-cols-3 gap-3 my-6 text-left">
            <Info label="Taxable" value={inr(saved.subtotal)} />
            <Info label="CGST + SGST" value={inr(Number(saved.cgst) + Number(saved.sgst))} />
            <Info label="Total" value={inr(saved.total)} />
          </div>
          <div className="flex gap-3 justify-center">
            <a className="btn-primary" href={`/api/invoices/${saved.id}/pdf/`} target="_blank" rel="noreferrer">
              <Printer size={16} /> Print / PDF
            </a>
            <button className="btn-ghost" onClick={() => setSaved(null)}>New bill</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Billing"
        subtitle="FEFO issues the earliest-expiring batch automatically"
        actions={
          <>
            <button className="btn-ghost" onClick={() => setShowBills(true)}>
              <FileSpreadsheet size={16} /> Download bills
            </button>
            <button className="btn-ghost" onClick={() => setShowDayClose(true)}>
              <CalendarCheck size={16} /> Day close · cash recon
            </button>
          </>
        }
      />
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Cart */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-3 relative">
            <div className="relative">
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-faint" />
              <input
                ref={searchRef}
                autoFocus
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Scan barcode or search medicine name / composition…  (F3)"
                className="input pl-10 text-[15px] py-3"
              />
            </div>
            {meds && search && (
              <div className="absolute left-3 right-3 top-full mt-1 z-20 card shadow-lg max-h-72 overflow-y-auto">
                {!meds.length && <Empty>No medicine matches “{search}”.</Empty>}
                {meds.map((m) => (
                  <button key={m.id} onClick={() => addToCart(m)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-canvas text-left border-b border-line last:border-0">
                    <div className="flex-none w-7 h-7 rounded-md bg-accent text-white grid place-items-center text-lg leading-none">
                      <Plus size={16} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-[13.5px] truncate">{m.name}</div>
                      <div className="text-[11.5px] text-muted truncate">{m.generic_name} · {m.manufacturer}</div>
                    </div>
                    <ScheduleBadge schedule={m.schedule} />
                    <div className="text-right text-[12px]">
                      <div className="font-mono">{inr(m.sell_mrp ?? 0)}</div>
                      <div className={m.total_stock <= m.reorder_level ? 'text-warn font-semibold' : 'text-muted'}>
                        {m.total_stock} in stock
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="card overflow-hidden">
            <table className="w-full text-[13px]">
              <thead className="bg-canvas text-muted text-[11.5px] uppercase tracking-wide">
                <tr>
                  <th className="text-left font-semibold px-4 py-2.5">Item</th>
                  <th className="text-right font-semibold px-2">MRP</th>
                  <th className="text-center font-semibold px-2">Qty</th>
                  <th className="text-right font-semibold px-2">Disc</th>
                  <th className="text-right font-semibold px-4">Amount</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {!cart.length && (
                  <tr><td colSpan={6}><Empty>Cart is empty — search to add medicines.</Empty></td></tr>
                )}
                {cart.map((c) => {
                  const rate = unitRate(c)
                  const amount = rate * c.quantity - c.discount
                  const loose = c.unitMode === 'loose'
                  return (
                    <tr key={c.medicine.id}>
                      <td className="px-4 py-2.5">
                        <div className="font-semibold flex items-center gap-2">
                          {c.medicine.name}
                          {c.medicine.schedule !== 'OTC' && <ScheduleBadge schedule={c.medicine.schedule} />}
                        </div>
                        <div className="text-[11.5px] text-muted flex items-center gap-2">
                          <span>{c.medicine.pack_unit} · GST {c.medicine.gst_rate}%</span>
                          {c.medicine.sells_loose && (
                            <span className="inline-flex rounded-md overflow-hidden border border-line">
                              {(['pack', 'loose'] as const).map((m) => (
                                <button key={m} onClick={() => setMode(c.medicine.id, m)}
                                  className={`px-1.5 py-0.5 text-[10px] font-semibold capitalize ${
                                    c.unitMode === m ? 'bg-accent text-white' : 'text-muted'}`}>
                                  {m === 'loose' ? `loose (×${c.medicine.units_per_pack})` : 'pack'}
                                </button>
                              ))}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="text-right px-2 font-mono">
                        {rate.toFixed(2)}{loose && <span className="text-[10px] text-muted">/unit</span>}
                      </td>
                      <td className="text-center px-2">
                        <input type="number" min={1} value={c.quantity}
                          onChange={(e) => setQty(c.medicine.id, Number(e.target.value))}
                          className="w-14 text-center border border-line rounded-md py-1" />
                        {loose && <div className="text-[9px] text-muted">tablets</div>}
                      </td>
                      <td className="px-2">
                        <input type="number" min={0} value={c.discount}
                          onChange={(e) => setCart((p) => p.map((x) =>
                            x.medicine.id === c.medicine.id ? { ...x, discount: Number(e.target.value) } : x))}
                          className="w-16 text-right border border-line rounded-md py-1 px-1" />
                      </td>
                      <td className="text-right px-4 font-mono font-semibold">{amount.toFixed(2)}</td>
                      <td className="px-2">
                        <button onClick={() => remove(c.medicine.id)} className="text-faint hover:text-danger">
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Prescription capture for scheduled drugs (FR-23) */}
          {scheduledLines.length > 0 && (
            <div className="card p-4 border-warn/40 bg-[#fdf3e7]/30">
              <div className="flex items-center gap-2 mb-3">
                <FileClock size={16} className="text-warn" />
                <h3 className="font-bold text-[13.5px]">Prescription required (scheduled drugs)</h3>
              </div>
              <div className="space-y-3">
                {scheduledLines.map((c) => (
                  <div key={c.medicine.id} className="grid grid-cols-1 md:grid-cols-4 gap-2 items-end">
                    <div className="md:col-span-1 text-[12.5px] font-semibold flex items-center gap-1.5">
                      <ScheduleBadge schedule={c.medicine.schedule} /> {c.medicine.name}
                    </div>
                    <input placeholder="Patient name *" className="input !py-2"
                      value={rx[c.medicine.id]?.patient_name ?? ''}
                      onChange={(e) => setRxField(c.medicine.id, 'patient_name', e.target.value)} />
                    <input placeholder="Prescriber name *" className="input !py-2"
                      value={rx[c.medicine.id]?.prescriber_name ?? ''}
                      onChange={(e) => setRxField(c.medicine.id, 'prescriber_name', e.target.value)} />
                    <input placeholder="Reg. no" className="input !py-2"
                      value={rx[c.medicine.id]?.prescriber_reg_no ?? ''}
                      onChange={(e) => setRxField(c.medicine.id, 'prescriber_reg_no', e.target.value)} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Checkout */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <div>
              <label className="label">Customer</label>
              <div className="flex gap-1.5 mb-1.5">
                <input
                  value={custQuery}
                  onChange={(e) => { setCustQuery(e.target.value); setCustErr('') }}
                  onKeyDown={(e) => e.key === 'Enter' && lookupCustomer.mutate()}
                  placeholder="Fetch by customer ID or phone…"
                  className="input !py-2 text-[13px]" />
                <button className="btn-ghost !py-2" disabled={!custQuery || lookupCustomer.isPending}
                  onClick={() => lookupCustomer.mutate()}>Fetch</button>
              </div>
              {custErr && <p className="text-[11.5px] text-danger mb-1">{custErr}</p>}
              <select className="input" value={customerId}
                onChange={(e) => setCustomerId(e.target.value ? Number(e.target.value) : '')}>
                <option value="">Walk-in customer</option>
                {customers?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.is_regular ? '★' : ''} {c.phone && `· ${c.phone}`}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Payment mode</label>
              <div className="grid grid-cols-4 gap-1.5">
                {['cash', 'upi', 'card', 'credit'].map((m) => (
                  <button key={m} onClick={() => setPaymentMode(m)}
                    className={`py-2 rounded-lg text-[12px] font-semibold capitalize border transition ${
                      paymentMode === m ? 'bg-accent text-white border-accent' : 'border-line text-muted hover:border-accent/40'
                    }`}>
                    {m}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="card p-4 space-y-2.5">
            <Row label="Taxable value" value={inr(totals.taxable)} />
            <Row label="GST (CGST + SGST)" value={inr(totals.gst)} />
            <div className="flex items-center justify-between">
              <span className="text-[13px] text-muted">Bill discount</span>
              <input type="number" min={0} value={billDiscount}
                onChange={(e) => setBillDiscount(Number(e.target.value))}
                className="w-24 text-right border border-line rounded-md py-1 px-2" />
            </div>
            <div className="flex items-center justify-between pt-2.5 border-t border-line">
              <span className="font-bold text-[15px]">Total</span>
              <span className="font-bold text-[20px]">{inr(totals.total)}</span>
            </div>
            {scheduledLines.length > 0 && !rxComplete && (
              <p className="text-[12px] text-warn">Enter patient &amp; prescriber for each scheduled drug to bill.</p>
            )}
            {save.isError && (
              <p className="text-[12px] text-danger">
                {(save.error as any)?.response?.data?.detail ??
                 JSON.stringify((save.error as any)?.response?.data) ?? 'Could not save bill.'}
              </p>
            )}
            <button disabled={!cart.length || save.isPending || (scheduledLines.length > 0 && !rxComplete)}
              onClick={() => save.mutate()} className="btn-primary w-full justify-center py-3 text-[14px]">
              {save.isPending ? 'Saving…' : 'Save & bill'}
            </button>
          </div>
        </div>
      </div>

      {showDayClose && <DayCloseModal onClose={() => setShowDayClose(false)} />}
      {showBills && <BillsDownloadModal onClose={() => setShowBills(false)} />}
    </div>
  )
}

function BillsDownloadModal({ onClose }: { onClose: () => void }) {
  const today = new Date().toISOString().slice(0, 10)
  const monthStart = today.slice(0, 8) + '01'
  const [start, setStart] = useState(monthStart)
  const [end, setEnd] = useState(today)
  const [busy, setBusy] = useState(false)

  const download = async (fmt: 'xlsx' | 'pdf') => {
    setBusy(true)
    try {
      const qs = new URLSearchParams({ start, end, export: fmt }).toString()
      await downloadFile(`/reports/bills/?${qs}`, `Bills_${start}_to_${end}.${fmt}`)
      onClose()
    } finally { setBusy(false) }
  }

  return (
    <Modal title="Download bills" onClose={onClose}>
      <p className="text-[12.5px] text-muted mb-3">
        Excel gives two sheets — a per-bill summary and full line-item detail.
      </p>
      <div className="grid grid-cols-2 gap-3 mb-2">
        <div>
          <label className="label">From</label>
          <input type="date" className="input !py-2" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div>
          <label className="label">To</label>
          <input type="date" className="input !py-2" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
      </div>
      <div className="flex gap-2 mb-4">
        <button className="btn-ghost !py-1.5" onClick={() => { setStart(today); setEnd(today) }}>Today</button>
        <button className="btn-ghost !py-1.5" onClick={() => { setStart(monthStart); setEnd(today) }}>This month</button>
      </div>
      <div className="flex justify-end gap-2">
        <button className="btn-ghost" onClick={() => download('pdf')} disabled={busy}>
          <FileText size={15} /> PDF
        </button>
        <button className="btn-primary" onClick={() => download('xlsx')} disabled={busy}>
          <FileSpreadsheet size={15} /> {busy ? 'Preparing…' : 'Download Excel'}
        </button>
      </div>
    </Modal>
  )
}

function DayCloseModal({ onClose }: { onClose: () => void }) {
  const { data } = useQuery({
    queryKey: ['day-close'],
    queryFn: async () => (await api.get<DayClose>('/day-close/')).data,
  })
  return (
    <Modal title="Day close · cash reconciliation" onClose={onClose}>
      {!data ? <Empty>Loading…</Empty> : (
        <div className="space-y-4">
          <div className="text-[12px] text-muted">For {data.date}</div>
          <div className="grid grid-cols-2 gap-3">
            <Info label="Bills" value={String(data.invoice_count)} />
            <Info label="Gross sales" value={inr(data.gross_total)} />
            <Info label="Cash in drawer" value={inr(data.cash_total)} />
            <Info label="GST collected" value={inr(data.tax_collected)} />
          </div>
          <div className="card overflow-hidden">
            <table className="w-full text-[13px]">
              <thead className="bg-canvas text-muted text-[11px] uppercase">
                <tr><th className="text-left px-3 py-2">Payment mode</th>
                  <th className="text-right px-2">Bills</th>
                  <th className="text-right px-3">Amount</th></tr>
              </thead>
              <tbody className="divide-y divide-line">
                {Object.entries(data.by_mode).map(([mode, v]) => (
                  <tr key={mode}>
                    <td className="px-3 py-2 capitalize">{mode}</td>
                    <td className="px-2 text-right">{v.count}</td>
                    <td className="px-3 text-right font-mono">{inr(v.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.returned_count > 0 && (
            <p className="text-[12px] text-danger">
              {data.returned_count} returned bill(s) · {inr(data.returned_total)}
            </p>
          )}
        </div>
      )}
    </Modal>
  )
}

const Row = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center justify-between text-[13px]">
    <span className="text-muted">{label}</span>
    <span className="font-mono">{value}</span>
  </div>
)
const Info = ({ label, value }: { label: string; value: string }) => (
  <div className="card p-3">
    <div className="text-[11px] text-muted">{label}</div>
    <div className="font-bold mt-0.5">{value}</div>
  </div>
)
