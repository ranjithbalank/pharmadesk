import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil } from 'lucide-react'
import { api } from '../lib/api'
import type { LeadTime, Paginated, PaymentTerm, Supplier } from '../lib/types'
import { PageHeader, Empty, Modal } from '../components/ui'

export default function Suppliers() {
  const qc = useQueryClient()
  const [edit, setEdit] = useState<Supplier | null | undefined>(undefined)

  const { data } = useQuery({
    queryKey: ['suppliers'],
    queryFn: async () => (await api.get<Paginated<Supplier>>('/suppliers/')).data,
  })
  const close = () => { setEdit(undefined); qc.invalidateQueries({ queryKey: ['suppliers'] }) }

  return (
    <div>
      <PageHeader
        title="Suppliers"
        subtitle="Distributor master — code, GSTIN, licence, terms &amp; lead time"
        actions={<button className="btn-primary" onClick={() => setEdit(null)}><Plus size={16} /> Add supplier</button>}
      />

      <div className="card overflow-hidden">
        <table className="w-full text-[13px]">
          <thead className="bg-canvas text-muted text-[11.5px] uppercase tracking-wide">
            <tr>
              <th className="text-left font-semibold px-4 py-2.5">Code</th>
              <th className="text-left font-semibold px-2">Supplier</th>
              <th className="text-left font-semibold px-2">GSTIN</th>
              <th className="text-left font-semibold px-2">Licence</th>
              <th className="text-left font-semibold px-2">Terms</th>
              <th className="text-right font-semibold px-2">Lead time</th>
              <th className="px-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data?.results.length === 0 && <tr><td colSpan={7}><Empty>No suppliers yet.</Empty></td></tr>}
            {data?.results.map((s) => (
              <tr key={s.id} className="hover:bg-canvas/60">
                <td className="px-4 py-2.5 font-mono text-[12px]">{s.code || '—'}</td>
                <td className="px-2 font-semibold">{s.name}</td>
                <td className="px-2 font-mono text-[12px]">{s.gstin || '—'}</td>
                <td className="px-2 text-[12px]">{s.has_drug_license ? (s.drug_license_no || 'Yes') : '—'}</td>
                <td className="px-2 text-muted">{s.payment_term_name || s.payment_terms || '—'}</td>
                <td className="px-2 text-right">{s.lead_time_label || `${s.lead_time_days} days`}</td>
                <td className="px-4 text-right">
                  <button className="btn-ghost !py-1.5 !px-2.5" onClick={() => setEdit(s)}><Pencil size={14} /> Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {edit !== undefined && <SupplierModal supplier={edit} onClose={close} />}
    </div>
  )
}

function SupplierModal({ supplier, onClose }: { supplier: Supplier | null; onClose: () => void }) {
  const isEdit = !!supplier
  const [form, setForm] = useState({
    code: supplier?.code ?? '', name: supplier?.name ?? '', gstin: supplier?.gstin ?? '',
    contact_person: supplier?.contact_person ?? '', phone: supplier?.phone ?? '',
    email: supplier?.email ?? '', address: supplier?.address ?? '',
    has_drug_license: supplier?.has_drug_license ?? false,
    drug_license_no: supplier?.drug_license_no ?? '',
    payment_term: supplier?.payment_term ? String(supplier.payment_term) : '',
    lead_time: supplier?.lead_time ? String(supplier.lead_time) : '',
  })
  const [err, setErr] = useState('')
  const { data: terms } = useQuery({ queryKey: ['payment-terms'], queryFn: async () => (await api.get<Paginated<PaymentTerm>>('/payment-terms/')).data.results })
  const { data: leads } = useQuery({ queryKey: ['lead-times'], queryFn: async () => (await api.get<Paginated<LeadTime>>('/lead-times/')).data.results })

  const save = useMutation({
    mutationFn: () => {
      const payload = { ...form, payment_term: form.payment_term || null, lead_time: form.lead_time || null }
      return isEdit ? api.patch(`/suppliers/${supplier!.id}/`, payload) : api.post('/suppliers/', payload)
    },
    onSuccess: onClose,
    onError: (e: any) => setErr(e?.response?.data?.drug_license_no?.[0] ?? 'Could not save supplier.'),
  })
  const set = (k: string, v: string | boolean) => setForm((f) => ({ ...f, [k]: v }))

  return (
    <Modal title={isEdit ? `Edit · ${supplier!.name}` : 'Add supplier'} onClose={onClose} wide>
      <div className="grid grid-cols-2 gap-3">
        <F label="Supplier code" v={form.code} on={(v) => set('code', v)} />
        <F label="Name *" v={form.name} on={(v) => set('name', v)} />
        <F label="GSTIN" v={form.gstin} on={(v) => set('gstin', v)} />
        <F label="Contact person" v={form.contact_person} on={(v) => set('contact_person', v)} />
        <F label="Phone" v={form.phone} on={(v) => set('phone', v)} />
        <F label="Email" v={form.email} on={(v) => set('email', v)} />
        <div>
          <label className="label">Payment term</label>
          <select className="input" value={form.payment_term} onChange={(e) => set('payment_term', e.target.value)}>
            <option value="">— select —</option>
            {terms?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Lead time</label>
          <select className="input" value={form.lead_time} onChange={(e) => set('lead_time', e.target.value)}>
            <option value="">— select —</option>
            {leads?.map((l) => <option key={l.id} value={l.id}>{l.label} ({l.days}d)</option>)}
          </select>
        </div>
        <F label="Address" v={form.address} on={(v) => set('address', v)} className="col-span-2" />
        <label className="col-span-2 flex items-center gap-2 text-[13px] mt-1">
          <input type="checkbox" checked={form.has_drug_license} onChange={(e) => set('has_drug_license', e.target.checked)} />
          Holds a medical supply (drug) licence
        </label>
        {form.has_drug_license && (
          <F label="Drug licence no. *" v={form.drug_license_no} on={(v) => set('drug_license_no', v)} className="col-span-2" />
        )}
      </div>
      {err && <p className="text-[12px] text-danger mt-2">{err}</p>}
      <p className="text-[11.5px] text-muted mt-3">Manage payment terms &amp; lead times in <b>Settings → Masters</b>.</p>
      <div className="flex justify-end gap-2 mt-4">
        <button className="btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn-primary" disabled={!form.name || save.isPending} onClick={() => save.mutate()}>
          {save.isPending ? 'Saving…' : isEdit ? 'Save changes' : 'Save supplier'}
        </button>
      </div>
    </Modal>
  )
}

function F({ label, v, on, className = '' }: { label: string; v: string; on: (v: string) => void; className?: string }) {
  return (
    <div className={className}>
      <label className="label">{label}</label>
      <input value={v} onChange={(e) => on(e.target.value)} className="input" />
    </div>
  )
}
