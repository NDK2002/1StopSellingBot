import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useQuery } from '@tanstack/react-query'
import { AlertCircle } from 'lucide-react'

export const Route = createFileRoute('/inventory')({
  component: InventoryPage,
})

interface Product {
  name: string
  category: string
}
interface InventoryItem {
  low_stock_threshold: number
  quantity: number
  sku: string
  products: Product
}

function InventoryPage() {
  const { data: inventory, isLoading } = useQuery<InventoryItem[]>({
    queryKey: ['inventory'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/inventory')
      if (!res.ok) throw new Error('Failed to fetch inventory')
      return res.json()
    }
  })

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Tồn kho</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Danh sách tồn kho</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mã Sản Phẩm</TableHead>
                <TableHead>Tên Sản Phẩm</TableHead>
                <TableHead className="text-right">Có sẵn</TableHead>
                <TableHead className="text-center">Trạng thái</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">Đang tải dữ liệu...</TableCell>
                </TableRow>
              ) : inventory?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">Chưa có dữ liệu</TableCell>
                </TableRow>
              ) : (
                inventory?.map((item) => (
                  <TableRow key={item.sku}>
                    <TableCell className="font-medium">{item.sku}</TableCell>
                    <TableCell>{item.products.name}</TableCell>
                    <TableCell className="text-right font-bold">{item.quantity}</TableCell>
                    <TableCell className="text-center">
                      {item.quantity <= item.low_stock_threshold ? 
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 align-center">
                          <AlertCircle className="w-3 h-3 mr-1" /> Sắp hết
                        </span> : 
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">Bình thường</span>
                      }
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
