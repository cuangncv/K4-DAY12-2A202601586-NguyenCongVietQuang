# Phiếu Phản Ánh — K4 Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> 
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Nguyễn Công Việt Quang  Mã học viên: 2A202601586

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Em tạo service trên Railway trước khi set biến môi trường, service vẫn lên
Online và có domain công khai ngay. Nếu api_token mặc định là "changeme" thì lúc
đó em đã có một URL công khai chấp nhận token ai cũng đoán được, mà nhìn bên
ngoài mọi thứ vẫn bình thường, chỉ phát hiện khi hết ngân sách. Không có mặc
định thì /chat trả 500 cho tới khi em set API_TOKEN thật nên buộc phải làm.

Em quan sát thêm là app không chết lúc khởi động như đề nói, vì get_settings có
lru_cache nên chỉ chạy ở request đầu tiên.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

```json
{"event": "service_started", "severity": "INFO", "ts": "2026-08-10T16:03:06.949355+00:00", "service": "day12-chat-service", "version": "1.0.0"}
```

Một là tổng hợp theo trường: cộng usd_cost nhóm theo client_id để biết client
nào tốn nhất, hoặc lọc severity=ERROR. Hai là đặt cảnh báo tự động khi usd_cost
trong ngày vượt ngưỡng. Cả hai đều dựa vào việc từng giá trị là một trường riêng
biệt, còn print thì phải viết regex bóc tách lại.

Bằng chứng là Railway hiển thị dòng trên với event, ts, service, version tách
thành từng cột, còn log của uvicorn chỉ là một khối text.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | ~1.8 GB (theo ghi chú trong Dockerfile gốc của lab) |
| Multi-stage | 270 MB (em tự build và đo) |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Phần chênh đến từ hai nguồn. Một là base image: python:3.11 đầy đủ mang theo
gcc, build-essential, header thư viện và tài liệu, còn python:3.11-slim thì
không. Hai là rác của quá trình build: bản một stage giữ lại cache pip và file
tạm, còn bản multi-stage cài vào /install ở stage builder rồi chỉ copy kết quả
sang, vứt cả stage builder đi.

Những thứ bị cắt đều chỉ cần lúc build chứ không cần lúc chạy. Trình biên dịch
nằm trong image production còn là công cụ sẵn có cho kẻ tấn công nếu họ vào được
bên trong.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Dùng lại từ cache: FROM, WORKDIR, COPY requirements.txt, RUN pip install và
COPY --from=builder /install /usr/local. Phải chạy lại: COPY . . vì nội dung đã
đổi, rồi RUN useradd và chown, vì một layer đổi thì mọi layer sau nó mất cache.

Nếu để COPY . . trước pip install thì sửa một ký tự trong app/ là mất cache layer
COPY, kéo theo pip install chạy lại, tải và cài lại toàn bộ 30 gói. Em đo bước
đó mất 21,5 giây, nhân với vài chục lần build mỗi ngày.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Chuỗi sự kiện: lỗ hổng trong code hoặc thư viện cho phép chạy lệnh tùy ý; kẻ tấn
công chạy lệnh với quyền của tiến trình app, là root nếu không có USER; là root
trong container thì đọc được hết biến môi trường, ghi đè mọi file và cài thêm
công cụ; từ đó tìm đường ra host qua volume được mount, Docker socket, capability
thừa hoặc lỗ hổng runtime; thoát ra thì uid 0 trong container thành root trên host.

USER appuser cắt ở đoạn giữa, chỗ tiến trình đáng lẽ có quyền root. Chạy bằng
uid 1000 thì không cài được gói, không ghi ngoài /app, và mất gần hết đường thoát
container vì phần lớn kỹ thuật đó đòi root. Em kiểm chứng bằng whoami trong
container, kết quả là appuser.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

Header đó là chuẩn HTTP cho response 401, nó nói cho client biết cần xác thực
kiểu gì để thử lại. Thiếu nó thì client tự động chỉ biết bị từ chối mà không biết
phải gửi Bearer hay Basic. Em kiểm chứng trên bản deploy, gọi /chat không token
trả 401 kèm www-authenticate: Bearer.

