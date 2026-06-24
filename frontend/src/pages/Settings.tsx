import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Check, Plus, Trash2, Upload } from 'lucide-react'
import { api, putForm } from '../lib/api'
import type { LeadTime, Paginated, PaymentTerm } from '../lib/types'
import { PageHeader, Empty } from '../components/ui'

interface ShopSettings {
  shop_name: string; gstin: string; drug_licence_no: string; has_drug_license: boolean
  logo: string | null; address: string; phone: string; email: string
  near_expiry_days: number; default_reorder_level: number; default_reorder_qty: number
  default_gst_rate: string; po_prefix: string; po_next_number: number; invoice_prefix: string
}

export default function SettingsPage() {
  const qc = useQueryClient()
  const [form, setForm] = useState<ShopSettings | null>(null)
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [done, setDone] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const { data } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => (await api.get<ShopSettings>('/settings/')).data,
  })
  useEffect(() => { if (data) setForm(data) }, [data])

  const [err, setErr] = useState('')
  const save = useMutation({
    mutationFn: () => {
      // Multipart so the logo (if chosen) uploads alongside the text fields.
      const fd = new FormData()
      Object.entries(form ?? {}).forEach(([k, v]) => {
        if (k === 'logo' || k === 'updated_at' || v == null) return
        fd.append(k, typeof v === 'boolean' ? String(v) : String(v))
      })
      if (logoFile) fd.append('logo', logoFile)
      return putForm('/settings/', fd)
    },
    onSuccess: () => {
      setDone(true); setLogoFile(null); setErr('')
      qc.invalidateQueries({ queryKey: ['settings'] })
      qc.invalidateQueries({ queryKey: ['shop'] })
      setTimeout(() => setDone(false), 2000)
    },
    onError: (e: any) => setErr(
      typeof e?.response?.data === 'object'
        ? Object.entries(e.response.data).map(([k, v]) => `${k}: ${v}`).join('; ')
        : 'Could not save settings.'),
  })

  if (!form) return null
  const set = (k: keyof ShopSettings, v: string | number | boolean) => setForm({ ...form, [k]: v })

  return (
    <div className="max-w-3xl">
      <PageHeader title="Settings" subtitle="Shop identity, documents, defaults and masters" />

      <div className="card p-5 mb-5">
        <h3 className="font-bold text-[14px] mb-4">Shop &amp; licence</h3>
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-lg border border-line bg-canvas grid place-items-center overflow-hidden">
            {logoFile ? <img src={URL.createObjectURL(logoFile)} className="w-full h-full object-contain" />
              : form.logo ? <img src={form.logo} className="w-full h-full object-contain" />
              : <span className="text-[10px] text-faint">No logo</span>}
          </div>
          <div>
            <input ref={fileRef} type="file" accept="image/*" className="hidden"
              onChange={(e) => setLogoFile(e.target.files?.[0] ?? null)} />
            <button className="btn-ghost" onClick={() => fileRef.current?.click()}><Upload size={15} /> Upload logo</button>
            <p className="text-[11px] text-muted mt-1">Shown on the PO document.</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <F label="Shop name" v={form.shop_name} on={(v) => set('shop_name', v)} className="col-span-2" />
          <F label="GSTIN" v={form.gstin} on={(v) => set('gstin', v)} />
          <F label="Drug licence no." v={form.drug_licence_no} on={(v) => set('drug_licence_no', v)} />
          <F label="Phone" v={form.phone} on={(v) => set('phone', v)} />
          <F label="Email" v={form.email} on={(v) => set('email', v)} />
          <div className="col-span-2">
            <label className="label">Address</label>
            <textarea className="input" rows={2} value={form.address} onChange={(e) => set('address', e.target.value)} />
          </div>
          <label className="col-span-2 flex items-center gap-2 text-[13px]">
            <input type="checkbox" checked={form.has_drug_license} onChange={(e) => set('has_drug_license', e.target.checked)} />
            Shop holds a medical supply (drug) licence — print licence no. on documents
          </label>
        </div>
      </div>

      <div className="card p-5 mb-5">
        <h3 className="font-bold text-[14px] mb-4">Document numbering</h3>
        <div className="grid grid-cols-3 gap-4">
          <F label="Invoice prefix" v={form.invoice_prefix} on={(v) => set('invoice_prefix', v)} />
          <F label="PO prefix" v={form.po_prefix} on={(v) => set('po_prefix', v)} />
          <F label="Next PO number" v={String(form.po_next_number)} on={(v) => set('po_next_number', Number(v))} type="number" />
        </div>
        <p className="text-[11.5px] text-muted mt-2">Next PO will be <b>{form.po_prefix}-{String(form.po_next_number).padStart(5, '0')}</b>.</p>
      </div>

      <div className="card p-5 mb-5">
        <h3 className="font-bold text-[14px] mb-4">Operational defaults</h3>
        <div className="grid grid-cols-3 gap-4">
          <F label="Near-expiry window (days)" v={String(form.near_expiry_days)} on={(v) => set('near_expiry_days', Number(v))} type="number" />
          <F label="Default reorder level" v={String(form.default_reorder_level)} on={(v) => set('default_reorder_level', Number(v))} type="number" />
          <F label="Default reorder qty" v={String(form.default_reorder_qty)} on={(v) => set('default_reorder_qty', Number(v))} type="number" />
        </div>
      </div>

      <div className="mb-8">
        <button className="btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>
          {done ? <><Check size={16} /> Saved</> : <><Save size={16} /> {save.isPending ? 'Saving…' : 'Save settings'}</>}
        </button>
        {err && <p className="text-[12px] text-danger mt-2">{err}</p>}
      </div>

      <MasterEditor
        title="Payment terms" endpoint="/payment-terms/" qkey="payment-terms"
        fields={[{ k: 'name', label: 'Name', ph: '30 days credit' }, { k: 'days', label: 'Days', type: 'number' }]}
        render={(r: PaymentTerm) => `${r.name} · ${r.days}d`} />
      <MasterEditor
        title="Lead times" endpoint="/lead-times/" qkey="lead-times"
        fields={[{ k: 'label', label: 'Label', ph: 'Next day' }, { k: 'days', label: 'Days', type: 'number' }]}
        render={(r: LeadTime) => `${r.label} · ${r.days}d`} />
    </div>
  )
}

