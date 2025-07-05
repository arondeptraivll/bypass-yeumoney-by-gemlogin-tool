# --- START OF FILE automation.py ---

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import random
import os
from urllib.parse import urlparse

# ================= CẤU HÌNH (Không đổi) =================
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
PROXY_FILE = "proxies.txt"
UNWANTED_LINKS = ["#", "javascript:", "logout", "signout", "tel:", "mailto:"]
BUTTON_XPATH = "//*[@id='layma_me_vuatraffic']" 

# ================= TIỆN ÍCH =================
def load_proxies(filename=PROXY_FILE):
    """Đọc danh sách proxy từ file và lọc bỏ các dòng rỗng."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File proxy '{filename}' không tồn tại. Vui lòng tạo file và thêm proxy.")
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    if not proxies:
        raise ValueError(f"File '{filename}' rỗng hoặc không chứa proxy hợp lệ.")
    print(f"✅ Đã tải {len(proxies)} proxy từ '{filename}'.")
    return proxies

def check_for_captcha(driver):
    """Kiểm tra xem trang hiện tại có phải là trang CAPTCHA của Google không."""
    # Dấu hiệu đáng tin cậy nhất là URL chứa "/sorry/" hoặc "/consent/"
    current_url = driver.current_url
    if "/sorry/" in current_url or "/consent/" in current_url:
        print("DETECTED: CAPTCHA page by URL.")
        return True
    # Dấu hiệu thứ hai là tiêu đề trang
    if "reCAPTCHA" in driver.title or "Unusual traffic" in driver.title:
        print("DETECTED: CAPTCHA page by title.")
        return True
    return False

# ... Các hàm tiện ích khác giữ nguyên ...
def is_valid_link(href, domain):
    if not href: return False
    if any(unwanted in href.lower() for unwanted in UNWANTED_LINKS): return False
    parsed = urlparse(href)
    return ((not parsed.netloc or parsed.netloc == domain) and not href.startswith(('javascript:', 'mailto:', 'tel:')))

def get_internal_links(driver):
    try:
        domain = urlparse(driver.current_url).netloc
        all_links = driver.find_elements(By.XPATH, "//a[@href]")
        valid_links = [link for link in all_links if is_valid_link(link.get_attribute('href'), domain) and link.is_displayed() and link.is_enabled()]
        return valid_links
    except Exception as e:
        print(f"❌ Lỗi khi lấy link: {str(e)}"); return []

def execute_js_action(driver, step_name):
    print(f"💉 Đang inject JS cho {step_name}...")
    try:
        if not os.path.exists(JS_FILE): raise Exception(f"File {JS_FILE} không tồn tại")
        with open(JS_FILE, 'r') as f: driver.execute_script(f.read())
        print(f"✅ Đã inject JS cho {step_name}. Chờ 5 giây để hành động hoàn tất...")
        time.sleep(5)
        return True
    except Exception as e:
        print(f"❌ Lỗi khi inject JS cho {step_name}: {str(e)}"); return False


# ================= HÀM CHÍNH ĐỂ BOT GỌI =================
def run_automation_task(keyword):
    if keyword not in KEYWORD_MAP:
        return {"status": "error", "message": f"Từ khóa không hợp lệ: {keyword}"}
    
    target = KEYWORD_MAP[keyword]
    proxies = load_proxies()
    random.shuffle(proxies) # Xáo trộn danh sách để thử ngẫu nhiên
    
    driver = None
    successful_proxy = None

    # --- VÒNG LẶP THỬ PROXY ---
    for i, proxy_url in enumerate(proxies):
        print("\n" + "="*50)
        print(f"🔄 Vòng lặp {i+1}/{len(proxies)}. Đang thử proxy: {proxy_url}")
        
        try:
            # --- CẤU HÌNH TRÌNH DUYỆT VỚI PROXY HIỆN TẠI ---
            options = webdriver.ChromeOptions()
            
            # Cấu hình proxy cho cả HTTP/HTTPS và SOCKS
            if 'socks' in proxy_url:
                 # SOCKS proxy
                options.add_argument(f'--proxy-server={proxy_url}')
            else:
                # HTTP/HTTPS proxy
                proxy_protocol_stripped = proxy_url.split('://')[-1]
                options.add_argument(f'--proxy-server=http://{proxy_protocol_stripped}')


            # Cải thiện fingerprint
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            bs_user = os.environ.get('BS_USER')
            bs_key = os.environ.get('BS_KEY')
            if not bs_user or not bs_key: raise Exception("Chưa thiết lập biến môi trường BS_USER và BS_KEY.")
            remote_url = f"https://{bs_user}:{bs_key}@hub-cloud.browserstack.com/wd/hub"
            
            bstack_options = {
                "os": "Windows", "osVersion": "11",
                "browserName": "Chrome", "browserVersion": "latest",
                "sessionName": f"Proxy Test {i+1} - {keyword}"
            }
            options.set_capability('bstack:options', bstack_options)

            print(f"Đang kết nối đến trình duyệt từ xa...")
            driver = webdriver.Remote(command_executor=remote_url, options=options)
            driver.set_page_load_timeout(45) # Set timeout để tránh treo
            print("✅ Kết nối thành công!")
            
            # --- KIỂM TRA PROXY VỚI GOOGLE ---
            print("🔬 Đang kiểm tra proxy trên Google...")
            driver.get("https://www.google.com")
            
            if check_for_captcha(driver):
                raise ValueError("Proxy bị Google phát hiện CAPTCHA.")

            print("✅ Proxy trong sạch! Tiến hành tác vụ chính.")
            successful_proxy = proxy_url
            break # Thoát khỏi vòng lặp vì đã tìm thấy proxy tốt

        except (TimeoutException, WebDriverException, ValueError) as e:
            print(f"❌ Proxy {proxy_url} thất bại: {str(e)[:200]}")
            if driver:
                driver.quit()
            driver = None
            continue # Thử proxy tiếp theo

    # --- KẾT THÚC VÒNG LẶP PROXY ---
    if not successful_proxy or not driver:
        return {"status": "error", "message": "Không tìm thấy proxy nào hoạt động trong danh sách. Vui lòng cập nhật file proxies.txt."}

    # --- THỰC HIỆN TÁC VỤ CHÍNH VỚI PROXY TỐT ---
    try:
        print(f"\n🚀 Bắt đầu tác vụ chính với proxy: {successful_proxy}")
        
        search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'q')))
        search_query = f"site:{target['url']}"
        search_box.send_keys(search_query)
        search_box.submit()
        
        print(f"...Đã tìm kiếm '{search_query}'. Chờ kết quả...")
        time.sleep(3)
        
        first_result = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='search']//a[h3]"))
        )
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_result)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", first_result)
        
        print("✅ Đã click thành công. Chờ trang đích tải...")
        time.sleep(7) 

        if not execute_js_action(driver, "lần 1"): raise Exception("Thất bại ở bước 1: Inject JS lần 1")
        
        internal_links = get_internal_links(driver)
        if not internal_links: raise Exception("Không tìm thấy link nội bộ hợp lệ.")
        
        chosen_link = random.choice(internal_links)
        print(f"👉 Chọn link: {chosen_link.get_attribute('href')}")
        driver.execute_script("arguments[0].click();", chosen_link)
        time.sleep(7)

        if not execute_js_action(driver, "lần 2"): raise Exception("Thất bại ở bước 2: Inject JS lần 2")
        
        code_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, BUTTON_XPATH)))
        code = code_element.text or code_element.get_attribute('value') or code_element.get_attribute('innerHTML')
        if not code or not code.strip(): raise Exception("Lấy được mã rỗng hoặc không hợp lệ.")
        
        print(f"✨ THÀNH CÔNG | MÃ: {code.strip()}")
        return {"status": "success", "data": code.strip()}

    except Exception as e:
        error_message = f"❌ CÓ LỖI TRONG TÁC VỤ CHÍNH: {str(e)}"
        print(error_message)
        return {"status": "error", "message": str(e)}
    finally:
        if driver:
            driver.quit()
            print("✅ Đã đóng phiên làm việc từ xa.")
