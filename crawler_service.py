import time
import re
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_schedule_data(msv, password):
    print(f"🚀 Bắt đầu crawler cho MSV: {msv}")
    
    # Khởi tạo driver là None để tránh lỗi UnboundLocalError
    driver = None
    
    # URL
    URL_LOGIN = "https://sinhvien.eaut.edu.vn/Login.aspx"
    URL_SCHEDULE = "https://sinhvien.eaut.edu.vn/wfrmLichHocSinhVienTinChi.aspx"

    # Cấu hình Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Biến kiểm tra môi trường Render
    is_render = os.environ.get("RENDER")

    if is_render:
        # Cấu hình đường dẫn Chrome thật trên Render
        chrome_binary_path = "/opt/render/project/.render/chrome/opt/google/chrome/google-chrome"
        chrome_options.binary_location = chrome_binary_path
    
    try:
        # --- KHỞI TẠO DRIVER (Đã sửa) ---
        if is_render:
            # Trên Render: KHÔNG dùng ChromeDriverManager để tránh lệch version
            # Selenium 4.x sẽ tự tìm driver tương thích với bản Chrome 143 đã cài
            driver = webdriver.Chrome(options=chrome_options)
        else:
            # Trên máy cá nhân: Dùng ChromeDriverManager cho tiện
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
        wait = WebDriverWait(driver, 10)

        # 1. ĐĂNG NHẬP
        driver.get(URL_LOGIN)
        
        # Điền thông tin
        user_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text']")))
        pass_input = driver.find_element(By.XPATH, "//input[@type='password']")
        
        user_input.clear()
        user_input.send_keys(msv)
        pass_input.clear()
        pass_input.send_keys(password)

        # Click Login
        try:
            btn = driver.find_element(By.ID, "btnDangNhap")
        except:
            btn = driver.find_element(By.XPATH, "//input[@type='submit']")
        btn.click()
        
        time.sleep(2)

        # Kiểm tra lỗi đăng nhập
        if "không hợp lệ" in driver.page_source:
            print("❌ Sai mật khẩu")
            return None 

        # 2. VÀO LỊCH HỌC
        driver.get(URL_SCHEDULE)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # 3. PARSE DATA
        soup = BeautifulSoup(driver.page_source, 'lxml')
        tables = soup.find_all('table')
        schedule_table = None
        for tbl in tables:
            if "Thứ 2" in tbl.get_text() or "Thứ Hai" in tbl.get_text():
                schedule_table = tbl
                break
        
        if not schedule_table: return []

        # Logic Parse
        rows = schedule_table.find_all('tr')
        days_template = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
        final_data = [{"date": d, "classes": []} for d in days_template]

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 3: continue 

            for i, cell in enumerate(cells):
                content = " ".join(cell.get_text().split())
                if not content: continue
                
                if "Tiết học:" in content:
                    day_index = (i - 1) if len(cells) > 7 else i
                    if day_index < 0 or day_index >= 7: day_index = 0
                    
                    subject = content.split("Tiết học:")[0].strip()
                    time_match = re.search(r'Tiết học:?\s*([\d,\-]+)', content)
                    room_match = re.search(r'Phòng:?\s*(.+?)(?=\s+GV|$)', content)
                    teacher_match = re.search(r'GV:?\s*(.+?)(?=\s+Phòng|$)', content)

                    tiet = time_match.group(1) if time_match else "??"
                    room = room_match.group(1).strip() if room_match else "Online"
                    teacher = teacher_match.group(1).strip() if teacher_match else "N/A"
                    
                    start_tiet = int(tiet.split('-')[0]) if '-' in tiet and tiet.split('-')[0].isdigit() else 1
                    buoi = "Sáng" if start_tiet <= 6 else "Chiều"
                    
                    color = "bg-blue-100 text-blue-800 border-blue-200"
                    if "Thực tập" in subject or "Thực hành" in subject:
                        color = "bg-green-100 text-green-800 border-green-200"

                    class_info = {
                        "name": subject,
                        "time": f"{buoi} (Tiết {tiet})",
                        "room": room,
                        "teacher": teacher,
                        "color": color
                    }
                    final_data[day_index]["classes"].append(class_info)
        
        return final_data

    except Exception as e:
        print(f"Lỗi: {e}")
        return None
    finally:
        # Chỉ quit nếu driver đã được khởi tạo thành công
        if driver: driver.quit()