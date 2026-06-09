import asyncio
import time
import httpx
import statistics

# Configuration
BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/api/chat"

TEST_CASES = [
    # RAG / Policy Info
    {"query": "Chính sách đổi trả hàng như thế nào?", "category": "RAG/Policy", "expected_keywords": ["7 ngày", "đổi trả"]},
    {"query": "Bảo hành giày dép bao lâu?", "category": "RAG/Policy", "expected_keywords": ["3 tháng", "bảo hành"]},
    {"query": "Phí vận chuyển đi tỉnh là bao nhiêu?", "category": "RAG/Policy", "expected_keywords": ["30.000", "vận chuyển"]},
    
    # Inventory
    {"query": "Còn áo thun nam basic không?", "category": "Inventory", "expected_keywords": ["còn", "AT001"]},
    {"query": "Mã BL001 còn hàng không?", "category": "Inventory", "expected_keywords": ["còn", "30"]},
    
    # Product Search
    {"query": "Bạn có bán quần jeans không?", "category": "Product", "expected_keywords": ["quần jeans", "QJ001"]},
    {"query": "Tìm cho tôi giày sneaker trắng", "category": "Product", "expected_keywords": ["sneaker", "GS001"]},
    
    # Order / Intent
    {"query": "Tôi muốn đặt mua 1 chiếc áo thun AT001", "category": "Order", "expected_keywords": ["đơn hàng", "xác nhận"]},
    
    # Escalation
    {"query": "Tôi muốn gặp nhân viên hỗ trợ ngay", "category": "Escalation", "expected_escalated": True},
    {"query": "Hệ thống bị lỗi rồi, chuyển tôi cho người thật", "category": "Escalation", "expected_escalated": True},
]

async def run_benchmark():
    print("🚀 Starting 1StopSellingBot Performance Benchmark...")
    print(f"Target: {CHAT_ENDPOINT}\n")

    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test in enumerate(TEST_CASES):
            print(f"[{i+1}/{len(TEST_CASES)}] Testing: '{test['query']}'...", end="", flush=True)
            
            start_time = time.perf_counter()
            try:
                response = await client.post(CHAT_ENDPOINT, json={"message": test["query"]})
                duration = time.perf_counter() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "")
                    escalated = data.get("escalated", False)
                    
                    # Validate
                    success = True
                    if "expected_keywords" in test:
                        if not any(k.lower() in reply.lower() for k in test["expected_keywords"]):
                            success = False
                    
                    if "expected_escalated" in test:
                        if escalated != test["expected_escalated"]:
                            success = False
                    
                    results.append({
                        "query": test["query"],
                        "category": test["category"],
                        "latency": duration,
                        "success": success,
                        "escalated": escalated,
                        "reply_len": len(reply)
                    })
                    print(f" Done ({duration:.2f}s) {'✅' if success else '❌'}")
                else:
                    print(f" Error (HTTP {response.status_code})")
            except Exception as e:
                print(f" Failed: {e}")
                
            # Small delay to avoid rate limiting or overlap if any
            await asyncio.sleep(0.5)

    if not results:
        print("No results collected. Make sure the server is running!")
        return

    # Summarize
    print("\n" + "="*50)
    print("📊 BENCHMARK SUMMARY")
    print("="*50)
    
    # Group by category
    categories = sorted(list(set(r["category"] for r in results)))
    
    total_latencies = [r["latency"] for r in results]
    
    print(f"{'Category':<15} | {'Count':<5} | {'Avg Lat':<10} | {'Success':<10}")
    print("-" * 50)
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        avg_lat = statistics.mean([r["latency"] for r in cat_results])
        success_rate = sum(1 for r in cat_results if r["success"]) / len(cat_results) * 100
        print(f"{cat:<15} | {len(cat_results):<5} | {avg_lat:7.2f}s | {success_rate:8.1f}%")
    
    print(f"\nOverall Avg Latency: {statistics.mean(total_latencies):.2f}s")
    print(f"Overall Success Rate: {sum(1 for r in results if r['success']) / len(results) * 100:.1f}%")
    print(f"Max Latency: {max(total_latencies):.2f}s")
    print(f"Min Latency: {min(total_latencies):.2f}s")
    print("="*50)
    
    print("\n💡 Tip for Slide 11:")
    print(f"- Use '{statistics.mean(total_latencies):.2f}s' for Average Response Time.")
    print(f"- Use '{sum(1 for r in results if r['success']) / len(results) * 100:.1f}%' for RAG/Agent Accuracy.")

if __name__ == "__main__":
    try:
        asyncio.run(run_benchmark())
    except KeyboardInterrupt:
        print("\nBenchmark cancelled.")
