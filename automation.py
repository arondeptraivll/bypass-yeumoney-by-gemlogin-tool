import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
from urllib.parse import urlparse

# ================= CẤU HÌNH =================
KEYWORD_MAP = {
    "m88": {"name": "m88", "url": "bet88ec.com"},
    "w88": {"name": "w88", "url": "188.166.185.213"},
    "188bet": {"name": "188bet", "url": "88betag.com"},
    "bk8": {"name": "bk8", "url": "bk8ze.com"},
    "vn8": {"name": "vn8", "url": "vn88no.com"},
    "fb88": {"name": "fb88", "url": "fb88mg.com"},
    "v9bet": {"name": "v9bet", "url": "v9betde.com"}
}
JS_FILE = "speedup.js"
UNWANTED_LINKS = ["#", "javascript:", "logout", "signout", "tel:", "mailto:"]
BUTTON_XPATH = "//*[@id='layma_me_vuatraffic']"

# ================= TIỆN ÍCH (đã được sửa đổi một chút) =================
def is_valid_link(href, domain):
    if not href:
        return False
    if any(unwanted in href.lower() for unwanted in UNWANTED_LINKS):
        return False
    parsed = urlparse(href)
    return ((not parsed.netloc or parsed.netloc == domain) and
            not href.startswith(('javascript:', 'mailto:', 'tel:')))

def get_internal_links(driver):
    try:
        current_url = driver.current_url
        domain = urlparse(current_url).netloc
        all_links = driver.find_elements(By.XPATH, "//a[@href]")
        valid_links = []
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if is_valid_link(href, domain) and link.is_displayed() and link.is_enabled():
                    valid_links.append(link)
            except:
                continue
        return valid_links
    except Exception as e:
        print(f"❌ Lỗi khi lấy link: {str(e)}")
        return []

def inject_js(driver):
    try:
        if not os.path.exists(JS_FILE):
            print(f"⚠️ File {JS_FILE} không tồn tại")
            return False
        with open(JS_FILE, 'r') as f:
            js_code = f.read()
            driver.execute_script(js_code)
            return True
    except Exception as e:
        print(f"❌ Lỗi inject JS: {str(e)}")
        return False

def click_with_js_injection(driver, step_name):
    print(f"💉 Đang inject JS cho {step_name}...")
    inject_js(driver)
    
    print(f"🖱️ Đang click {step_name}...")
    try:
        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, BUTTON_XPATH)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", button)
        print(f"✅ {step_name} thành công")
        return True
    except Exception as e:
        print(f"❌ Lỗi {step_name}: {str(e)}")
        return False

# ================= HÀM CHÍNH ĐỂ BOT GỌI =================
def run_automation_task(keyword):
    """
    Hàm chính thực hiện tác vụ tự động hóa.
    Args:
        keyword (str): Từ khóa người dùng chọn (ví dụ: 'm88').
    Returns:
        dict: Một dictionary chứa status và message/data.
              {'status': 'success', 'data': 'MÃ_LẤY_ĐƯỢC'}
              {'status': 'error', 'message': 'Lý do lỗi'}
    """
    if keyword not in KEYWORD_MAP:
        return {"status": "error", "message": f"Từ khóa không hợp lệ: {keyword}"}

    target = KEYWORD_MAP[keyword]
    print(f"\n🔍 Bắt đầu xử lý cho: {target['name']} ({target['url']})")

    driver = None
    try:
        # Khởi tạo trình duyệt
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--start-maximized")
        options.add_argument("--headless=new") # Chạy ở chế độ không giao diện trên server
        driver = uc.Chrome(options=options)
        
        # 1. Truy cập qua Google
        print("🌐 Đang truy cập Google...")
        driver.get("https://www.google.com")
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'q'))
        )
        search_box.send_keys(f"site:{target['url']}")
        search_box.submit()
        time.sleep(2)

        # 2. Click kết quả đầu tiên
        print("🔗 Đang chọn kết quả tìm kiếm...")
        first_result = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@id='search']//a"))
        )
        first_result.click()
        time.sleep(3)

        # 3. Xử lý LẦN 1
        if not click_with_js_injection(driver, "nút lần 1"):
            raise Exception("Thất bại ở bước 1: Click nút lần 1")
        time.sleep(3)

        # 4. Vào link nội bộ
        print("🎲 Đang tìm link nội bộ...")
        internal_links = get_internal_links(driver)
        if not internal_links:
            raise Exception("Không tìm thấy link nội bộ hợp lệ")
        
        chosen_link = random.choice(internal_links)
        print(f"👉 Chọn link: {chosen_link.get_attribute('href')}")
        driver.execute_script("arguments[0].click();", chosen_link)
        time.sleep(3)

        # 5. Xử lý LẦN 2
        if not click_with_js_injection(driver, "nút lần 2"):
            raise Exception("Thất bại ở bước 2: Click nút lần 2")
        time.sleep(4)

        # 6. Lấy mã cuối cùng
        print("🔢 Đang lấy mã...")
        code_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, BUTTON_XPATH))
        )
        code = code_element.text or code_element.get_attribute('value') or code_element.get_attribute('innerHTML')
        
        if not code or not code.strip():
             raise Exception("Lấy được mã rỗng hoặc không hợp lệ.")

        print(f"✨ THÀNH CÔNG | MÃ: {code.strip()}")
        return {"status": "success", "data": code.strip()}

    except Exception as e:
        error_message = f"❌ CÓ LỖI: {str(e)}"
        print(error_message)
        if driver:
            os.makedirs("debug", exist_ok=True)
            timestamp = int(time.time())
            screenshot_path = f"debug/error_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Đã lưu ảnh lỗi vào {screenshot_path}")
        return {"status": "error", "message": str(e)}
    finally:
        if driver:
            driver.quit()
            print("✅ Đã đóng trình duyệt.")
