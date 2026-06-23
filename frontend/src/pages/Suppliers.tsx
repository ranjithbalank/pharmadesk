import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { api } from '../lib/api'
import type { Paginated, Supplier } from '../lib/types'
import { PageHeader, Empty, Modal } from '../components/ui'

export default function Suppliers() {
  const qc = useQueryClient()
  const [show, setShow] = useState(false)

  const { data } = useQuery({
    queryKey: ['suppliers'],
    queryFn: async () => (await api.get<Paginated<Supplier>>('/suppliers/')).data,
  })

  return (
    <div>
      <PageHeader
        title="Suppliers"
        subtitle="Distributor master — GSTIN, lead time, payment terms"
        actions={<button className="btn-primary" onClick={() => setShow(true)}><Plus size={16} /> Add supplier</button>}
      />

      <div className="card overflow-hidden">
        <table className="w-full text-[13px]">
          <thead className="bg-canvas text-muted text-[11.5px] uppercase tracking-wide">
            <tr>
              <th className="text-left font-semibold px-4 py-2.5">Supplier</th>
              <th className="text-left font-semibold px-2">GSTIN</th>
              <th className="text-left font-semibold px-2">Contact</th>
              <th className="text-left font-semibold px-2">Terms</th>
              <th className="text-right font-semibold px-4">Lead time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data?.results.length === 0 && <tr><td colSpan={5}><Empty>No suppliers yet.</Empty></td></tr>}
            {data?.results.map((s) => (
              <tr key={s.id} className="hover:bg-canvas/60">
                <td className="px-4 py-2.5 font-semibold">{s.name}</td>
                <td className="px-2 font-mono text-[12px]">{s.gstin || '—'}</td>
                <td className="px-2">{s.contact_person} {s.phone && <span className="text-muted">· {s.phone}</span>}</td>
                <td className="px-2 text-muted">{s.payment_terms || '—'}</td>
                <td className="px-4 text-right">{s.lead_time_days} days</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {show && <AddSupplier onClose={() => { setShow(false); qc.invalidateQueries({ queryKey: ['suppliers'] }) }} />}
    </div>
  )
}

function AddSupplier({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({
    name: '', gstin: '', contact_person: '', phone: '', email: '',
    address: '', payment_terms: '', lead_time_days: '3',
  })
  const create = useMutation({ mutationFn: () => api.post('/suppliers/', form), onSuccess: onClose })
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

  return (
    <Modal title="Add supplier" onClose={onClose} wide>
      <div className="grid grid-cols-2 gap-3">
        <F label="Name *" v={form.name} on={(v) => set('name', v)} className="col-span-2" />
        <F label="GSTIN" v={form.gstin} on={(v) => set('gstin', v)} />
        <F label="Contact person" v={form.contact_person} on={(v) => set('contact_person', v)} />
        <F label="Phone" v={form.phone} on={(v) => set('phone', v)} />
        <F label="Email" v={form.email} on={(v) => set('email', v)} />
        <F label="Payment terms" v={form.payment_terms} on={(v) => set('payment_terms', v)} />
        <F label="Lead time (days)" v={form.lead_time_days} on={(v) => set('lead_time_days', v)} type="number" />
        <F label="Address" v={form.address} on={(v) => set('address', v)} className="col-span-2" />
      </div>
      <div className="flex justify-end gap-2 mt-5">
        <button className="btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn-primary" disabled={!form.name || create.isPending} onClick={() => create.mutate()}>
          {create.isPending ? 'Saving…' : 'Save'}
        </button>
      </div>
    </Modal>
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
