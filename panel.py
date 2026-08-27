import requests
import re

API_KEY = "NP-7ZWSHJTSSN4LP3HX"
BASE_URL = "https://npsmsnetwork.com/api/index.php?route=user"
HEADERS = {"mauthapi": API_KEY, "Content-Type": "application/json"}

RANGE_MAP = {
    "MADAGASCAR": "26134",
}
DISPLAY_NAME = {
    "MADAGASCAR": "MADAGASCAR 🇲🇬",
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
        payload = {"action": "getnum", "range": range_id}
        r = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=20)
        print(f"NP API: {r.text}")
        data = r.json()
        if data.get("meta", {}).get("code") == 200:
            full = data["data"]["full_number"]
            return {"number": full, "id": full}
        return None
    except Exception as e:
        print(f"NP Error: {e}")
        return None

def get_otp(order_id):
    try:
        num = order_id.replace("+","").replace(" ","")
        r = requests.get(f"{BASE_URL}?action=otp", headers=HEADERS, timeout=15)
        data = r.json()
        if data.get("meta", {}).get("code") == 200:
            for otp_entry in reversed(data.get("data", {}).get("otps", [])):
                entry_num = str(otp_entry.get("number","")).replace("+","")
                if entry_num == num or num in entry_num:
                    msg = otp_entry.get("message","")
                    m = re.search(r'\b(\d{3,8})\b', msg)
                    return m.group(1) if m else msg
        return None
    except:
        return None
