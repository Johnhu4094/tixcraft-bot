import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# === 設定 ===
TOKEN = "8372484239:AAFIUJkeqhD1kzfOWzkJ6_u05qfrxrjK0gk"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
CHAT_ID = None  # 先留空，第一次抓到訊息後會填入
LAST_UPDATE_ID = None

TIXCRAFT_URL = "https://tixcraft.com/ticket/area/25_nctdream/20097"
TARGET_ZONES = [
    "B2平面 7800區",
    "B2平面 6800區",
    "B1看台 6800區"
]

INTERVAL = 300  # 定時抓票間隔秒數（5 分鐘）

# === 抓票邏輯 ===
def fetch_ticket_info():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(TIXCRAFT_URL)
    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    driver.quit()

    result_lines = []
    zone_labels = soup.select("div.zone-label")
    for zone_label in zone_labels:
        zone_name = zone_label.get_text(strip=True)
        if zone_name not in TARGET_ZONES:
            continue

        group_id = zone_label.get("data-id")
        result_lines.append(f"🎟 區域: {zone_name}")

        area_list = soup.find(id=group_id)
        if area_list:
            for item in area_list.find_all("li"):
                result_lines.append(f"  - {item.get_text(strip=True)}")

    return "\n".join(result_lines)

# === 傳訊息 ===
def send_message(text):
    global CHAT_ID
    if CHAT_ID is None:
        print("❌ CHAT_ID 尚未設定，無法發送訊息")
        return
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=payload)

# === 抓 Telegram chat_id ===
def get_chat_id():
    global CHAT_ID, LAST_UPDATE_ID
    try:
        params = {}
        if LAST_UPDATE_ID is not None:
            params['offset'] = LAST_UPDATE_ID + 1
        res = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=10)
        data = res.json()
        for update in data.get("result", []):
            update_id = update.get("update_id")
            message = update.get("message")
            if not message:
                continue
            CHAT_ID = message["chat"]["id"]
            LAST_UPDATE_ID = update_id
            print(f"✅ 已抓到 CHAT_ID: {CHAT_ID}")
            return True
    except Exception as e:
        print("❌ 無法抓到 CHAT_ID:", e)
    return False

# === 主程式（定時抓票）===
if __name__ == "__main__":
    print("📬 等待第一次訊息以抓取 CHAT_ID...")
    while CHAT_ID is None:
        if get_chat_id():
            break
        time.sleep(5)

    print("⏰ 開始定時抓票，每 5 分鐘一次")
    while True:
        try:
            ticket_info = fetch_ticket_info()
            if ticket_info:
                send_message(ticket_info)
            else:
                send_message("⚠️ 找不到票券資訊")
        except Exception as e:
            send_message(f"❌ 抓取失敗: {e}")
        time.sleep(INTERVAL)
