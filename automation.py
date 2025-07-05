# --- START OF FILE automation.py ---

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
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
        options.add_argument("--incognito") 
        
        bstack_options = {
            "os": "Windows", "osVersion": "11",
            "browserName": "Chrome", "browserVersion": "latest",
            "sessionName": f"Yeumoney Task - {keyword} - {random.randint(1000, 9999)}"
        }
        options.set_capability('bstack:options', bstack_options)

        print(f"Đang kết nối đến trình duyệt từ xa...")
        driver = webdriver.Remote(command_executor=remote_url, options=options)
        print("✅ KẾT NỐI TRÌNH DUYỆT TỪ XA THÀNH CÔNG!")
        
        # --- SỬ DỤNG DUCKDUCKGO ĐỂ TRÁNH CAPTCHA ---
        print("🌐 Đang truy cập DuckDuckGo...")
        driver.get("https://duckduckgo.com/")
        search_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'q')))
        search_query = f"site:{target['url']}"
        print(f"🦆 Đang tìm kiếm với DuckDuckGo: '{search_query}'")
        search_box.send_keys(search_query)
        search_box.submit()
        print("...Chờ trang kết quả của DuckDuckGo ổn định...")
        time.sleep(3)

        # === THAY ĐỔI: KIỂM TRA TRƯỜNG HỢP KHÔNG CÓ KẾT QUẢ ===
        try:
            # Dùng WebDriverWait với thời gian ngắn để kiểm tra nhanh
            no_results_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'results--no')]"))
            )
            if no_results_element:
                raise Exception(f"DuckDuckGo không tìm thấy kết quả nào cho truy vấn '{search_query}'. Vui lòng kiểm tra lại URL trong KEYWORD_MAP.")
        except TimeoutException:
            # Tốt! Không tìm thấy thông báo lỗi, nghĩa là có kết quả.
            print("ℹ️ Đã tìm thấy trang kết quả, tiếp tục xử lý.")
            pass

        # === THAY ĐỔI: SỬ DỤNG NHIỀU XPATH ĐỂ TĂNG ĐỘ TIN CẬY ===
        possible_xpaths = [
            # 1. XPath mới, hiện đại và ổn định hơn, dựa trên data-testid
            "//article[@data-testid='result']//a[@data-testid='result-title-a']",
            # 2. XPath cũ làm dự phòng
            "//div[@id='links']//a[contains(@class, 'result__a')]"
        ]
        
        first_result = None
        for i, xpath in enumerate(possible_xpaths):
            try:
                print(f"🔗 Đang thử tìm kết quả với XPath #{i+1}...")
                first_result = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                print(f"✅ Tìm thấy phần tử với XPath #{i+1}. Tiến hành click.")
                break 
            except TimeoutException:
                print(f"⚠️ Không tìm thấy với XPath #{i+1}. Thử phương án tiếp theo...")

        if not first_result:
            raise Exception("Không thể tìm thấy kết quả tìm kiếm trên DuckDuckGo với tất cả các XPath đã thử.")

        print("Sử dụng JavaScript để thực hiện cú click 'bất khả chiến bại'...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_result)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", first_result)
        
        print("✅ Đã click thành công vào kết quả tìm kiếm. Chờ trang đích tải...")
        time.sleep(7) 

        # --- Các bước sau giữ nguyên ---
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
                print(f"Đã xảy ra lỗi. Vui lòng kiểm tra video ghi lại phiên làm việc trên Dashboard của BrowserStack.")
            except: pass
        return {"status": "error", "message": str(e)}
    finally:
        if driver:
            driver.quit()
            print("✅ Đã đóng phiên làm việc từ xa.")
