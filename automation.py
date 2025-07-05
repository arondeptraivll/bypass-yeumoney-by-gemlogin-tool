from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
UNWANTED_LINKS = ["#", "javascript:", "logout", "signout", "tel:", "mailto:"]
BUTTON_XPATH = "//*[@id='layma_me_vuatraffic']" 

# ================= TIỆN ÍCH (Không đổi) =================
# ... (Giữ nguyên các hàm tiện ích)
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
    print(f"\n🔍 Bắt đầu xử lý cho: {target['name']} ({target['url']})")
    driver = None
    try:
        # --- KẾT NỐI ĐẾN BROWSERSTACK ---
        bs_user = os.environ.get('BS_USER')
        bs_key = os.environ.get('BS_KEY')
        if not bs_user or not bs_key: raise Exception("Chưa thiết lập biến môi trường BS_USER và BS_KEY.")
        remote_url = f"https://{bs_user}:{bs_key}@hub-cloud.browserstack.com/wd/hub"
        
        options = webdriver.ChromeOptions()
        bstack_options = {
            "os": "Windows", "osVersion": "11",
            "browserName": "Chrome", "browserVersion": "latest",
            "sessionName": f"Yeumoney Task - {keyword}"
        }
        options.set_capability('bstack:options', bstack_options)

        print(f"Đang kết nối đến trình duyệt từ xa tại BrowserStack...")
        driver = webdriver.Remote(command_executor=remote_url, options=options)
        print("✅ KẾT NỐI TRÌNH DUYỆT TỪ XA THÀNH CÔNG!")
        
        print("🌐 Đang truy cập Google...")
        driver.get("https://www.google.com")
        
        search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'q')))
        search_box.send_keys(f"site:{target['url']}")
        search_box.submit()
        
        # --- THAY ĐỔI CHIẾN LƯỢC TẠI ĐÂY ---
        print("...Chờ trang kết quả của Google ổn định...")
        time.sleep(5) # Tăng thời gian chờ lên 5 giây

        print("🔗 Đang tìm kết quả tìm kiếm với XPath chính xác hơn...")
        # Sử dụng XPath mạnh mẽ hơn, nhắm vào link có chứa tiêu đề h3
        first_result_xpath = "//div[@id='search']//a[h3]"
        
        # Chờ cho đến khi phần tử có thể nhìn thấy được
        first_result = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, first_result_xpath))
        )
        
        print("Sử dụng JavaScript để thực hiện cú click 'bất khả chiến bại'...")
        # Sử dụng JavaScript để click, tránh các lớp phủ vô hình
        driver.execute_script("arguments[0].click();", first_result)
        
        print("✅ Đã click thành công vào kết quả tìm kiếm. Chờ trang đích tải...")
        time.sleep(7) 

        # --- Các bước sau giữ nguyên logic đúng của bạn ---
        if not execute_js_action(driver, "lần 1"): raise Exception("Thất bại ở bước 1: Inject JS lần 1")
        
        print("🎲 Đang tìm link nội bộ...")
        internal_links = get_internal_links(driver)
        if not internal_links: raise Exception("Không tìm thấy link nội bộ hợp lệ để tiếp tục.")
        
        chosen_link = random.choice(internal_links)
        print(f"👉 Chọn link: {chosen_link.get_attribute('href')}")
        driver.execute_script("arguments[0].click();", chosen_link)
        time.sleep(7)

        if not execute_js_action(driver, "lần 2"): raise Exception("Thất bại ở bước 2: Inject JS lần 2")
        
        print("🔢 Đang lấy mã...")
        code_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, BUTTON_XPATH)))
        code = code_element.text or code_element.get_attribute('value') or code_element.get_attribute('innerHTML')
        if not code or not code.strip(): raise Exception("Lấy được mã rỗng hoặc không hợp lệ.")
        
        print(f"✨ THÀNH CÔNG | MÃ: {code.strip()}")
        return {"status": "success", "data": code.strip()}

    except Exception as e:
        error_message = f"❌ CÓ LỖI: {str(e)}"
        print(error_message)
        if driver:
            try:
                # Cố gắng chụp ảnh màn hình để chẩn đoán
                screenshot_name = f"debug_error_{int(time.time())}.png"
                driver.save_screenshot(screenshot_name)
                print(f"Đã lưu ảnh lỗi vào {screenshot_name} (Lưu ý: trên server sẽ không thể lấy file này về)")
            except: pass
        return {"status": "error", "message": str(e)}
    finally:
        if driver:
            driver.quit()
            print("✅ Đã đóng phiên làm việc từ xa.")