Dùng chung một thông báo vì phân biệt ba trường hợp là cho kẻ dò biết họ đã đúng
tới đâu. Biết được scheme đúng, chỉ sai giá trị, thì không gian tìm kiếm hẹp đi
nhiều. Cùng tinh thần với secrets.compare_digest là không rò rỉ qua bất kỳ kênh
nào, kể cả nội dung lỗi lẫn thời gian phản hồi.

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

Có min thì gửi được 10 request. Im lặng 10 phút tích được 10 x 10 = 100 token
nhưng min(10, 100) cắt xuống đúng 10 là sức chứa xô, request thứ 11 bị 429.

Bỏ min thì gửi được khoảng 100 request, vì available trả về đúng số token đã
tích. Nghỉ một ngày thì thành 1440 x 10 = 14.400 token, dội hết trong vài giây,
đúng kiểu tải đột biến mà rate limit sinh ra để chặn. Bỏ min là capacity mất hết
tác dụng, chỉ còn tốc độ nạp.

Em đo thật trên bản deploy, gọi 15 lần liên tiếp cùng X-Client-Id thì được 200
chín lần rồi 429 sáu lần. Chín chứ không phải mười vì trước đó em đã gọi thử một
lần và tiêu mất một token.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

Hạn mức tháng: thiệt hại tối đa 30 USD, tức toàn bộ ngân sách. Sự cố lúc 2h sáng
không ai phát hiện, đốt tới khi chạm 30 USD mới bị chặn, và service đứng luôn cho
tới hết tháng vì chỉ reset khi sang tháng mới. Một đêm sự cố hỏng cả phần còn lại
của tháng.

Hạn mức ngày: thiệt hại tối đa 1 USD. Sang 00:00 UTC hôm sau, key
spend:client:ngày đổi tên nên spent đọc key chưa tồn tại và trả 0.0, service tự
chạy lại không cần ai can thiệp, chậm nhất khoảng 22 tiếng. Hạn mức tính theo
từng client_id nên client khác không bị ảnh hưởng.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Redis mất kết nối. Cả 3 container ping thất bại nên cùng lúc trả 503, vì chúng
cùng phụ thuộc một thứ. Load balancer rút cả 3 khỏi cụm, không còn instance nào
nhận traffic nên mọi request lỗi, kể cả request không cần Redis. Orchestrator đọc
cùng endpoint đó như liveness, kết luận cả 3 đã chết và restart cả 3. Việc restart
giết luôn các request đang xử lý dở. Đến giây thứ 30 Redis về nhưng 3 container
đang khởi động lại từ đầu nên vẫn chưa phục vụ được.

Sự cố gốc dài 30 giây nhưng downtime dài gấp đôi. Một trục trặc tạm thời ở
dependency bị khuếch đại thành sự cố nặng hơn của chính service.

Tách hai endpoint thì /healthz không gọi Redis nên vẫn 200, không container nào
bị restart, còn /readyz trả 503 để tạm ngừng traffic. Redis về là cụm nhận lại
ngay. Đó cũng là lý do healthz không nhận tham số dependency nào.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Lỗi: Railway báo Build failed ngay sau khi kết nối GitHub repo.

Cách tìm nguyên nhân: em mở tab Details của deployment rồi so khối Configuration
với railway.toml trong repo. Railway ghi Builder là Railpack trong khi file khai
dockerfile, và restart retries là 10 trong khi file khai 3. Cả hai đều lệch nên
kết luận Railway không đọc railway.toml mà tự đoán cách build, tức là không dùng
Dockerfile em viết ở CP2. Ngoài ra còn một chặn khác là workspace bị hạn chế vì
chưa gắn payment method.

Cách sửa: bỏ đường build từ repo, chuyển sang deploy từ image dựng sẵn. Em build
ở máy với --platform linux/amd64 --provenance=false, push lên
cuangncv/day12-chat:1.0.0, rồi tạo service Railway bằng Docker Image thay vì
GitHub Repository. Cách này bỏ qua khâu builder của Railway nên Railpack không
còn cơ hội đoán sai.

Kết quả: deployment ACTIVE, log ghi Uvicorn running on http://0.0.0.0:8080.
Railway gán PORT=8080 và app đọc đúng biến đó nhờ CMD dạng shell. Nếu cố định
cổng 8000 thì service vẫn Online nhưng không ai gọi được.
