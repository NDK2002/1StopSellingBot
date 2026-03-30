import { createRootRoute, Outlet, useNavigate, useLocation } from '@tanstack/react-router'
import { useAuth } from '@/store/auth'
import { BotMessageSquare, Package, MessagesSquare, Settings, LogOut, FileSearch, ChevronDown, Database, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useEffect, useState } from 'react'

export const Route = createRootRoute({
  component: RootLayout,
})

type MenuItem = {
  name: string
  path: string
  icon: any
  children?: { name: string; path: string; icon: any }[]
}

function RootLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const isLoginPage = location.pathname === '/login'
  const [ragOpen, setRagOpen] = useState(location.pathname.startsWith('/rag'))

  useEffect(() => {
    if (!user && !isLoginPage) {
      navigate({ to: '/login', replace: true })
    } else if (user && isLoginPage) {
      navigate({ to: '/', replace: true })
    }
  }, [user, isLoginPage, navigate])

  // Auto-expand RAG group when navigating to a child
  useEffect(() => {
    if (location.pathname.startsWith('/rag')) {
      setRagOpen(true)
    }
  }, [location.pathname])

  if (isLoginPage) {
    return <Outlet />
  }

  if (!user) return null

  const menus: MenuItem[] = [
    { name: 'Dashboard', path: '/', icon: BotMessageSquare },
    { name: 'Sản phẩm', path: '/products', icon: Package },
    { name: 'Tồn kho', path: '/inventory', icon: Package },
    { name: 'Takeover', path: '/conversations', icon: MessagesSquare },
    { name: 'Đơn hàng', path: '/orders', icon: Package },
    {
      name: 'RAG',
      path: '#rag',
      icon: FileSearch,
      children: [
        { name: 'Knowledge', path: '/rag', icon: BookOpen },
        { name: 'Documents', path: '/rag-documents', icon: Database },
      ],
    },
    { name: 'Nhân sự', path: '/staff', icon: Settings },
  ]

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname === path
  }

  return (
    <div className="min-h-screen bg-muted/40 font-sans text-foreground flex">
      {/* Sidebar */}
      <aside className="w-64 bg-card border-r border-border flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-border gap-2 font-bold text-lg text-primary">
          <BotMessageSquare /> 1StopSellingBot
        </div>
        <div className="flex-1 py-4 overflow-y-auto space-y-0.5 px-3">
          {menus.map((m) =>
            m.children ? (
              <div key={m.name}>
                <Button
                  variant={location.pathname.startsWith('/rag') ? 'secondary' : 'ghost'}
                  className="w-full justify-between text-sm"
                  onClick={() => setRagOpen(!ragOpen)}
                >
                  <span className="flex items-center">
                    <m.icon className="h-4 w-4 mr-2" />
                    {m.name}
                  </span>
                  <ChevronDown className={`h-3.5 w-3.5 transition-transform duration-200 ${ragOpen ? 'rotate-180' : ''}`} />
                </Button>
                {ragOpen && (
                  <div className="ml-4 mt-0.5 space-y-0.5 border-l-2 border-border/60 pl-2">
                    {m.children.map((child) => (
                      <Button
                        key={child.name}
                        variant={isActive(child.path) ? 'secondary' : 'ghost'}
                        className="w-full justify-start text-xs h-8"
                        onClick={() => navigate({ to: child.path })}
                      >
                        <child.icon className="h-3.5 w-3.5 mr-2" />
                        {child.name}
                      </Button>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <Button
                key={m.name}
                variant={isActive(m.path) ? 'secondary' : 'ghost'}
                className="w-full justify-start text-sm"
                onClick={() => navigate({ to: m.path })}
              >
                <m.icon className="h-4 w-4 mr-2" />
                {m.name}
              </Button>
            )
          )}
        </div>
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-10 w-10 bg-primary/10 text-primary rounded-full flex items-center justify-center font-bold">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-medium leading-none">{user.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user.role}</p>
            </div>
          </div>
          <Button variant="outline" className="w-full justify-start text-destructive hover:bg-destructive/10 hover:text-destructive" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" /> Đăng xuất
          </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-16 flex items-center px-8 border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10 w-full md:hidden">
          <div className="font-bold text-primary flex items-center gap-2">
            <BotMessageSquare /> 1StopSellingBot
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
