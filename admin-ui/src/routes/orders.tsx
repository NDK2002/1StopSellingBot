import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useQuery } from '@tanstack/react-query'

export const Route = createFileRoute('/orders')({
  component: OrdersPage,
})

interface Order {
  id: string
  user_phone: string
  user_name: string
  status: string
  total_amount: number
  created_at: string
}

function OrdersPage() {
  const { data: orders, isLoading } = useQuery<Order[]>({
    queryKey: ['orders'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/orders')
      if (!res.ok) throw new Error('Failed to fetch orders')
      return res.json()
    }
  })

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Đơn hàng</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Danh sách đơn đặt hàng từ Chatbot</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mã Đơn</TableHead>
                <TableHead>Khách hàng</TableHead>
                <TableHead>SĐT</TableHead>
                <TableHead className="text-right">Tổng tiền</TableHead>
                <TableHead>Trạng thái</TableHead>
                <TableHead>Ngày đặt</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">Đang tải dữ liệu...</TableCell>
                </TableRow>
              ) : orders?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">Chưa có đơn hàng nào</TableCell>
                </TableRow>
              ) : (
                orders?.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell className="font-medium text-primary">#{order.id.split('-').pop()?.slice(0, 6).toUpperCase()}</TableCell>
                    <TableCell>{order.user_name || 'Khách vãng lai'}</TableCell>
                    <TableCell>{order.user_phone}</TableCell>
                    <TableCell className="text-right font-medium">{order.total_amount?.toLocaleString('vi-VN')} đ</TableCell>
                    <TableCell>
                      {order.status === 'pending' && <span className="text-yellow-600 bg-yellow-100 px-2 py-1 rounded-full text-xs font-bold">Chờ xử lý</span>}
                      {order.status === 'confirmed' && <span className="text-blue-600 bg-blue-100 px-2 py-1 rounded-full text-xs font-bold">Đã xác nhận</span>}
                      {order.status === 'completed' && <span className="text-green-600 bg-green-100 px-2 py-1 rounded-full text-xs font-bold">Hoàn thành</span>}
                      {order.status === 'cancelled' && <span className="text-red-600 bg-red-100 px-2 py-1 rounded-full text-xs font-bold">Đã huỷ</span>}
                    </TableCell>
                    <TableCell>{new Date(order.created_at).toLocaleDateString('vi-VN')}</TableCell>
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
