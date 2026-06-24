import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Layers, Pencil, Info, RotateCcw, Check, Ban, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import type { Batch, Medicine, Paginated, StockMovement, Supplier } from '../lib/types'
import { PageHeader, StatusBadge, ScheduleBadge, Empty, Modal } from '../components/ui'

const SCHEDULES = ['OTC', 'H', 'H1', 'X']

const MED_TYPES: [string, string][] = [
  ['tablet', 'Tablet / capsule'], ['syrup', 'Syrup / liquid'], ['injection', 'Injection'],
  ['drops', 'Drops'], ['ointment', 'Ointment / cream'], ['commercial', 'Commercial product'],
  ['other', 'Other'],
]

const SCHEDULE_HELP: { code: string; title: string; desc: string }[] = [
  { code: 'OTC', title: 'Over the counter', desc: 'No prescription required.' },
  { code: 'H', title: 'Schedule H', desc: 'Prescription required to dispense.' },
  { code: 'H1', title: 'Schedule H1', desc: 'Prescription required; sale recorded in the H1 register (kept 3 years).' },
  { code: 'X', title: 'Schedule X', desc: 'Prescription required; strictest controls (narcotic/psychotropic).' },
]

export default function Inventory() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [editMed, setEditMed] = useState<Medicine | null | undefined>(undefined) // null=add, Medicine=edit
  const [batchFor, setBatchFor] = useState<Medicine | null>(null)
  const [showGuide, setShowGuide] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['medicines', 'list', search],
    queryFn: async () =>
      (await api.get<Paginated<Medicine>>('/medicines/', { params: { search } })).data,
  })
  const closeMed = () => { setEditMed(undefined); qc.invalidateQueries({ queryKey: ['medicines'] }) }

  return (
    <div>
      <PageHeader
        title="Inventory"
        subtitle="Medicine master with batch &amp; expiry tracking"
        actions={
          <>
            <button className="btn-ghost" onClick={() => setShowGuide((s) => !s)}>
              <Info size={16} /> Schedule guide
            </button>
            <button className="btn-primary" onClick={() => setEditMed(null)}>
              <Plus size={16} /> Add medicine
            </button>
          </>
        }
      />

      {showGuide && (
        <div className="card p-4 mb-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {SCHEDULE_HELP.map((s) => (
            <div key={s.code} className="flex gap-2">
              <ScheduleBadge schedule={s.code} />
              <div>
                <div className="font-semibold text-[12.5px]">{s.title}</div>
                <div className="text-[11.5px] text-muted">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      )}

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
                  <div className="font-semibold flex items-center gap-2">
                    {m.name}
                    {!m.is_active && <span className="text-[10px] font-bold rounded px-1.5 py-0.5 bg-canvas text-faint uppercase">Discontinued</span>}
                  </div>
                  <div className="text-[11.5px] text-muted">
                    {m.generic_name} · {m.manufacturer}
                    {m.med_type_display && <span> · {m.med_type_display}</span>}
                    {m.sells_loose && <span className="text-accent"> · {m.units_per_pack}/pack</span>}
                  </div>
                </td>
                <td className="px-2"><ScheduleBadge schedule={m.schedule} /></td>
                <td className="px-2 text-muted font-mono text-[12px]">{m.rack_location || '—'}</td>
                <td className="px-2 text-right">{m.gst_rate}%</td>
                <td className="px-2 text-right font-semibold">{m.total_stock}</td>
                <td className="px-2"><StatusBadge status={m.stock_status} /></td>
                <td className="px-4 text-right whitespace-nowrap">
                  <button className="btn-ghost !py-1.5 !px-2.5 mr-1.5" onClick={() => setEditMed(m)}>
                    <Pencil size={14} /> Edit
                  </button>
                  <button className="btn-ghost !py-1.5 !px-2.5" onClick={() => setBatchFor(m)}>
                    <Layers size={14} /> Batches
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editMed !== undefined && <MedicineModal medicine={editMed} onClose={closeMed} />}
      {batchFor && <BatchModal medicine={batchFor} onClose={() => { setBatchFor(null); qc.invalidateQueries({ queryKey: ['medicines'] }) }} />}
    </div>
  )
}

