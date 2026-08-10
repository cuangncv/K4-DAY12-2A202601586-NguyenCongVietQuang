# ═══════════════════════════════════════════════════════════════════
# CP2 — Containerization (bản production-ready)
#
# Build thử: docker build -t day12-chat:prod .
#            docker images day12-chat:prod     # xem dung lượng
# ═══════════════════════════════════════════════════════════════════

# ── Stage 1: builder ───────────────────────────────────────────────
# Cài thư viện vào một prefix riêng. Toàn bộ pip cache và mọi thứ
# cần để BUILD nằm lại ở stage này, không theo sang image cuối.
FROM python:3.11-slim AS builder

WORKDIR /app

# COPY requirements.txt TRƯỚC source code: Docker cache theo layer, nên
# sửa một dòng trong app/ không làm cài lại toàn bộ thư viện.
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ───────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Không ghi .pyc, không buffer stdout — log ra cloud ngay lập tức
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Chỉ mang sang kết quả đã cài, không mang compiler và pip cache
COPY --from=builder /install /usr/local

COPY . .

# Container chạy bằng root nghĩa là ai thoát được khỏi app cũng thành
# root. Tạo user thường và chuyển sang trước khi chạy app.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Base image slim không có curl, nên probe bằng chính Python đã có sẵn.
# Gọi /healthz — endpoint nhẹ, không đụng Redis.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c 'import os, urllib.request; urllib.request.urlopen("http://127.0.0.1:" + os.environ.get("PORT", "8000") + "/healthz")' || exit 1

# Dạng shell (sh -c) chứ không phải exec array, vì array không nở biến
# môi trường. Railway/Render/Cloud Run tự gán PORT, hardcode 8000 là
# platform gửi traffic vào cổng không ai nghe.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
