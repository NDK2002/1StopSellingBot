import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, Loader2, Save, Trash2, Pencil, X, Check, Shield, User, RefreshCcw } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { useState } from 'react'

export const Route = createFileRoute('/staff')({
  component: StaffPage,
})

interface Staff {
  id: string
  name: string
  email: string
  role: string
  skills: string[]
  is_available: boolean
  telegram_chat_id: string
  max_concurrent: number
  current_load: number
  created_at: string
  updated_at: string
}

type StaffFormData = {
  name: string
  email: string
  role: string
  skills: string[]
  is_available: boolean
  telegram_chat_id: string
  max_concurrent: number
  password?: string
}

const emptyForm: StaffFormData = {
  name: '',
  email: '',
  role: 'staff',
  skills: [],
  is_available: true,
  telegram_chat_id: '',
  max_concurrent: 3,
  password: '',
}

const STAFF_SKILL_OPTIONS = [
  'order_support',
  'inventory_support',
  'technical_support',
  'product_support',
  'general_support',
]

function StaffPage() {
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null)
  const [form, setForm] = useState<StaffFormData>(emptyForm)

  const { data: staffList, isLoading } = useQuery<Staff[]>({
    queryKey: ['staff'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/staff')
      if (!res.ok) throw new Error('Failed to fetch staff')
      return res.json()
    }
  })

  // --- Mutations ---
  const saveMutation = useMutation({
    mutationFn: async (payload: { id?: string; data: Record<string, any> }) => {
      const url = payload.id
        ? `http://localhost:8000/api/staff/${payload.id}`
        : 'http://localhost:8000/api/staff'
      const method = payload.id ? 'PUT' : 'POST'
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload.data)
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Thao tác thất bại')
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff'] })
      closeDialog()
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`http://localhost:8000/api/staff/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Xoá thất bại')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff'] })
    }
  })

  // --- Handlers ---
  const openAddDialog = () => {
    setEditingStaff(null)
    setForm(emptyForm)
    setIsDialogOpen(true)
  }

  const openEditDialog = (staff: Staff) => {
    setEditingStaff(staff)
    setForm({
      name: staff.name,
      email: staff.email,
      role: staff.role || 'staff',
      skills: staff.skills || [],
      is_available: staff.is_available,
      telegram_chat_id: staff.telegram_chat_id || '',
      max_concurrent: staff.max_concurrent ?? 3,
      password: '',
    })
    setIsDialogOpen(true)
  }

  const closeDialog = () => {
    setIsDialogOpen(false)
    setEditingStaff(null)
    setForm(emptyForm)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data: Record<string, any> = {
      name: form.name,
      email: form.email,
      role: form.role,
      skills: form.skills,
      is_available: form.is_available,
      telegram_chat_id: form.telegram_chat_id,
      max_concurrent: form.max_concurrent,
    }
    // Only send password if user typed one (for create or password change)
    if (form.password && form.password.length > 0) {
      data.password = form.password
    }
    saveMutation.mutate({ id: editingStaff?.id, data })
  }

  const updateField = (field: keyof StaffFormData, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const toggleSkill = (skill: string) => {
    setForm(prev => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter((item) => item !== skill)
        : [...prev.skills, skill],
    }))
  }

  // --- Render ---
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Nhân sự (Staff)</h1>
          <p className="text-muted-foreground mt-1">Quản lý tài khoản nhân viên hỗ trợ & Admin</p>
        </div>
        <Button onClick={openAddDialog}>
          <Plus className="mr-2 h-4 w-4" /> Thêm nhân sự
        </Button>
      </div>

      {/* === ADD / EDIT DIALOG === */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[520px]">
          <DialogHeader>
            <DialogTitle>{editingStaff ? `Sửa: ${editingStaff.name}` : 'Thêm nhân sự mới'}</DialogTitle>
            <DialogDescription>
              {editingStaff
                ? 'Chỉnh sửa thông tin nhân viên. Để trống mật khẩu nếu không muốn đổi.'
                : 'Tạo tài khoản mới cho nhân viên hỗ trợ hoặc quản trị viên.'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 pt-2">
            {/* Row 1: Name + Role */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Họ Tên *</label>
                <Input
                  value={form.name}
                  onChange={(e: any) => updateField('name', e.target.value)}
                  required
                  placeholder="Nguyễn Văn A"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Chức vụ *</label>
                <select
                  className="w-full h-9 px-3 text-sm border bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  value={form.role}
                  onChange={(e) => updateField('role', e.target.value)}
                >
                  <option value="staff">Staff (Nhân viên)</option>
                  <option value="admin">Admin (Quản trị)</option>
                </select>
              </div>
            </div>

            {/* Row 2: Email + Password */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Email (Đăng nhập) *</label>
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e: any) => updateField('email', e.target.value)}
                  required
                  placeholder="nva@company.com"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {editingStaff ? 'Đổi mật khẩu' : 'Mật khẩu *'}
                </label>
                <Input
                  type="password"
                  value={form.password || ''}
                  onChange={(e: any) => updateField('password', e.target.value)}
                  required={!editingStaff}
                  placeholder={editingStaff ? '(để trống = giữ nguyên)' : 'Nhập mật khẩu'}
                />
              </div>
            </div>

            {/* Row 3: Telegram + Max Concurrent */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Telegram Chat ID</label>
                <Input
                  value={form.telegram_chat_id}
                  onChange={(e: any) => updateField('telegram_chat_id', e.target.value)}
                  placeholder="123456789"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Max Concurrent (đồng thời)</label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={form.max_concurrent}
                  onChange={(e: any) => updateField('max_concurrent', parseInt(e.target.value) || 3)}
                />
              </div>
            </div>

            {/* Row 4: Skills */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Kỹ năng xử lý (Skills)</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 rounded-md border bg-background p-3">
                {STAFF_SKILL_OPTIONS.map((skill) => (
                  <label
                    key={skill}
                    className="flex items-center gap-2 text-sm font-mono cursor-pointer rounded-sm px-2 py-1.5 hover:bg-muted"
                  >
                    <input
                      type="checkbox"
                      className="h-4 w-4 accent-primary"
                      checked={form.skills.includes(skill)}
                      onChange={() => toggleSkill(skill)}
                    />
                    <span>{skill}</span>
                  </label>
                ))}
              </div>
              <p className="text-[11px] text-muted-foreground">Chọn một hoặc nhiều kỹ năng để routing escalation phù hợp.</p>
            </div>

            {/* Row 5: Availability */}
            <div className="flex items-center gap-3 pt-1">
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={form.is_available}
                  onChange={(e) => updateField('is_available', e.target.checked)}
                />
                <div className="w-9 h-5 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:bg-primary transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4"></div>
              </label>
              <span className="text-sm font-medium">Đang trực (nhận được phân công)</span>
            </div>

            {saveMutation.isError && (
              <div className="bg-red-50 text-red-600 text-sm p-3 rounded-md border border-red-200">
                ⚠️ {(saveMutation.error as Error).message}
              </div>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeDialog}>Huỷ</Button>
              <Button type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                {editingStaff ? 'Cập nhật' : 'Tạo mới'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* === TABLE === */}
      <Card>
        <CardHeader>
          <CardTitle>Danh sách nhân viên ({staffList?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">Tên</TableHead>
                <TableHead>Email</TableHead>
                <TableHead className="w-[80px]">Role</TableHead>
                <TableHead className="w-[90px]">Trạng thái</TableHead>
                <TableHead>Skills</TableHead>
                <TableHead className="w-[90px]">Telegram</TableHead>
                <TableHead className="w-[60px] text-center">Max</TableHead>
                <TableHead className="w-[60px] text-center">Load</TableHead>
                <TableHead className="w-[100px] text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-12 text-muted-foreground">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" /> Đang tải...
                  </TableCell>
                </TableRow>
              ) : !staffList?.length ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-12 text-muted-foreground">
                    Chưa có dữ liệu nhân sự. Bấm "Thêm nhân sự" để bắt đầu.
                  </TableCell>
                </TableRow>
              ) : (
                staffList.map((staff) => (
                  <TableRow key={staff.id} className="group">
                    <TableCell className="font-medium">{staff.name}</TableCell>
                    <TableCell className="text-muted-foreground text-xs">{staff.email}</TableCell>
                    <TableCell>
                      {staff.role === 'admin' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-primary/10 text-primary border border-primary/20">
                          <Shield className="w-3 h-3" /> Admin
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-secondary text-secondary-foreground">
                          <User className="w-3 h-3" /> Staff
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {staff.is_available ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-green-100 text-green-700">
                          <Check className="w-3 h-3" /> Online
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-gray-100 text-gray-500">
                          <X className="w-3 h-3" /> Offline
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1 flex-wrap">
                        {(staff.skills || []).map((s, i) => (
                          <span key={i} className="bg-muted text-muted-foreground px-1.5 py-0.5 text-[10px] rounded font-mono">{s}</span>
                        ))}
                        {(!staff.skills || staff.skills.length === 0) && (
                          <span className="text-muted-foreground text-[10px] italic">chưa cấu hình</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground font-mono">
                      {staff.telegram_chat_id || <span className="italic text-[10px]">N/A</span>}
                    </TableCell>
                    <TableCell className="text-center font-mono text-sm">{staff.max_concurrent ?? '-'}</TableCell>
                    <TableCell className="text-center font-mono text-sm">
                      <span className={staff.current_load > 0 ? 'text-orange-600 font-bold' : ''}>{staff.current_load ?? 0}</span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => openEditDialog(staff)}
                          title="Sửa"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-blue-500 hover:text-blue-600 hover:bg-blue-50"
                          onClick={() => {
                            if (confirm(`Xác nhận reset load cho "${staff.name}" về 0?`)) {
                              saveMutation.mutate({ id: staff.id, data: { current_load: 0 } })
                            }
                          }}
                          title="Reset Load"
                        >
                          <RefreshCcw className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-red-500 hover:text-red-600 hover:bg-red-50"
                          title="Xoá"
                          onClick={() => {
                            if (confirm(`Xác nhận xoá "${staff.name}"?`)) {
                              deleteMutation.mutate(staff.id)
                            }
                          }}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