function MedicineModal({ medicine, onClose }: { medicine: Medicine | null; onClose: () => void }) {
  const isEdit = !!medicine
  const [form, setForm] = useState({
    name: medicine?.name ?? '', generic_name: medicine?.generic_name ?? '',
    manufacturer: medicine?.manufacturer ?? '', med_type: medicine?.med_type ?? 'tablet',
    hsn_code: medicine?.hsn_code ?? '',
    gst_rate: String(medicine?.gst_rate ?? '12'), schedule: medicine?.schedule ?? 'OTC',
    pack_unit: medicine?.pack_unit ?? '', units_per_pack: String(medicine?.units_per_pack ?? '1'),
    rack_location: medicine?.rack_location ?? '',
    barcode: medicine?.barcode ?? '', reorder_level: String(medicine?.reorder_level ?? '10'),
    reorder_qty: String(medicine?.reorder_qty ?? '50'),
    preferred_supplier: medicine?.preferred_supplier ? String(medicine.preferred_supplier) : '',
  })
  const { data: suppliers } = useQuery({
    queryKey: ['suppliers', 'all'],
    queryFn: async () => (await api.get<Paginated<Supplier>>('/suppliers/')).data.results,
  })
  const save = useMutation({
    mutationFn: () => {
      const payload = { ...form, preferred_supplier: form.preferred_supplier || null }
      return isEdit
        ? api.patch(`/medicines/${medicine!.id}/`, payload)
        : api.post('/medicines/', payload)
    },
    onSuccess: onClose,
  })
  const [actionMsg, setActionMsg] = useState('')
  const discontinue = useMutation({
    mutationFn: (reactivate: boolean) =>
      api.post(`/medicines/${medicine!.id}/discontinue/`, { reactivate }),
    onSuccess: onClose,
  })
  const del = useMutation({
    mutationFn: () => api.delete(`/medicines/${medicine!.id}/`),
    onSuccess: onClose,
    onError: (e: any) => setActionMsg(e?.response?.data?.detail ?? 'Could not delete medicine.'),
  })
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

  return (
    <Modal title={isEdit ? `Edit · ${medicine!.name}` : 'Add medicine'} onClose={onClose} wide>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Name *" v={form.name} on={(v) => set('name', v)} className="col-span-2" />
        <Field label="Generic / composition" v={form.generic_name} on={(v) => set('generic_name', v)} />
        <Field label="Manufacturer" v={form.manufacturer} on={(v) => set('manufacturer', v)} />
        <div>
          <label className="label">Type</label>
          <select className="input" value={form.med_type} onChange={(e) => set('med_type', e.target.value)}>
            {MED_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
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
        <div>
          <label className="label">Units per pack</label>
          <input type="number" min={1} value={form.units_per_pack}
            onChange={(e) => set('units_per_pack', e.target.value)} className="input" />
          <p className="text-[10.5px] text-muted mt-0.5">e.g. 10 tablets/strip — enables loose sale. Use 1 for syrups.</p>
        </div>
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
      {isEdit && (
        <div className="mt-5 pt-4 border-t border-line">
          <div className="text-[12px] font-semibold text-muted mb-2">Discontinue this medicine</div>
          <div className="flex flex-wrap items-center gap-2">
            {medicine!.is_active ? (
              <button className="btn-ghost !border-warn/40 !text-warn"
                disabled={discontinue.isPending}
                onClick={() => discontinue.mutate(false)}>
                <Ban size={15} /> Discontinue (hide from billing)
              </button>
            ) : (
              <button className="btn-ghost !border-ok/40 !text-ok"
                disabled={discontinue.isPending}
                onClick={() => discontinue.mutate(true)}>
                <RotateCcw size={15} /> Reactivate
              </button>
            )}
            <button className="btn-ghost !border-danger/40 !text-danger"
              disabled={del.isPending}
              onClick={() => { if (confirm('Delete this medicine permanently? This only works if it has no sales/PO/Rx history.')) del.mutate() }}>
              <Trash2 size={15} /> Delete permanently
            </button>
          </div>
          {actionMsg && <p className="text-[12px] text-danger mt-2">{actionMsg}</p>}
          <p className="text-[11px] text-muted mt-1.5">
            Discontinue keeps the medicine's history (invoices, reports, H1). Permanent
            delete is only for items added by mistake with no history.
          </p>
        </div>
      )}

      <div className="flex justify-end gap-2 mt-5">
        <button className="btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn-primary" disabled={!form.name || save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? 'Saving…' : isEdit ? 'Save changes' : 'Save medicine'}
        </button>
      </div>
    </Modal>
  )
}

function BatchModal({ medicine, onClose }: { medicine: Medicine; onClose: () => void }) {
  const qc = useQueryClient()
  const [tab, setTab] = useState<'batches' | 'adjust'>('batches')
  const { data } = useQuery({
    queryKey: ['medicine', medicine.id],
    queryFn: async () => (await api.get<Medicine>(`/medicines/${medicine.id}/`)).data,
  })
  const [form, setForm] = useState({
    batch_number: '', expiry_date: '', mfg_date: '', quantity: '', purchase_cost: '', mrp: '',
  })
  const [err, setErr] = useState('')
  const add = useMutation({
    mutationFn: () => api.post('/batches/', { medicine: medicine.id, ...form, mfg_date: form.mfg_date || null }),
    onSuccess: () => { setForm({ batch_number: '', expiry_date: '', mfg_date: '', quantity: '', purchase_cost: '', mrp: '' }); setErr(''); refresh() },
    onError: (e: any) => setErr(e?.response?.data?.expiry_date?.[0] ?? e?.response?.data?.detail ?? 'Could not add batch.'),
  })
  const refresh = () => { qc.invalidateQueries({ queryKey: ['medicine', medicine.id] }); qc.invalidateQueries({ queryKey: ['movements', medicine.id] }) }
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

  return (
    <Modal title={`${medicine.name}`} onClose={onClose} wide>
      <div className="flex gap-1 mb-4 border-b border-line">
        {(['batches', 'adjust'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3.5 py-2 text-[13px] font-semibold capitalize border-b-2 -mb-px ${
              tab === t ? 'border-accent text-accent' : 'border-transparent text-muted'
            }`}>
            {t === 'batches' ? 'Batches' : 'Adjust stock'}
          </button>
        ))}
      </div>

      {tab === 'batches' && (
        <>
          <div className="card overflow-hidden mb-4">
            <table className="w-full text-[13px]">
              <thead className="bg-canvas text-muted text-[11px] uppercase">
                <tr>
                  <th className="text-left px-3 py-2">Batch</th>
                  <th className="text-left px-2">Expiry</th>
                  <th className="text-right px-2">Qty</th>
                  <th className="text-right px-2">Cost</th>
                  <th className="text-right px-2">MRP / price</th>
                  <th className="text-right px-3">Days</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {!data?.batches?.length && <tr><td colSpan={7}><Empty>No batches yet.</Empty></td></tr>}
                {data?.batches?.map((b) => (
                  <BatchPriceRow key={b.id} batch={b} onSaved={refresh} />
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[11.5px] text-muted mb-3">Edit a batch's <b>Cost</b> or <b>MRP/price</b> above and click ✓ to save. Billing uses the MRP of the earliest-expiring batch.</p>

          <div className="text-[12px] font-semibold text-muted mb-2">Add / receive batch</div>
          <div className="grid grid-cols-3 gap-3">
            <Field label="Batch number *" v={form.batch_number} on={(v) => set('batch_number', v)} />
            <Field label="Expiry date *" v={form.expiry_date} on={(v) => set('expiry_date', v)} type="date" />
            <Field label="Mfg date" v={form.mfg_date} on={(v) => set('mfg_date', v)} type="date" />
            <Field label="Quantity *" v={form.quantity} on={(v) => set('quantity', v)} type="number" />
            <Field label="Purchase cost" v={form.purchase_cost} on={(v) => set('purchase_cost', v)} type="number" />
            <Field label="MRP *" v={form.mrp} on={(v) => set('mrp', v)} type="number" />
          </div>
          {err && <p className="text-[12px] text-danger mt-2">{err}</p>}
          <div className="flex justify-end gap-2 mt-5">
            <button className="btn-ghost" onClick={onClose}>Done</button>
            <button className="btn-primary"
              disabled={!form.batch_number || !form.expiry_date || !form.quantity || add.isPending}
              onClick={() => add.mutate()}>
              {add.isPending ? 'Adding…' : 'Add batch'}
            </button>
          </div>
        </>
      )}

      {tab === 'adjust' && <AdjustTab medicine={medicine} batches={data?.batches ?? []} onChange={refresh} />}
    </Modal>
  )
}

function AdjustTab({ medicine, batches, onChange }: { medicine: Medicine; batches: NonNullable<Medicine['batches']>; onChange: () => void }) {
  const qc = useQueryClient()
  const [batch, setBatch] = useState('')
  const [qty, setQty] = useState('')
  const [reason, setReason] = useState('damage')
  const [note, setNote] = useState('')

  const { data: movements } = useQuery({
    queryKey: ['movements', medicine.id],
    queryFn: async () => {
      const ids = (medicine.batches ?? batches).map((b) => b.id)
      const all = await Promise.all(ids.map((id) =>
        api.get<Paginated<StockMovement>>(`/stock-movements/?batch=${id}`).then((r) => r.data.results)))
      return all.flat().filter((m) => ['damage', 'expiry', 'count'].includes(m.reason))
        .sort((a, b) => b.id - a.id).slice(0, 15)
    },
  })
  const adjust = useMutation({
    mutationFn: () => api.post(`/medicines/${medicine.id}/adjust/`, { batch: Number(batch), quantity: Number(qty), reason, note }),
    onSuccess: () => { setQty(''); setNote(''); onChange(); qc.invalidateQueries({ queryKey: ['movements', medicine.id] }) },
  })
  const reverse = useMutation({
    mutationFn: (id: number) => api.post(`/stock-movements/${id}/reverse/`),
    onSuccess: () => { onChange(); qc.invalidateQueries({ queryKey: ['movements', medicine.id] }) },
  })

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 items-end">
        <div className="col-span-2">
          <label className="label">Batch</label>
          <select className="input !py-2" value={batch} onChange={(e) => setBatch(e.target.value)}>
            <option value="">Select batch…</option>
            {batches.map((b) => <option key={b.id} value={b.id}>{b.batch_number} ({b.quantity})</option>)}
          </select>
        </div>
        <div>
          <label className="label">Reason</label>
          <select className="input !py-2" value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="damage">Damage</option>
            <option value="expiry">Expiry write-off</option>
            <option value="count">Count correction</option>
          </select>
        </div>
        <div>
          <label className="label">Qty (±)</label>
          <input type="number" className="input !py-2" value={qty} onChange={(e) => setQty(e.target.value)} placeholder="-5" />
        </div>
        <button className="btn-primary !py-2.5" disabled={!batch || !qty || adjust.isPending} onClick={() => adjust.mutate()}>
          Post
        </button>
      </div>
      <input className="input mt-2" placeholder="Note (e.g. breakage, spillage)" value={note} onChange={(e) => setNote(e.target.value)} />

      <div className="text-[12px] font-semibold text-muted mt-5 mb-2">Recent adjustments</div>
      <div className="card overflow-hidden">
        <table className="w-full text-[12.5px]">
          <tbody className="divide-y divide-line">
            {!movements?.length && <tr><td><Empty>No adjustments yet.</Empty></td></tr>}
            {movements?.map((m) => (
              <tr key={m.id} className={m.reversed ? 'opacity-50' : ''}>
                <td className="px-3 py-2">{m.reason_display}</td>
                <td className="px-2 font-mono">{m.quantity > 0 ? `+${m.quantity}` : m.quantity}</td>
                <td className="px-2 text-muted">{m.note}</td>
                <td className="px-2 text-muted text-[11px]">{new Date(m.created_at).toLocaleDateString()}</td>
                <td className="px-3 text-right">
                  {m.note.startsWith('Reversal') ? <span className="text-[11px] text-muted">reversal</span>
                    : m.reversed ? <span className="text-[11px] text-muted">reversed</span>
                    : <button className="btn-ghost !py-1 !px-2 text-[11px]" disabled={reverse.isPending} onClick={() => reverse.mutate(m.id)}>
                        <RotateCcw size={12} /> Reverse
                      </button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function BatchPriceRow({ batch, onSaved }: { batch: Batch; onSaved: () => void }) {
  const [cost, setCost] = useState(String(batch.purchase_cost))
  const [mrp, setMrp] = useState(String(batch.mrp))
  const dirty = cost !== String(batch.purchase_cost) || mrp !== String(batch.mrp)
  const save = useMutation({
    mutationFn: () => api.patch(`/batches/${batch.id}/`, { purchase_cost: cost, mrp }),
    onSuccess: onSaved,
  })
  return (
    <tr className={batch.days_to_expiry <= 90 ? 'bg-[#fdf3e7]/40' : ''}>
      <td className="px-3 py-2 font-mono">{batch.batch_number}</td>
      <td className="px-2">{batch.expiry_date}</td>
      <td className="px-2 text-right">{batch.quantity}</td>
      <td className="px-2 text-right">
        <input type="number" min={0} value={cost} onChange={(e) => setCost(e.target.value)}
          className="w-20 text-right border border-line rounded-md py-1 px-1.5" />
      </td>
      <td className="px-2 text-right">
        <input type="number" min={0} value={mrp} onChange={(e) => setMrp(e.target.value)}
          className="w-20 text-right border border-line rounded-md py-1 px-1.5 font-semibold" />
      </td>
      <td className={`px-3 text-right font-semibold ${batch.days_to_expiry <= 90 ? 'text-warn' : 'text-muted'}`}>
        {batch.days_to_expiry}
      </td>
      <td className="px-2 text-right">
        {dirty && (
          <button onClick={() => save.mutate()} disabled={save.isPending}
            className="text-ok hover:bg-[#eaf6ee] rounded p-1" title="Save price">
            <Check size={16} />
          </button>
        )}
      </td>
    </tr>
  )
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
