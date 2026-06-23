import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutGrid, ReceiptText, Boxes, ShoppingCart, Truck, Users,
  BarChart3, Settings, Menu, Bell,
} from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'
import type { Dashboard } from '../lib/types'

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

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const loc = useLocation()
  const { data } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get<Dashboard>('/dashboard/')).data,
    refetchInterval: 30000,
  })
  const alertCount = data?.alert_count ?? 0
  const title = TITLES[loc.pathname] ?? 'PharmaDesk'

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Sidebar */}
      <aside
        className="flex-none flex flex-col bg-sidebar text-white transition-all duration-200"
        style={{ width: collapsed ? 64 : 248 }}
      >
        <div className="flex items-center gap-3 px-4 py-4 border-b border-white/[0.07]">
          <div className="flex-none w-9 h-9 rounded-lg bg-accent grid place-items-center font-bold text-[17px] shadow-lg shadow-accent/40">
            ℞
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="font-bold text-[15px] tracking-tight whitespace-nowrap">Sri Sakthi Medicals</div>
              <div className="text-[11px] text-sidebar-muted font-mono whitespace-nowrap">GSTIN 33ABCFS1234K1Z9</div>
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
          <NavLink
            to="/"
            className="relative w-[34px] h-[34px] rounded-lg grid place-items-center text-muted border border-line hover:bg-[#f3f6fb]"
          >
            <Bell size={18} />
            {alertCount > 0 && (
              <span className="absolute -top-1 -right-1 text-[9px] font-bold bg-danger text-white rounded-full px-1 min-w-[15px] text-center">
                {alertCount}
              </span>
            )}
          </NavLink>
          <div className="w-[34px] h-[34px] rounded-full bg-accent text-white grid place-items-center font-semibold text-[13px]">
            SK
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
