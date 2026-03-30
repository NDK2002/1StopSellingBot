import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Search, Bot, Database, Sparkles, Loader2 } from 'lucide-react'

export const Route = createFileRoute('/rag')({
  component: RAGKnowledgePage,
})

function RAGKnowledgePage() {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<{
    answer: string
    chunks: Array<{ id: string; content: string; similarity: number }>
  } | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/rag/sandbox/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 3, generate_answer: true }),
      })
      const data = await res.json()
      setResult(data)
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">RAG Knowledge</h1>
        <p className="text-muted-foreground mt-1">
          Kiểm thử khả năng truy xuất và sinh câu trả lời của AI từ tài liệu nội bộ
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Left: Input & Answer */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="bg-muted/30">
              <CardTitle className="text-lg flex items-center gap-2">
                <Search className="w-5 h-5 text-primary" /> Nhập câu hỏi kiểm thử
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <form onSubmit={handleSearch} className="flex gap-2">
                <Input
                  value={query}
                  onChange={(e: any) => setQuery(e.target.value)}
                  placeholder="VD: Cửa hàng có chính sách đổi trả thế nào?"
                  className="flex-1"
                />
                <Button type="submit" disabled={isLoading || !query.trim()}>
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
                  Hỏi AI
                </Button>
              </form>
            </CardContent>
          </Card>

          {result && (
            <Card className="border-primary/20 shadow-md">
              <CardHeader className="bg-primary/5 pb-4">
                <CardTitle className="text-lg flex items-center gap-2 text-primary">
                  <Bot className="w-5 h-5" /> AI Trả lời
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                {result.answer ? (
                  <div className="prose prose-sm max-w-none prose-p:leading-relaxed text-foreground whitespace-pre-wrap">
                    {result.answer}
                  </div>
                ) : (
                  <p className="text-muted-foreground italic">Không tìm thấy câu trả lời phù hợp trong tài liệu.</p>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: Retrieved Context */}
        <div className="space-y-6">
          <Card className="h-full flex flex-col min-h-[400px]">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Database className="w-5 h-5 text-muted-foreground" />
                Dữ liệu truy xuất (Context)
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto space-y-4">
              {!result ? (
                <div className="h-40 flex items-center justify-center text-muted-foreground text-sm border-2 border-dashed rounded-lg">
                  Chưa có dữ liệu trích xuất
                </div>
              ) : result.chunks?.length === 0 ? (
                <div className="text-center text-sm text-red-500 py-8">Không tìm thấy tài liệu nào khớp!</div>
              ) : (
                result.chunks.map((chunk, idx) => (
                  <div key={chunk.id || idx} className="bg-muted/40 border rounded-lg p-4 text-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-[10px] px-2 py-1 rounded-bl-lg font-mono">
                      Khớp {((chunk.similarity || 0) * 100).toFixed(1)}%
                    </div>
                    <div className="text-muted-foreground mb-2 text-xs font-semibold">Đoạn #{idx + 1}</div>
                    <p className="leading-relaxed line-clamp-6 group-hover:line-clamp-none transition-all">{chunk.content}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
