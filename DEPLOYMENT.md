# Thông Tin Deploy — Checkpoint 5

> `pytest tests/test_cp5.py` đọc file này để tìm địa chỉ service và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị token vào đây.**
> Repo này công khai — dán token vào là mất token.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Nguyễn Công Việt Quang |
| Mã học viên | 2A202601586 |
| Repo | https://github.com/cuangncv/K4-DAY12-2A202601586-NguyenCongVietQuang |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://day12-chat-production-c064.up.railway.app |
| Platform | Railway (deploy từ Docker image, không dùng builder tự động) |
| Ngày deploy | 10/08/2026 |

Kiến trúc trên cloud: hai service trong cùng một project.

```
project "happy-simplicity"
├── day12-chat   ← image cuangncv/day12-chat:1.0.0, đọc $PORT do Railway gán
└── Redis        ← nối vào nhau qua biến tham chiếu REDIS_URL
```

Image được build ở máy từ `Dockerfile` của CP2 rồi đẩy lên Docker Hub:
`cuangncv/day12-chat:1.0.0` (270MB, multi-stage, chạy bằng user `appuser`).

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | Railway tự gán (thực tế là 8080), app đọc từ biến |
| `API_TOKEN` | ✅ | đặt trong dashboard Railway, không nằm trong repo |
| `REDIS_URL` | ✅ | biến tham chiếu tới service Redis cùng project |
| `BUCKET_CAPACITY` | ✅ | 10 |
| `REFILL_PER_MINUTE` | ✅ | 10 |
| `DAILY_BUDGET_USD` | ✅ | 1.0 |
| `LOG_LEVEL` | ✅ | INFO |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i <URL>/healthz

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i <URL>/readyz

# 3. Không có token — mong đợi 401 kèm header WWW-Authenticate
curl -i -X POST <URL>/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'

# 4. Có token — mong đợi 200 kèm câu trả lời
curl -i -X POST <URL>/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "X-Client-Id: sv-test" \
  -d '{"message":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "X-Client-Id: sv-test" \
    -d '{"message":"test"}'
done; echo
```

## Kết Quả Chạy Thật

Chạy lúc 23:20 ngày 10/08/2026 (GMT+7):

```
=== 1. healthz ===
HTTP/1.1 200 OK
{"status":"ok","service":"day12-chat-service","version":"1.0.0"}

=== 2. readyz ===
HTTP/1.1 200 OK
{"status":"ready","redis":true}

=== 3. chat khong token ===
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer

=== 4. chat co token ===
{"reply":"Ngắn gọn: Deploy la gi phụ thuộc vào ba yếu tố — cấu hình qua biến môi
trường, health check để orchestrator biết trạng thái, và giới hạn tài nguyên.",
 "client_id":"sv-test","turns_before":0,"usd_cost":2.265e-05,
 "usage":{"prompt":3,"completion":37}}

=== 5. rate limit: goi 15 lan ===
200 200 200 200 200 200 200 200 200 429 429 429 429 429 429
```

Ghi chú về kết quả số 5: xô token có sức chứa 10, nhưng lần gọi ở bước 4 đã tiêu
mất 1 token của cùng `X-Client-Id: sv-test`, nên chỉ còn 9 lần đi qua trước khi
xô cạn và trả 429.

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — canvas Railway với hai service `day12-chat` và `Redis`
- `screenshots/healthz.png` — kết quả gọi `/healthz` từ trình duyệt
