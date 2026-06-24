import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import {
  IndianRupee, Boxes, AlertTriangle, CalendarClock, PackageX, X,
  CalendarRange, Wallet, Filter,
} from 'lucide-react'
import { api, inr } from '../lib/api'
import type { Dashboard as Dash, NotificationItem } from '../lib/types'
import { PageHeader, Empty } from '../components/ui'

function StatCard({ icon, label, value, tone, to }: {
  icon: React.ReactNode; label: string; value: string; tone?: string; to?: string
}) {
  const body = (
    <div className="card p-4 flex items-center gap-4 hover:border-accent/40 transition">
      <div className={`w-11 h-11 rounded-xl grid place-items-center ${tone ?? 'bg-accent-soft text-accent'}`}>
        {icon}
      </div>
      <div>
        <div className="text-[12px] text-muted font-medium">{label}</div>
        <div className="text-[20px] font-bold tracking-tight">{value}</div>
      </div>
    </div>
  )
  return to ? <Link to={to}>{body}</Link> : body
}

const SEV: Record<string, string> = {
  critical: 'border-l-danger bg-[#fdeceb]/40',
  warning: 'border-l-warn bg-[#fdf3e7]/40',
  info: 'border-l-accent bg-accent-soft/40',
}

export default function Dashboard() {
  const qc = useQueryClient()
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [showFilter, setShowFilter] = useState(false)
  const { data } = useQuery({
    queryKey: ['dashboard', start, end],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (start && end) { params.start = start; params.end = end }
      return (await api.get<Dash>('/dashboard/', { params })).data
    },
  })
  const { data: notes } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => (await api.post<NotificationItem[]>('/notifications/refresh/')).data,
  })
  const dismiss = useMutation({
    mutationFn: (id: number) => api.post(`/notifications/${id}/dismiss/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const rangeActive = !!(start && end)

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Today at a glance — Sri Sakthi Medicals"
        actions={
          <div className="relative">
            <button
              onClick={() => setShowFilter((s) => !s)}
              className={`btn-ghost ${rangeActive ? '!border-accent !text-accent' : ''}`}
            >
              <Filter size={16} /> Filter sales{rangeActive ? ' · on' : ''}
            </button>
            {showFilter && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setShowFilter(false)} />
                <div className="absolute right-0 top-[44px] z-40 w-[300px] card shadow-xl p-4"
                  style={{ animation: 'pdpop .12s ease' }}>
                  <div className="text-[12.5px] font-bold mb-3">Sales between dates</div>
                  <label className="label">From</label>
                  <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="input !py-2 mb-2.5" />
                  <label className="label">To</label>
                  <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="input !py-2" />
                  {rangeActive && (
                    <div className="mt-3 p-2.5 rounded-lg bg-canvas">
                      <div className="text-[11px] text-muted">Total for range</div>
                      <div className="font-bold text-[18px]">{inr(data?.range_sales_total ?? 0)}</div>
                      <div className="text-[11.5px] text-muted">{data?.range_invoice_count ?? 0} bills</div>
                    </div>
                  )}
                  <div className="flex justify-between mt-3">
                    <button className="btn-ghost !py-1.5 !px-2.5" onClick={() => { setStart(''); setEnd('') }}>Clear</button>
                    <button className="btn-primary !py-1.5 !px-3" onClick={() => setShowFilter(false)}>Done</button>
                  </div>
                </div>
              </>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <StatCard icon={<IndianRupee size={20} />} label="Today's sales"
          value={inr(data?.today_sales_total ?? 0)} />
        <StatCard icon={<CalendarRange size={20} />} label="This week's sales"
          value={inr(data?.week_sales_total ?? 0)} />
        <StatCard icon={<IndianRupee size={20} />} label="This month's sales"
          value={inr(data?.month_sales_total ?? 0)} />
        <StatCard icon={<Wallet size={20} />} label="Credit outstanding"
          value={inr(data?.credit_outstanding ?? 0)}
          tone="bg-[#fdf3e7] text-warn" to="/customers" />
      </div>

      {/* Compact result banner when a range is applied (filter itself lives in the header popover) */}
      {rangeActive && (
        <div className="card px-4 py-2.5 mb-4 flex items-center gap-2 text-[13px]">
          <Filter size={14} className="text-accent" />
          <span className="text-muted">Sales {start} → {end}:</span>
          <b>{inr(data?.range_sales_total ?? 0)}</b>
          <span className="text-muted">· {data?.range_invoice_count ?? 0} bills</span>
          <button className="btn-ghost !py-1 !px-2.5 ml-auto" onClick={() => { setStart(''); setEnd('') }}>Clear</button>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard icon={<Boxes size={20} />} label="Medicines"
          value={String(data?.medicine_count ?? 0)} to="/inventory" />
        <StatCard icon={<AlertTriangle size={20} />} label="Low stock"
          value={String(data?.low_stock_count ?? 0)}
          tone="bg-[#fdf3e7] text-warn" to="/inventory" />
        <StatCard icon={<PackageX size={20} />} label="Out of stock"
          value={String(data?.out_of_stock_count ?? 0)}
          tone="bg-[#fdeceb] text-danger" to="/inventory" />
        <StatCard icon={<CalendarClock size={20} />} label="Near expiry"
          value={String(data?.near_expiry_count ?? 0)}
          tone="bg-[#fdeceb] text-danger" to="/reports" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-line">
              <h3 className="font-bold text-[15px]">Alerts &amp; reorder</h3>
              <span className="text-[12px] text-muted">{notes?.length ?? 0} active</span>
            </div>
            <div className="divide-y divide-line max-h-[460px] overflow-y-auto">
              {!notes?.length && <Empty>No alerts — stock levels are healthy.</Empty>}
              {notes?.map((n) => (
                <div key={n.id} className={`flex items-start gap-3 px-5 py-3 border-l-[3px] ${SEV[n.severity]}`}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[13.5px]">{n.title}</span>
                      <span className="text-[10px] uppercase tracking-wide font-bold text-faint">{n.kind_display}</span>
                    </div>
                    <p className="text-[12.5px] text-muted mt-0.5">{n.message}</p>
                  </div>
                  <button onClick={() => dismiss.mutate(n.id)} className="text-faint hover:text-ink flex-none">
                    <X size={15} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <StatCard icon={<CalendarClock size={20} />} label="Expired batches"
            value={String(data?.expired_count ?? 0)} tone="bg-[#fdeceb] text-danger" />
          <StatCard icon={<IndianRupee size={20} />} label="Today's bills"
            value={String(data?.today_invoice_count ?? 0)} />
          <div className="card p-4">
            <div className="text-[12px] text-muted font-medium mb-2">Quick actions</div>
            <div className="flex flex-col gap-2">
              <Link to="/billing" className="btn-primary justify-center">New bill (F2)</Link>
              <Link to="/purchase-orders" className="btn-ghost justify-center">Create purchase order</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
