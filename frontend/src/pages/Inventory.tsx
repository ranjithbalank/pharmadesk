import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Layers } from 'lucide-react'
import { api, inr } from '../lib/api'
import type { Medicine, Paginated, Supplier } from '../lib/types'
import { PageHeader, StatusBadge, ScheduleBadge, Empty, Modal } from '../components/ui'

const SCHEDULES = ['OTC', 'H', 'H1', 'X']

export default function Inventory() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [showMed, setShowMed] = useState(false)
  const [batchFor, setBatchFor] = useState<Medicine | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['medicines', 'list', search],
    queryFn: async () =>
      (await api.get<Paginated<Medicine>>('/medicines/', { params: { search } })).data,
  })

  return (
    <div>
      <PageHeader
        title="Inventory"
        subtitle="Medicine master with batch &amp; expiry tracking"
        actions={
          <button className="btn-primary" onClick={() => setShowMed(true)}>
            <Plus size={16} /> Add medicine
          </button>
        }
      />

      <div className="card p-3 mb-4">
        <div className="relative">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-faint" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name, composition, manufacturer, barcode…"
            className="input pl-10" />
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-[13px]">
          <thead className="bg-canvas text-muted text-[11.5px] uppercase tracking-wide">
            <tr>
              <th className="text-left font-semibold px-4 py-2.5">Medicine</th>
              <th className="text-left font-semibold px-2">Schedule</th>
              <th className="text-left font-semibold px-2">Rack</th>
              <th className="text-right font-semibold px-2">GST</th>
              <th className="text-right font-semibold px-2">Stock</th>
              <th className="text-left font-semibold px-2">Status</th>
              <th className="px-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {isLoading && <tr><td colSpan={7}><Empty>Loading…</Empty></td></tr>}
            {data?.results.length === 0 && <tr><td colSpan={7}><Empty>No medicines yet.</Empty></td></tr>}
            {data?.results.map((m) => (
              <tr key={m.id} className="hover:bg-canvas/60">
                <td className="px-4 py-2.5">
                  <div className="font-semibold">{m.name}</div>
                  <div className="text-[11.5px] text-muted">{m.generic_name} · {m.manufacturer}</div>
                </td>
                <td className="px-2"><ScheduleBadge schedule={m.schedule} /></td>
                <td className="px-2 text-muted font-mono text-[12px]">{m.rack_location || '—'}</td>
                <td className="px-2 text-right">{m.gst_rate}%</td>
                <td className="px-2 text-right font-semibold">{m.total_stock}</td>
                <td className="px-2"><StatusBadge status={m.stock_status} /></td>
                <td className="px-4 text-right">
                  <button className="btn-ghost !py-1.5 !px-2.5" onClick={() => setBatchFor(m)}>
                    <Layers size={14} /> Batch
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showMed && <MedicineModal onClose={() => { setShowMed(false); qc.invalidateQueries({ queryKey: ['medicines'] }) }} />}
      {batchFor && <BatchModal medicine={batchFor} onClose={() => { setBatchFor(null); qc.invalidateQueries({ queryKey: ['medicines'] }) }} />}
    </div>
  )

  function MedicineModal({ onClose }: { onClose: () => void }) {
    const [form, setForm] = useState({
      name: '', generic_name: '', manufacturer: '', hsn_code: '', gst_rate: '12',
      schedule: 'OTC', pack_unit: '', rack_location: '', barcode: '',
      reorder_level: '10', reorder_qty: '50', preferred_supplier: '',
    })
    const { data: suppliers } = useQuery({
      queryKey: ['suppliers', 'all'],
      queryFn: async () => (await api.get<Paginated<Supplier>>('/suppliers/')).data.results,
    })
    const create = useMutation({
      mutationFn: () => api.post('/medicines/', {
        ...form,
        preferred_supplier: form.preferred_supplier || null,
      }),
      onSuccess: onClose,
    })
    const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

    return (
      <Modal title="Add medicine" onClose={onClose} wide>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Name *" v={form.name} on={(v) => set('name', v)} className="col-span-2" />
          <Field label="Generic / composition" v={form.generic_name} on={(v) => set('generic_name', v)} />
          <Field label="Manufacturer" v={form.manufacturer} on={(v) => set('manufacturer', v)} />
          <Field label="HSN code" v={form.hsn_code} on={(v) => set('hsn_code', v)} />
          <div>
            <label className="label">GST rate %</label>
            <select className="input" value={form.gst_rate} onChange={(e) => set('gst_rate', e.target.value)}>
              {['0', '5', '12', '18', '28'].map((r) => <option key={r} value={r}>{r}%</option>)}
            </select>
          </div>
          <div>
            <label className="label">Schedule</label>
            <select className="input" value={form.schedule} onChange={(e) => set('schedule', e.target.value)}>
              {SCHEDULES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <Field label="Pack / unit" v={form.pack_unit} on={(v) => set('pack_unit', v)} />
          <Field label="Rack location" v={form.rack_location} on={(v) => set('rack_location', v)} />
          <Field label="Barcode" v={form.barcode} on={(v) => set('barcode', v)} />
          <Field label="Reorder level" v={form.reorder_level} on={(v) => set('reorder_level', v)} type="number" />
          <Field label="Reorder qty" v={form.reorder_qty} on={(v) => set('reorder_qty', v)} type="number" />
          <div className="col-span-2">
            <label className="label">Preferred supplier</label>
            <select className="input" value={form.preferred_supplier}
              onChange={(e) => set('preferred_supplier', e.target.value)}>
              <option value="">— none —</option>
              {suppliers?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn-primary" disabled={!form.name || create.isPending}
            onClick={() => create.mutate()}>
            {create.isPending ? 'Saving…' : 'Save medicine'}
          </button>
        </div>
      </Modal>
    )
  }

  function BatchModal({ medicine, onClose }: { medicine: Medicine; onClose: () => void }) {
    const { data } = useQuery({
      queryKey: ['medicine', medicine.id],
      queryFn: async () => (await api.get<Medicine>(`/medicines/${medicine.id}/`)).data,
    })
    const [form, setForm] = useState({
      batch_number: '', expiry_date: '', mfg_date: '', quantity: '', purchase_cost: '', mrp: '',
    })
    const add = useMutation({
      mutationFn: () => api.post('/batches/', {
        medicine: medicine.id, ...form, mfg_date: form.mfg_date || null,
      }),
      onSuccess: () => { setForm({ batch_number: '', expiry_date: '', mfg_date: '', quantity: '', purchase_cost: '', mrp: '' }); qc.invalidateQueries({ queryKey: ['medicine', medicine.id] }) },
    })
    const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

    return (
      <Modal title={`Batches · ${medicine.name}`} onClose={onClose} wide>
        <div className="card overflow-hidden mb-4">
          <table className="w-full text-[13px]">
            <thead className="bg-canvas text-muted text-[11px] uppercase">
              <tr>
                <th className="text-left px-3 py-2">Batch</th>
                <th className="text-left px-2">Expiry</th>
                <th className="text-right px-2">Qty</th>
                <th className="text-right px-2">MRP</th>
                <th className="text-right px-3">Days left</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {!data?.batches?.length && <tr><td colSpan={5}><Empty>No batches yet.</Empty></td></tr>}
              {data?.batches?.map((b) => (
                <tr key={b.id} className={b.days_to_expiry <= 90 ? 'bg-[#fdf3e7]/40' : ''}>
                  <td className="px-3 py-2 font-mono">{b.batch_number}</td>
                  <td className="px-2">{b.expiry_date}</td>
                  <td className="px-2 text-right">{b.quantity}</td>
                  <td className="px-2 text-right">{inr(b.mrp)}</td>
                  <td className={`px-3 text-right font-semibold ${b.days_to_expiry <= 90 ? 'text-warn' : 'text-muted'}`}>
                    {b.days_to_expiry}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="text-[12px] font-semibold text-muted mb-2">Add / receive batch</div>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Batch number *" v={form.batch_number} on={(v) => set('batch_number', v)} />
          <Field label="Expiry date *" v={form.expiry_date} on={(v) => set('expiry_date', v)} type="date" />
          <Field label="Mfg date" v={form.mfg_date} on={(v) => set('mfg_date', v)} type="date" />
          <Field label="Quantity *" v={form.quantity} on={(v) => set('quantity', v)} type="number" />
          <Field label="Purchase cost" v={form.purchase_cost} on={(v) => set('purchase_cost', v)} type="number" />
          <Field label="MRP *" v={form.mrp} on={(v) => set('mrp', v)} type="number" />
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button className="btn-ghost" onClick={onClose}>Done</button>
          <button className="btn-primary"
            disabled={!form.batch_number || !form.expiry_date || !form.quantity || add.isPending}
            onClick={() => add.mutate()}>
            {add.isPending ? 'Adding…' : 'Add batch'}
          </button>
        </div>
      </Modal>
    )
  }
}

function Field({ label, v, on, type = 'text', className = '' }: {
  label: string; v: string; on: (v: string) => void; type?: string; className?: string
}) {
  return (
    <div className={className}>
      <label className="label">{label}</label>
      <input type={type} value={v} onChange={(e) => on(e.target.value)} className="input" />
    </div>
  )
}
