import requests
import re

API_KEY = "4d7e8a90d19b1dc5"
BASE_URL_ALLOCATE = "https://yesms.online/api/allocate_number"
BASE_URL_OTP = "https://yesms.online/api/user_numbers"
HEADERS = {"authkey": API_KEY, "Content-Type": "application/json"}

# Tomar Range Gula
RANGE_MAP = {
    "MADAGASCAR": "26134",
    "MONTENEGRO_382661": "382661",
    "NEPAL_977X97": "977X97",
}
DISPLAY_NAME = {
    "MADAGASCAR": "MADAGASCAR 🇲🇬",
    "MONTENEGRO_382661": "MONTENEGRO 382661XXX 🇲🇪",
    "NEPAL_977X97": "NEPAL 977X97 🇳🇵",
}

def get_all_countries():
    return list(RANGE_MAP.keys())

def get_display_name(code):
    return DISPLAY_NAME.get(code, code)

def get_range_id(code):
    return RANGE_MAP.get(code.upper(), "26134")

def create_order(service, country_code):
    range_id = get_range_id(country_code)
    try:
        payload = {"range_id": range_id}
        r = requests.post(BASE_URL_ALLOCATE, headers=HEADERS, json=payload, timeout=20)
        print(f"YESMS API: {r.text}")
        data = r.json()
        if data.get("success") == True:
            full = data["data"]["full_number"]
            return {"number": full, "id": full}
        return None
    except Exception as e:
        print(f"YESMS Error: {e}")
        return None

def get_otp(order_id):
    try:
        num = order_id.replace("+","").replace(" ","").replace("-","")
        r = requests.get(BASE_URL_OTP, headers={"authkey": API_KEY}, timeout=15)
        data = r.json()
        if data.get("success") == True:
            for entry in data.get("logs", []):
                entry_num = str(entry.get("number","")).replace("+","").replace(" ","").replace("-","")
                if entry_num == num or num in entry_num or entry_num in num:
                    return entry.get("otp_code") or entry.get("full_message")
        return None
    except Exception as e:
        print(f"YESMS OTP Error: {e}")
        return None
