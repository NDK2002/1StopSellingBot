import { createFileRoute } from '@tanstack/react-router'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { useQuery } from '@tanstack/react-query'
import { MessagesSquare, BotMessageSquare, User, Loader2, Send, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useState, useRef, useEffect } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export const Route = createFileRoute('/conversations')({
  component: ConversationsPage,
})

interface Escalation {
  id: string
  session_id: string
  status: string
  reason: string
  customer_summary: string
  skill_required: string
  created_at: string
}

interface Message {
  id: string
  role: 'user' | 'model'
  content: string
  created_at: string
}

interface Staff {
  id: string
  name: string
  is_available: boolean
  current_load: number
}

function ConversationsPage() {
  const [activeSession, setActiveSession] = useState<string | null>(null)
  const [replyText, setReplyText] = useState('')
  const [isSending, setIsSending] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.replace('#', '')
      if (hash) {
        setActiveSession(hash)
      } else {
        setActiveSession(null)
      }
    }

    window.addEventListener('hashchange', onHashChange)
    onHashChange() // handle initial load

    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const { data: escalations, isLoading: isEscalationsLoading, refetch: refetchEscalations } = useQuery<Escalation[]>({
    queryKey: ['escalations'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/escalations?limit=50')
      return res.json()
    }
  })

  const { data: staffList } = useQuery<Staff[]>({
    queryKey: ['staff'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/staff?available_only=true')
      return res.json()
    }
  })

  const { data: messages, isLoading: isMessagesLoading, refetch: refetchMessages } = useQuery<Message[]>({
    queryKey: ['messages', activeSession],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/api/escalations/${activeSession}/messages`)
      return res.json()
    },
    enabled: !!activeSession,
  })

  // WebSocket connection for real-time chat updates
  useEffect(() => {
    if (!activeSession) return

    // Connect to WebSocket using active session ID
    const ws = new WebSocket(`ws://localhost:8000/api/ws/${activeSession}`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'new_message') {
        refetchMessages()
      }
    }

    ws.onopen = () => {
      console.log('Live Takeover WS connected')
      // Send ping every 20s to keep alive
      const interval = setInterval(() => ws.send('ping'), 20000)
      ws.onclose = () => clearInterval(interval)
    }

    return () => {
      ws.close()
    }
  }, [activeSession, refetchMessages])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  const [isReassigning, setIsReassigning] = useState(false)

  const reassignEscalation = async (newStaffId: string) => {
    const esc = escalations?.find(e => e.session_id === activeSession)
    if (!esc || isReassigning) return
    setIsReassigning(true)
    try {
      await fetch(`http://localhost:8000/api/escalations/${esc.id}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_staff_id: newStaffId })
      })
      refetchEscalations()
    } finally {
      setIsReassigning(false)
    }
  }

  const sendReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!replyText.trim() || !activeSession) return
    setIsSending(true)

    try {
      await fetch(`http://localhost:8000/api/escalations/${activeSession}/takeover_message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: replyText })
      })
      setReplyText('')
      refetchMessages()
      refetchEscalations()
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="h-full flex flex-col md:flex-row gap-6 p-4 md:p-8 max-w-[1600px] mx-auto">
      {/* Sidebar: Danh sách phiên */}
      <Card className="w-full md:w-80 flex flex-col h-[50vh] md:h-[calc(100vh-8rem)]">
        <CardHeader className="py-4 border-b">
          <CardTitle className="text-lg flex items-center gap-2">
            <MessagesSquare className="w-5 h-5" /> Hộp thư chờ
            <span className="ml-auto text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded-full">
              {escalations?.filter(esc => esc.status !== 'resolved').length || 0}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 flex-1 overflow-y-auto">
          {isEscalationsLoading ? (
            <div className="p-4 text-center text-muted-foreground"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>
          ) : escalations?.filter(esc => esc.status !== 'resolved').length === 0 ? (
            <div className="p-4 text-center text-sm text-muted-foreground">Không có yêu cầu hỗ trợ nào</div>
          ) : (
            <div className="divide-y">
              {escalations?.filter(esc => esc.status !== 'resolved').map((esc) => (
                <button
                  key={esc.id}
                  onClick={() => {
                    setActiveSession(esc.session_id)
                    window.location.hash = esc.session_id
                  }}
                  className={`w-full text-left p-4 hover:bg-muted/50 transition-colors ${activeSession === esc.session_id ? 'bg-muted' : ''}`}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-medium text-sm truncate pr-2">Session: {esc.session_id.split('-')[0]}</span>
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                      {new Date(esc.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">{esc.customer_summary || esc.reason}</p>
                  <div className="mt-2 flex gap-1 items-center">
                    {esc.status === 'assigned' ? (
                      <span className="px-1.5 py-0.5 text-[10px] font-medium bg-purple-100 text-purple-700 rounded">Assigned</span>
                    ) : esc.status === 'in_progress' ? (
                      <span className="px-1.5 py-0.5 text-[10px] font-medium bg-blue-100 text-blue-700 rounded">In Progress</span>
                    ) : esc.status === 'resolved' ? (
                      <span className="px-1.5 py-0.5 text-[10px] font-medium bg-green-100 text-green-700 rounded">Resolved</span>
                    ) : (
                      <span className="px-1.5 py-0.5 text-[10px] font-medium bg-gray-100 text-gray-700 rounded capitalize text-nowrap">{esc.status.replace('_', ' ')}</span>
                    )}
                    {esc.skill_required && (
                      <span className="px-1.5 py-0.5 text-[10px] bg-secondary text-secondary-foreground rounded">
                        {esc.skill_required}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Chat Area */}
      <Card className="flex-1 flex flex-col h-[60vh] md:h-[calc(100vh-8rem)]">
        {!activeSession ? (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
            <MessagesSquare className="w-12 h-12 mb-4 opacity-20" />
            <p>Chọn một cuộc hội thoại để bắt đầu hỗ trợ</p>
          </div>
        ) : (
          <>
            <CardHeader className="py-4 border-b flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Trực tiếp hỗ trợ</CardTitle>
                <div className="text-xs text-green-600 flex items-center mt-1">
                  <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
                  Realtime connection active (Polling)
                </div>
              </div>
                <div className="flex items-center gap-2">
                  <DropdownMenu>
                    <DropdownMenuTrigger className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border border-input bg-background shadow-xs hover:bg-accent hover:text-accent-foreground h-8 px-3" disabled={isReassigning}>
                      <Users className="w-4 h-4" />
                      Chuyển người (Re-assign)
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {staffList?.map((staff) => (
                        <DropdownMenuItem
                          key={staff.id}
                          onClick={() => reassignEscalation(staff.id)}
                          className="cursor-pointer"
                        >
                          {staff.name} (Tải: {staff.current_load})
                        </DropdownMenuItem>
                      ))}
                    </DropdownMenuContent>
                  </DropdownMenu>

                  {escalations?.find(e => e.session_id === activeSession)?.status === 'in_progress' && (
                    <Button variant="outline" size="sm" onClick={async () => {
                      const esc = escalations?.find(e => e.session_id === activeSession)
                      if (!esc) return
                      await fetch(`http://localhost:8000/api/escalations/${esc.id}/resolve`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ staff_notes: 'Resolved via admin panel' })
                      })
                      refetchEscalations()
                    }}>Kết thúc (Resolve)</Button>
                  )}
                </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {isMessagesLoading ? (
                <div className="flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-primary opacity-50" /></div>
              ) : messages?.length === 0 ? (
                <div className="text-center text-muted-foreground text-sm">Chưa có tin nhắn nào</div>
              ) : (
                messages?.map((msg) => {
                  const isUser = msg.role === 'user'
                  const isStaff = msg.content.startsWith('[Hệ thống cập nhật thông tin')

                  return (
                    <div key={msg.id} className={`flex gap-3 ${isUser && !isStaff ? 'justify-end' : 'justify-start'}`}>
                      {(!isUser || isStaff) && (
                        <div className={`mt-1 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isStaff ? 'bg-blue-100 text-blue-600' : 'bg-primary/10 text-primary'}`}>
                          {isStaff ? <User className="w-4 h-4" /> : <BotMessageSquare className="w-4 h-4" />}
                        </div>
                      )}

                      <div className={`max-w-[75%] rounded-2xl px-4 py-2 ${isUser && !isStaff
                        ? 'bg-primary text-primary-foreground rounded-tr-sm'
                        : isStaff
                          ? 'bg-blue-600 text-white rounded-tl-sm'
                          : 'bg-muted rounded-tl-sm'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">
                          {isStaff ? msg.content.replace(/\[Hệ thống.*\]:\s*/, '') : msg.content}
                        </p>
                        <span className="text-[10px] opacity-70 mt-1 block">
                          {new Date(msg.created_at).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>

                      {isUser && !isStaff && (
                        <div className="mt-1 flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                          <User className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  )
                })
              )}
              <div ref={chatEndRef} />
            </CardContent>
            <div className="p-4 border-t bg-card">
              <form onSubmit={sendReply} className="flex gap-2">
                <Input
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Nhập tin nhắn..."
                  className="flex-1 focus-visible:ring-primary"
                  disabled={isSending}
                />
                <Button type="submit" disabled={!replyText.trim() || isSending}>
                  {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </Button>
              </form>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