interface MasterField { k: string; label: string; ph?: string; type?: string }
function MasterEditor<T extends { id: number }>({ title, endpoint, qkey, fields, render }: {
  title: string; endpoint: string; qkey: string; fields: MasterField[]; render: (r: T) => string
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState<Record<string, string>>({})
  const { data } = useQuery({ queryKey: [qkey], queryFn: async () => (await api.get<Paginated<T>>(endpoint)).data.results })
  const add = useMutation({
    mutationFn: () => api.post(endpoint, form),
    onSuccess: () => { setForm({}); qc.invalidateQueries({ queryKey: [qkey] }) },
  })
  const del = useMutation({
    mutationFn: (id: number) => api.delete(`${endpoint}${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: [qkey] }),
  })

  return (
    <div className="card p-5 mb-5">
      <h3 className="font-bold text-[14px] mb-3">{title} <span className="text-muted font-normal text-[12px]">master</span></h3>
      <div className="flex flex-wrap gap-2 mb-3">
        {!data?.length && <Empty>None yet.</Empty>}
        {data?.map((r) => (
          <span key={r.id} className="inline-flex items-center gap-1.5 bg-canvas border border-line rounded-lg px-2.5 py-1 text-[12.5px]">
            {render(r)}
            <button className="text-faint hover:text-danger" onClick={() => del.mutate(r.id)}><Trash2 size={12} /></button>
          </span>
        ))}
      </div>
      <div className="flex gap-2 items-end">
        {fields.map((f) => (
          <div key={f.k} className="flex-1">
            <label className="label">{f.label}</label>
            <input type={f.type ?? 'text'} placeholder={f.ph} className="input !py-2"
              value={form[f.k] ?? ''} onChange={(e) => setForm((s) => ({ ...s, [f.k]: e.target.value }))} />
          </div>
        ))}
        <button className="btn-primary !py-2.5" disabled={!fields.every((f) => form[f.k]) || add.isPending} onClick={() => add.mutate()}>
          <Plus size={15} /> Add
        </button>
      </div>
    </div>
  )
}

function F({ label, v, on, type = 'text', className = '' }: {
  label: string; v: string; on: (v: string) => void; type?: string; className?: string
}) {
  return (
    <div className={className}>
      <label className="label">{label}</label>
      <input type={type} value={v} onChange={(e) => on(e.target.value)} className="input" />
    </div>
  )
}
