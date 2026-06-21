import { NavLink, Outlet } from 'react-router-dom'
import { clsx } from 'clsx'
import { Dna, Upload, Briefcase, BarChart3, Info } from 'lucide-react'

const nav = [
  { to: '/', label: 'Home', icon: Dna, end: true },
  { to: '/upload', label: 'New Job', icon: Upload },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/about', label: 'About', icon: Info },
]

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-brand-900 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Dna className="w-7 h-7 text-blue-300" />
            <div>
              <span className="text-xl font-bold tracking-tight">TDPortal</span>
              <span className="text-blue-300 text-xs ml-1">-OS</span>
            </div>
            <span className="text-blue-400 text-xs hidden sm:inline ml-2 border-l border-blue-700 pl-2">
              Open-Source Top-Down Proteomics
            </span>
          </div>
          <nav className="flex items-center gap-1">
            {nav.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-700 text-white'
                      : 'text-blue-200 hover:bg-blue-800 hover:text-white'
                  )
                }
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{label}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      <footer className="bg-white border-t border-gray-200 py-4">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-gray-400">
          TDPortal-OS is an independent open-source project. Not affiliated with official TDPortal or ProSight.
          Real search results require installed engine binaries. Demo mode produces synthetic data only.
        </div>
      </footer>
    </div>
  )
}
