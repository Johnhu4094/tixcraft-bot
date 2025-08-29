import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

dotenv_path = ".env"
load_dotenv(dotenv_path=dotenv_path)
token = os.getenv("token")
# === 設定 ===
# 您的 Channel Access Token
token = token
url = 'https://api.line.me/v2/bot/message/push'

TIXCRAFT_URL = "https://tixcraft.com/ticket/area/25_twice/20208"
TARGET_ZONES = [
    "VIP區 $8800",
    "平面區 $6800",
    "平面區 $5800"

]

INTERVAL = 60  # 定時抓票間隔秒數（1 分鐘）

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
        area_list = soup.find(id=group_id)
        if area_list:
            for item in area_list.find_all("li"):
                text = item.get_text(strip=True)
                # ✅ 只在有 "剩餘" 時記錄
                if "剩餘" in text:
                    if not result_lines:
                        result_lines.append(f"2025-11-23 🎟 區域: {zone_name}")
                    result_lines.append(f"  - {text}")

    return "\n".join(result_lines)

# === 傳訊息 ===
def send_message(text):
    # 訊息內容
    message = {
        'to': 'U5a33d5a9fdaacee4060e60d4e86b93e2',  # 目標使用者的 User ID
        'messages': [
            {
                'type': 'text',
                'text': text
            }
        ]
    }

    # 設定標頭
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # 發送 POST 請求
    response = requests.post(url, headers=headers, json=message)

    # 檢查回應
    if response.status_code == 200:
        print('訊息已成功發送！')
    else:
        print(f'發送失敗，狀態碼：{response.status_code}')

# === 主程式（定時抓票）===
if __name__ == "__main__":
    print("⏰ 開始定時抓票，每 1 分鐘一次")
    while True:
        try:
            ticket_info = fetch_ticket_info()
            if ticket_info:
                send_message(ticket_info)
        except Exception as e:
            send_message(f"❌ 抓取失敗: {e}")
        time.sleep(INTERVAL)
