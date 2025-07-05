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
PROXY_FILE = "proxies.txt"
UNWANTED_LINKS = ["#", "javascript:", "logout", "signout", "tel:", "mailto:"]
BUTTON_XPATH = "//*[@id='layma_me_vuatraffic']" 

# ================= TIỆN ÍCH =================
def load_proxies(filename=PROXY_FILE):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File proxy '{filename}' không tồn tại.")
    with open(filename, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    if not proxies:
        raise ValueError(f"File '{filename}' rỗng hoặc không chứa proxy hợp lệ.")
    print(f"✅ Đã tải {len(proxies)} proxy từ '{filename}'.")
    return proxies

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
    try:
        proxies = load_proxies()
    except (FileNotFoundError, ValueError) as e:
        return {"status": "error", "message": str(e)}

    random.shuffle(proxies)
    
    # --- VÒNG LẶP THỬ-SAI-LÀM-LẠI ---
    for i, proxy_url in enumerate(proxies):
        print("\n" + "="*50)
        print(f"🔄 Vòng lặp {i+1}/{len(proxies)}. Thử thực hiện tác vụ với proxy: {proxy_url}")
        
        driver = None # Đảm bảo driver được reset cho mỗi vòng lặp
        try:
            # --- Bước 1: Khởi tạo trình duyệt với proxy hiện tại ---
            options = webdriver.ChromeOptions()
            options.add_argument(f'--proxy-server={proxy_url}')
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            bs_user = os.environ.get('BS_USER')
            bs_key = os.environ.get('BS_KEY')
            if not bs_user or not bs_key:
                # Nếu không có thông tin BS, báo lỗi và dừng hẳn
                return {"status": "error", "message": "Thiếu biến môi trường BS_USER hoặc BS_KEY."}

            remote_url = f"https://{bs_user}:{bs_key}@hub-cloud.browserstack.com/wd/hub"
            bstack_options = {"os": "Windows", "osVersion": "11", "browserName": "Chrome", "browserVersion": "latest", "sessionName": f"Task Attempt {i+1} - {keyword}"}
            options.set_capability('bstack:options', bstack_options)

            print("Đang kết nối đến trình duyệt từ xa...")
            driver = webdriver.Remote(command_executor=remote_url, options=options)
            driver.set_page_load_timeout(60) # Tăng timeout để cho proxy yếu có cơ hội
            
            # --- Bước 2: Thử thực hiện toàn bộ tác vụ ---
            print("🌐 Truy cập Google để tìm kiếm mục tiêu...")
            driver.get("https://www.google.com")
            
            search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'q')))
            search_query = f"site:{target['url']}"
            search_box.send_keys(search_query)
            search_box.submit()
            print(f"...Đã tìm kiếm '{search_query}'.")

            # Nếu bị CAPTCHA, bước này sẽ timeout
            first_result = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[@id='search']//a[h3]")))
            driver.execute_script("arguments[0].click();", first_result)
            print("✅ Đã click vào kết quả tìm kiếm. Chờ trang đích tải...")
            time.sleep(7) 

            # Các bước còn lại
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
            
            # --- THÀNH CÔNG! ---
            print(f"✨ THÀNH CÔNG VỚI PROXY: {proxy_url} | MÃ: {code.strip()}")
            driver.quit() # Đóng trình duyệt sau khi thành công
            return {"status": "success", "data": code.strip()}

        except (TimeoutException, WebDriverException) as e:
            # Bắt các lỗi phổ biến của Selenium (timeout, không kết nối được,...)
            # Đây là dấu hiệu proxy hỏng hoặc bị CAPTCHA
            print(f"❌ Proxy {proxy_url} thất bại. Lỗi: {str(e)[:150]}...")
            print("➡️ Thử proxy tiếp theo.")
            if driver:
                driver.quit() # Rất quan trọng: đóng phiên làm việc lỗi
            continue # Chuyển sang proxy tiếp theo trong vòng lặp

    # Nếu vòng lặp kết thúc mà không có proxy nào thành công
    return {"status": "error", "message": "Đã thử tất cả proxy nhưng không có proxy nào hoàn thành được tác vụ. Vui lòng kiểm tra lại danh sách proxy."}
