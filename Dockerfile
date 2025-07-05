# Sử dụng ảnh nền Python 3.11-slim, một bản Debian ổn định
FROM python:3.11-slim

# Đặt các biến môi trường để tránh các câu hỏi tương tác khi cài đặt
ENV DEBIAN_FRONTEND=noninteractive

# Cài đặt các gói cần thiết và Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    # Các thư viện mà Chrome cần để chạy
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 libx11-6 libx11-xcb1 \
    libxcb1 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdbus-1-3 libgtk-3-0 libpango-1.0-0 libcairo2 \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc
WORKDIR /app

# Sao chép các file cần thiết
COPY requirements.txt .
COPY speedup.js .
COPY automation.py .
COPY bot.py .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- LỆNH KHÁM NGHIỆM VÀ KHỞI ĐỘNG ---
# Chạy một shell script để kiểm tra trước khi khởi động bot.
CMD ["/bin/bash", "-c", "echo '--- BẮT ĐẦU KHÁM NGHIỆM HỆ THỐNG FILE ---' && \
    echo '1. Kiểm tra đường dẫn /usr/bin/google-chrome-stable:' && \
    ls -l /usr/bin/google-chrome-stable || echo '>>> KẾT QUẢ: File KHÔNG TỒN TẠI ở /usr/bin/google-chrome-stable' && \
    echo '2. Tìm kiếm file google-chrome-stable trên toàn bộ hệ thống:' && \
    find / -name 'google-chrome-stable' 2>/dev/null || echo '>>> KẾT QUẢ: File KHÔNG TÌM THẤY ở bất kỳ đâu' && \
    echo '--- KẾT THÚC KHÁM NGHIỆM ---' && \
    echo '--- BẮT ĐẦU CHẠY BOT ---' && \
    python bot.py"]
