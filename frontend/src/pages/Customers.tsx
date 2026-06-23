import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Star, Search } from 'lucide-react'
import { api, inr } from '../lib/api'
import type { Customer, Paginated } from '../lib/types'
import { PageHeader, Empty, Modal } from '../components/ui'

export default function Customers() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [show, setShow] = useState(false)

  const { data } = useQuery({
    queryKey: ['customers', search],
    queryFn: async () =>
      (await api.get<Paginated<Customer>>('/customers/', { params: { search } })).data,
  })

  return (
    <div>
      <PageHeader
        title="Customers"
        subtitle="Regular customers (★) get quick re-bill and credit / khata"
        actions={<button className="btn-primary" onClick={() => setShow(true)}><Plus size={16} /> Add customer</button>}
      />

      <div className="card p-3 mb-4">
        <div className="relative">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-faint" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name or phone…" className="input pl-10" />
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-[13px]">
          <thead className="bg-canvas text-muted text-[11.5px] uppercase tracking-wide">
            <tr>
              <th className="text-left font-semibold px-4 py-2.5">Name</th>
              <th className="text-left font-semibold px-2">Phone</th>
              <th className="text-center font-semibold px-2">Regular</th>
              <th className="text-right font-semibold px-2">Bills</th>
              <th className="text-right font-semibold px-4">Credit balance</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {data?.results.length === 0 && <tr><td colSpan={5}><Empty>No customers yet.</Empty></td></tr>}
            {data?.results.map((c) => (
              <tr key={c.id} className="hover:bg-canvas/60">
                <td className="px-4 py-2.5 font-semibold">{c.name}</td>
                <td className="px-2 font-mono text-[12px]">{c.phone || '—'}</td>
                <td className="px-2 text-center">
                  {c.is_regular && <Star size={15} className="inline text-warn fill-warn" />}
                </td>
                <td className="px-2 text-right">{c.invoice_count ?? 0}</td>
                <td className="px-4 text-right font-mono">
                  {Number(c.credit_balance) > 0
                    ? <span className="text-warn font-semibold">{inr(c.credit_balance)}</span>
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {show && <AddCustomer onClose={() => { setShow(false); qc.invalidateQueries({ queryKey: ['customers'] }) }} />}
    </div>
  )
}

function AddCustomer({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({
    name: '', phone: '', address: '', is_regular: false, allow_credit: false, consent_given: false,
  })
  const create = useMutation({ mutationFn: () => api.post('/customers/', form), onSuccess: onClose })

  return (
    <Modal title="Add customer" onClose={onClose}>
      <div className="space-y-3">
        <div>
          <label className="label">Name *</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div>
          <label className="label">Phone</label>
          <input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        </div>
        <div>
          <label className="label">Address</label>
          <textarea className="input" rows={2} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
        </div>
        <div className="flex flex-col gap-2 pt-1">
          {([['is_regular', 'Regular customer'], ['allow_credit', 'Allow credit / khata'], ['consent_given', 'Consent given to store personal data (DPDP)']] as const).map(([k, label]) => (
            <label key={k} className="flex items-center gap-2 text-[13px]">
              <input type="checkbox" checked={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.checked })} />
              {label}
            </label>
          ))}
        </div>
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
