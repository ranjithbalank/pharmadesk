import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  LayoutGrid, ReceiptText, Boxes, ShoppingCart, Truck, Users,
  BarChart3, Settings, Menu, Bell, X, Phone, Building2, ChevronRight, LogOut,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, clearToken, setShopName, getShopName } from '../lib/api'
import type { Dashboard, NotificationItem } from '../lib/types'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutGrid, end: true },
  { to: '/billing', label: 'Billing', icon: ReceiptText, kbd: 'F2' },
  { to: '/inventory', label: 'Inventory', icon: Boxes },
  { to: '/purchase-orders', label: 'Purchase Orders', icon: ShoppingCart },
  { to: '/suppliers', label: 'Suppliers', icon: Truck },
  { to: '/customers', label: 'Customers', icon: Users },
  { to: '/reports', label: 'Reports', icon: BarChart3 },
]

const TITLES: Record<string, string> = {
  '/': 'Dashboard', '/billing': 'Billing', '/inventory': 'Inventory',
  '/purchase-orders': 'Purchase Orders', '/suppliers': 'Suppliers',
  '/customers': 'Customers', '/reports': 'Reports', '/settings': 'Settings',
}

interface Shop {
  shop_name: string; gstin: string; phone: string; email: string
  drug_licence_no: string; address: string; logo: string | null
}

