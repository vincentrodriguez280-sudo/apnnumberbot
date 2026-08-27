import requests
import re

API_KEY = "NP-7ZWSHJTSSN4LP3HX"
BASE_URL = "https://npsmsnetwork.com/api/index.php?route=user"
HEADERS = {
    "mauthapi": API_KEY,
    "Content-Type": "application/json"
}

# ===== TUMI SUDU EKHANE RANGE ADD KORBA =====
# Joto range add korba, bot e toto desh dekhabe
RANGE_MAP = {
    "MADAGASCAR 🇲🇬": "26134", # Facebook Madagascar - 26134XXX
}
# ===========================================

def get_all_countries():
    return list(RANGE_MAP.keys())

def get_range_id(country):
    return RANGE_MAP.get(country, "26134")

def create_order(service, country):
    range_id = get_range_id(country).replace("XXX","").strip()
    try:
        payload = {"action": "getnum", "range": range_id}
        r = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=20)
        data = r.json()
        print(f"[NP] {country} -> Range {range_id} -> {data}")

        if data.get("meta", {}).get("code") == 200:
            full = data["data"]["full_number"]
            return {"number": full, "id": full, "raw": data["data"]}
        elif data.get("meta", {}).get("code") == 2946:
            print(f"[NP] Out of stock for {range_id}")
            return None
        else:
            print(f"[NP] Error: {data}")
            return None
    except Exception as e:
        print(f"[NP] Exception getnum: {e}")
        return None

def get_number(service, country):
    order = create_order(service, country)
    return order["number"] if order else None

def get_otp(order_id):
    try:
        num = order_id.replace("+","").replace(" ","")
        r = requests.get(f"{BASE_URL}?action=otp", headers=HEADERS, timeout=15)
        data = r.json()

        if data.get("meta", {}).get("code") == 200:
            otps = data.get("data", {}).get("otps", [])
            # Last er OTP gulo age check
            for otp_entry in reversed(otps):
                entry_num = str(otp_entry.get("number","")).replace("+","")
                if entry_num == num or num in entry_num or entry_num in num:
                    msg = otp_entry.get("message","")
                    m = re.search(r'\b(\d{3,8})\b', msg)
                    if m:
                        return m.group(1)
                    return msg
        return None
    except Exception as e:
        print(f"[NP] OTP Error: {e}")
        return None
