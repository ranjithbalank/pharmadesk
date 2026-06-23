import type { ReactNode } from 'react'

export function PageHeader({ title, subtitle, actions }: {
  title: string; subtitle?: string; actions?: ReactNode
}) {
  return (
    <div className="flex items-end justify-between mb-5 gap-4 flex-wrap">
      <div>
        <h2 className="text-[20px] font-bold tracking-tight">{title}</h2>
        {subtitle && <p className="text-[13px] text-muted mt-0.5">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

const STATUS_STYLES: Record<string, string> = {
  in_stock: 'bg-[#eaf6ee] text-ok',
  low_stock: 'bg-[#fdf3e7] text-warn',
  out_of_stock: 'bg-[#fdeceb] text-danger',
  paid: 'bg-[#eaf6ee] text-ok',
  credit: 'bg-[#fdf3e7] text-warn',
  returned: 'bg-[#fdeceb] text-danger',
}
const STATUS_LABELS: Record<string, string> = {
  in_stock: 'In stock', low_stock: 'Low stock', out_of_stock: 'Out of stock',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-block text-[11px] font-semibold rounded-md px-2 py-0.5 ${STATUS_STYLES[status] ?? 'bg-canvas text-muted'}`}>
      {STATUS_LABELS[status] ?? status}
    </span>
  )
}

export function ScheduleBadge({ schedule }: { schedule: string }) {
  if (schedule === 'OTC')
    return <span className="text-[11px] text-faint font-medium">OTC</span>
  const tone = schedule === 'X' ? 'bg-[#fdeceb] text-danger' : 'bg-accent-soft text-accent'
  return <span className={`text-[11px] font-bold rounded px-1.5 py-0.5 ${tone}`}>Sch {schedule}</span>
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="text-center text-muted text-sm py-12">{children}</div>
}

export function Modal({ title, onClose, children, wide }: {
  title: string; onClose: () => void; children: ReactNode; wide?: boolean
}) {
  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-start justify-center p-6 overflow-y-auto" onClick={onClose}>
      <div
        className={`card shadow-xl w-full ${wide ? 'max-w-3xl' : 'max-w-lg'} mt-10`}
        onClick={(e) => e.stopPropagation()}
        style={{ animation: 'pdpop .12s ease' }}
      >
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-line">
          <h3 className="font-bold text-[15px]">{title}</h3>
          <button onClick={onClose} className="text-faint hover:text-ink text-xl leading-none">×</button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}
