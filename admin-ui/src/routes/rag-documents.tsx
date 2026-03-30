import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { useState } from 'react'
import { Plus, Loader2, Save, Trash2, Pencil, RefreshCcw, CheckCircle2, FileText, Database } from 'lucide-react'

export const Route = createFileRoute('/rag-documents')({
  component: RAGDocumentsPage,
})

interface RAGDocument {
  id: string
  title: string
  content: string | null
  doc_type: string
  file_path: string | null
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

type DocFormData = {
  title: string
  content: string
  doc_type: string
}

const emptyForm: DocFormData = { title: '', content: '', doc_type: 'text' }

function RAGDocumentsPage() {
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingDoc, setEditingDoc] = useState<RAGDocument | null>(null)
  const [form, setForm] = useState<DocFormData>(emptyForm)
  const [reindexingId, setReindexingId] = useState<string | null>(null)

  const { data: docs, isLoading } = useQuery<RAGDocument[]>({
    queryKey: ['rag-documents'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/rag/documents')
      if (!res.ok) throw new Error('Failed to fetch')
      return res.json()
    }
  })

  // Save (Create or Update)
  const saveMutation = useMutation({
    mutationFn: async (payload: { id?: string; data: any }) => {
      if (payload.id) {
        // Update
        const res = await fetch(`http://localhost:8000/api/rag/${payload.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: payload.data.title, content: payload.data.content }),
        })
        if (!res.ok) throw new Error('Cập nhật thất bại')
        return res.json()
      } else {
        // Create + auto-index
        const res = await fetch('http://localhost:8000/api/rag/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload.data),
        })
        if (!res.ok) throw new Error('Tạo mới thất bại')
        return res.json()
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] })
      closeDialog()
    }
  })

  // Delete
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`http://localhost:8000/api/rag/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Xoá thất bại')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] })
    }
  })

  // Re-index
  const reindexDoc = async (id: string) => {
    setReindexingId(id)
    try {
      const res = await fetch(`http://localhost:8000/api/rag/${id}/reindex`, { method: 'POST' })
      if (!res.ok) throw new Error('Re-embed thất bại')
      queryClient.invalidateQueries({ queryKey: ['rag-documents'] })
    } finally {
      setTimeout(() => setReindexingId(null), 1200)
    }
  }

  // Dialog handlers
  const openAdd = () => {
    setEditingDoc(null)
    setForm(emptyForm)
    setIsDialogOpen(true)
  }
  const openEdit = (doc: RAGDocument) => {
    setEditingDoc(doc)
    setForm({ title: doc.title, content: doc.content || '', doc_type: doc.doc_type })
    setIsDialogOpen(true)
  }
  const closeDialog = () => {
    setIsDialogOpen(false)
    setEditingDoc(null)
    setForm(emptyForm)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    saveMutation.mutate({
      id: editingDoc?.id,
      data: { title: form.title, content: form.content, doc_type: form.doc_type, metadata: {} }
    })
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setForm(prev => ({ ...prev, title: prev.title || file.name.replace(/\.[^/.]+$/, '') }))
    const reader = new FileReader()
    reader.onload = (ev) => setForm(prev => ({ ...prev, content: ev.target?.result as string }))
    reader.readAsText(file)
  }

  const updateField = (field: keyof DocFormData, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const formatDate = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">RAG Documents</h1>
          <p className="text-muted-foreground mt-1">Quản lý tài liệu nội bộ cho Chatbot (Knowledge Base)</p>
        </div>
        <Button onClick={openAdd}>
          <Plus className="mr-2 h-4 w-4" /> Thêm tài liệu
        </Button>
      </div>

      {/* === DIALOG === */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[640px]">
          <DialogHeader>
            <DialogTitle>{editingDoc ? `Sửa: ${editingDoc.title}` : 'Thêm tài liệu mới'}</DialogTitle>
            <DialogDescription>
              {editingDoc
                ? 'Chỉnh sửa nội dung. Sau khi lưu, bấm nút Re-embed để cập nhật vector.'
                : 'Tài liệu mới sẽ tự động chunk + embed ngay khi tạo.'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 pt-2">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Tiêu đề *</label>
                <Input value={form.title} onChange={(e: any) => updateField('title', e.target.value)} required placeholder="VD: Chính sách đổi trả 2026" />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Loại tài liệu</label>
                <select
                  className="w-full h-9 px-3 text-sm border bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  value={form.doc_type}
                  onChange={(e) => updateField('doc_type', e.target.value)}
                >
                  <option value="text">Text</option>
                  <option value="csv">CSV</option>
                  <option value="pdf">PDF</option>
                  <option value="docx">DOCX</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex justify-between items-center">
                Nội dung văn bản *
                <label className="cursor-pointer text-[10px] bg-muted hover:bg-muted/80 text-foreground px-2.5 py-1 rounded-md border transition-colors flex items-center normal-case font-normal">
                  <FileText className="w-3 h-3 mr-1" />
                  Import file (.txt, .md, .csv)
                  <input type="file" accept=".txt,.md,.csv" className="hidden" onChange={handleFileUpload} />
                </label>
              </label>
              <textarea
                className="w-full h-52 p-3 text-sm border bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring font-mono"
                placeholder="Dán nội dung tài liệu vào đây..."
                value={form.content}
                onChange={(e) => updateField('content', e.target.value)}
                required
              />
              <p className="text-[11px] text-muted-foreground">Hệ thống sẽ tự chia nhỏ (chunk) và nhúng vector (embed) để Chatbot tra cứu.</p>
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
                {editingDoc ? 'Cập nhật' : 'Tạo & Embed'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* === TABLE === */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" /> Danh sách tài liệu ({docs?.length || 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[280px]">Tiêu đề</TableHead>
                <TableHead className="w-[70px]">Loại</TableHead>
                <TableHead>Nội dung (preview)</TableHead>
                <TableHead className="w-[140px]">Ngày tạo</TableHead>
                <TableHead className="w-[140px]">Cập nhật</TableHead>
                <TableHead className="w-[150px] text-right">Thao tác</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" /> Đang tải...
                  </TableCell>
                </TableRow>
              ) : !docs?.length ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    Chưa có tài liệu nào. Bấm "Thêm tài liệu" để bắt đầu.
                  </TableCell>
                </TableRow>
              ) : (
                docs.map((doc) => (
                  <TableRow key={doc.id} className="group">
                    <TableCell className="font-medium">{doc.title}</TableCell>
                    <TableCell>
                      <span className="bg-secondary text-secondary-foreground px-2 py-0.5 text-[10px] rounded font-mono uppercase">{doc.doc_type}</span>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground max-w-[300px] truncate">
                      {doc.content ? doc.content.substring(0, 120) + (doc.content.length > 120 ? '…' : '') : <span className="italic">Không có nội dung</span>}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(doc.created_at)}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDate(doc.updated_at)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          title="Sửa"
                          onClick={() => openEdit(doc)}
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                          title="Re-embed (tái tạo vector)"
                          onClick={() => reindexDoc(doc.id)}
                          disabled={reindexingId === doc.id}
                        >
                          {reindexingId === doc.id ? <CheckCircle2 className="w-3.5 h-3.5 text-green-600 animate-pulse" /> : <RefreshCcw className="w-3.5 h-3.5" />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-red-500 hover:text-red-600 hover:bg-red-50"
                          title="Xoá"
                          onClick={() => {
                            if (confirm(`Xác nhận xoá "${doc.title}"?`)) {
                              deleteMutation.mutate(doc.id)
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