const SEV_DOT: Record<string, string> = {
  critical: 'bg-danger', warning: 'bg-warn', info: 'bg-accent',
}

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [openNotif, setOpenNotif] = useState(false)
  const [openProfile, setOpenProfile] = useState(false)
  const loc = useLocation()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<Dashboard>('/dashboard/')).data,
    refetchInterval: 20000,
  })
  // Real-time in-app alerts: recompute + refetch every 15s while the app is open.
  const { data: notes } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => (await api.post<NotificationItem[]>('/notifications/refresh/')).data,
    refetchInterval: 15000,
  })
  const { data: shop } = useQuery({
    queryKey: ['shop'],
    queryFn: async () => (await api.get<Shop>('/settings/')).data,
  })
  const dismiss = useMutation({
    mutationFn: (id: number) => api.post(`/notifications/${id}/dismiss/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  // Counter shortcut: F2 jumps to Billing from anywhere (F3 focuses search there).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'F2') { e.preventDefault(); navigate('/billing') }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [navigate])

  // Keep the browser tab in sync with the pharmacy's name (as "PharmaDesk —
  // <name>") so a rename in Settings shows up everywhere; PharmaDesk stays.
  useEffect(() => { if (shop?.shop_name) setShopName(shop.shop_name) }, [shop?.shop_name])

  const shopName = shop?.shop_name || getShopName() || 'PharmaDesk'
  const alertCount = notes?.length ?? data?.alert_count ?? 0
  const title = TITLES[loc.pathname] ?? shopName
  const initials = shopName
    .split(' ').slice(0, 2).map((w) => w[0]).join('').toUpperCase()

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar */}
      <aside
        className="flex-none flex flex-col bg-sidebar text-white transition-all duration-200"
        style={{ width: collapsed ? 64 : 248 }}
      >
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/[0.07]">
          <div className="flex-none w-9 h-9 rounded-lg bg-accent grid place-items-center font-bold text-[17px] shadow-lg shadow-accent/40 overflow-hidden">
            {shop?.logo ? <img src={shop.logo} alt="" className="w-full h-full object-contain" /> : '℞'}
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="font-bold text-[15px] tracking-tight whitespace-nowrap truncate">{shopName}</div>
              <div className="text-[11px] text-sidebar-muted font-mono whitespace-nowrap">GSTIN {shop?.gstin || '—'}</div>
            </div>
          )}
        </div>

        <nav className="flex-1 py-2.5 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon, kbd, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 mx-2 my-0.5 px-3 py-2.5 rounded-lg cursor-pointer text-[13.5px] transition ${
                  isActive
                    ? 'bg-accent text-white font-semibold'
                    : 'text-sidebar-muted hover:bg-sidebar-hover hover:text-white'
                }`
              }
            >
              <Icon size={18} className="flex-none" />
              {!collapsed && <span className="flex-1">{label}</span>}
              {!collapsed && to === '/' && alertCount > 0 && (
                <span className="text-[10px] font-bold bg-danger text-white rounded-full px-1.5 py-0.5 min-w-[18px] text-center">
                  {alertCount}
                </span>
              )}
              {!collapsed && kbd && (
                <kbd className="font-mono text-[10px] text-sidebar-muted border border-white/15 rounded px-1.5 py-px">
                  {kbd}
                </kbd>
              )}
            </NavLink>
          ))}
        </nav>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 mx-2 mb-2 px-3 py-2.5 rounded-lg cursor-pointer text-[13.5px] transition ${
              isActive ? 'bg-accent text-white font-semibold' : 'text-sidebar-muted hover:bg-sidebar-hover hover:text-white'
            }`
          }
        >
          <Settings size={18} className="flex-none" />
          {!collapsed && <span>Settings</span>}
        </NavLink>
      </aside>

      {/* Main */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="flex-none h-[60px] bg-white border-b border-line flex items-center gap-4 px-5">
          <button
            onClick={() => setCollapsed((c) => !c)}
            className="flex-none w-[34px] h-[34px] rounded-lg grid place-items-center text-muted border border-line hover:bg-[#f3f6fb]"
          >
            <Menu size={18} />
          </button>
          <h1 className="text-[17px] font-bold tracking-tight">{title}</h1>
          <div className="flex-1" />

          {/* Notification bell + dropdown */}
          <div className="relative">
            <button
              onClick={() => { setOpenNotif((o) => !o); setOpenProfile(false) }}
              className="relative w-[34px] h-[34px] rounded-lg grid place-items-center text-muted border border-line hover:bg-[#f3f6fb]"
            >
              <Bell size={18} />
              {alertCount > 0 && (
                <span className="absolute -top-1 -right-1 text-[9px] font-bold bg-danger text-white rounded-full px-1 min-w-[15px] text-center">
                  {alertCount}
                </span>
              )}
            </button>
            {openNotif && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setOpenNotif(false)} />
                <div className="absolute right-0 top-[42px] z-40 w-[360px] card shadow-xl" style={{ animation: 'pdpop .12s ease' }}>
                  <div className="flex items-center justify-between px-4 py-2.5 border-b border-line">
                    <span className="font-bold text-[13.5px]">Notifications</span>
                    <span className="text-[11px] text-muted">{alertCount} active</span>
                  </div>
                  <div className="max-h-[400px] overflow-y-auto divide-y divide-line">
                    {!notes?.length && (
                      <div className="px-4 py-8 text-center text-muted text-[13px]">
                        All clear — no alerts.
                      </div>
                    )}
                    {notes?.map((n) => (
                      <div key={n.id} className="flex items-start gap-2.5 px-4 py-2.5 hover:bg-canvas/60">
                        <span className={`mt-1.5 flex-none w-2 h-2 rounded-full ${SEV_DOT[n.severity] ?? 'bg-faint'}`} />
                        <button
                          className="flex-1 min-w-0 text-left"
                          onClick={() => { setOpenNotif(false); navigate('/inventory') }}
                        >
                          <div className="font-semibold text-[12.5px] truncate">{n.title}</div>
                          <div className="text-[11.5px] text-muted line-clamp-2">{n.message}</div>
                        </button>
                        <button onClick={() => dismiss.mutate(n.id)} className="text-faint hover:text-ink flex-none mt-0.5">
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => { setOpenNotif(false); navigate('/') }}
                    className="w-full text-center text-[12.5px] font-semibold text-accent py-2.5 border-t border-line hover:bg-canvas/60"
                  >
                    View all on dashboard
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Profile avatar + dropdown */}
          <div className="relative">
            <button
              onClick={() => { setOpenProfile((o) => !o); setOpenNotif(false) }}
              className="w-[34px] h-[34px] rounded-full bg-accent text-white grid place-items-center font-semibold text-[12px]"
            >
              {initials || 'PD'}
            </button>
            {openProfile && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setOpenProfile(false)} />
                <div className="absolute right-0 top-[42px] z-40 w-[280px] card shadow-xl" style={{ animation: 'pdpop .12s ease' }}>
                  <div className="px-4 py-3.5 border-b border-line flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-accent text-white grid place-items-center font-bold overflow-hidden">
                      {shop?.logo ? <img src={shop.logo} alt="" className="w-full h-full object-contain" /> : initials || 'PD'}
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-[13.5px] truncate">{shopName}</div>
                      <div className="text-[11px] text-muted font-mono truncate">GSTIN {shop?.gstin || '—'}</div>
                    </div>
                  </div>
                  <div className="px-4 py-3 space-y-1.5 text-[12.5px]">
                    <div className="flex items-center gap-2 text-muted">
                      <Phone size={13} /> {shop?.phone || 'No contact number'}
                    </div>
                    <div className="flex items-start gap-2 text-muted">
                      <Building2 size={13} className="mt-0.5 flex-none" />
                      <span className="line-clamp-2">{shop?.address || 'No address set'}</span>
                    </div>
                    {shop?.drug_licence_no && (
                      <div className="text-[11.5px] text-muted">DL No: {shop.drug_licence_no}</div>
                    )}
                  </div>
                  <button
                    onClick={() => { setOpenProfile(false); navigate('/settings') }}
                    className="w-full flex items-center justify-between px-4 py-2.5 border-t border-line text-[12.5px] font-semibold text-accent hover:bg-canvas/60"
                  >
                    Edit shop details <ChevronRight size={15} />
                  </button>
                  <button
                    onClick={async () => {
                      try { await api.post('/auth/logout/') } catch { /* ignore */ }
                      clearToken(); window.location.reload()
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 border-t border-line text-[12.5px] font-semibold text-danger hover:bg-[#fdeceb]/50"
                  >
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
