# Sử dụng ảnh nền Python 3.11 chính thức
FROM python:3.11-slim

# Đặt thư mục làm việc trong container
WORKDIR /app

# Cài đặt các gói hệ thống và trình duyệt Google Chrome chính chủ
# Chúng ta sẽ sử dụng wget để tải trực tiếp file .deb của Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    # Dọn dẹp để giảm kích thước ảnh
    && apt-get purge -y --auto-remove wget \
    && rm -rf /var/lib/apt/lists/*

# Sao chép các file cần thiết vào container
COPY requirements.txt .
COPY speedup.js .
COPY automation.py .
COPY bot.py .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Đặt biến môi trường cho đường dẫn của Chrome (quan trọng)
ENV UC_DRIVER_EXE=/usr/bin/google-chrome-stable

# Lệnh để chạy bot khi container khởi động
CMD ["python", "bot.py"]
