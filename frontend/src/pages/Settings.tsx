import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Check } from 'lucide-react'
import { api } from '../lib/api'
import { PageHeader } from '../components/ui'

interface ShopSettings {
  shop_name: string; gstin: string; drug_licence_no: string; address: string
  phone: string; email: string; near_expiry_days: number
  default_reorder_level: number; default_reorder_qty: number; default_gst_rate: string
}

export default function SettingsPage() {
  const qc = useQueryClient()
  const [form, setForm] = useState<ShopSettings | null>(null)
  const [done, setDone] = useState(false)

  const { data } = useQuery({
    queryKey: ['settings'],
    queryFn: async () => (await api.get<ShopSettings>('/settings/')).data,
  })
  useEffect(() => { if (data) setForm(data) }, [data])

  const save = useMutation({
    mutationFn: () => api.put('/settings/', form),
    onSuccess: () => { setDone(true); qc.invalidateQueries({ queryKey: ['settings'] }); setTimeout(() => setDone(false), 2000) },
  })

  if (!form) return null
  const set = (k: keyof ShopSettings, v: string | number) => setForm({ ...form, [k]: v })

  return (
    <div className="max-w-3xl">
      <PageHeader title="Settings" subtitle="Shop identity, GST and operational defaults" />

      <div className="card p-5 mb-5">
        <h3 className="font-bold text-[14px] mb-4">Shop &amp; licence</h3>
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
        </div>
      </div>

      <div className="card p-5 mb-5">
        <h3 className="font-bold text-[14px] mb-4">Operational defaults</h3>
        <div className="grid grid-cols-3 gap-4">
          <F label="Near-expiry window (days)" v={String(form.near_expiry_days)} on={(v) => set('near_expiry_days', Number(v))} type="number" />
          <F label="Default reorder level" v={String(form.default_reorder_level)} on={(v) => set('default_reorder_level', Number(v))} type="number" />
          <F label="Default reorder qty" v={String(form.default_reorder_qty)} on={(v) => set('default_reorder_qty', Number(v))} type="number" />
        </div>
      </div>

      <button className="btn-primary" disabled={save.isPending} onClick={() => save.mutate()}>
        {done ? <><Check size={16} /> Saved</> : <><Save size={16} /> {save.isPending ? 'Saving…' : 'Save settings'}</>}
      </button>
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
