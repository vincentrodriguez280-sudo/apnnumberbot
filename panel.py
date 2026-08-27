import requests

API_KEY = "NP-7ZWSHJTSSN4LP3HX"  # Tor key
BASE_URL = "https://npsmsnetwork.com/api/index.php?route=user"
HEADERS = {
    "mauthapi": API_KEY,
    "Content-Type": "application/json"
}

# Country -> Range mapping (NP Network er range ID)
# Tui tor panel e je range gulo ache oigula ekhane bosabi
# 26134 = UK EE (example)
RANGE_MAP = {
    "UK 🇬🇧": "26134",
    "UNITED KINGDOM": "26134",
    "SRI LANKA 🇱🇰": "94XXX",  # <-- ekhane tor Sri Lanka range bosao
    "LAOS 🇱🇦": "856XXX",
    "ALGERIA 🇩🇿": "213XXX",
    "TUNISIA 🇹🇳": "216XXX",
    "HAITI 🇭🇹": "509XXX",
    "ITALY 🇮🇹": "39XXX",
    "MALAYSIA 🇲🇾": "60XXX",
    "MOROCCO 🇲🇦": "212XXX",
    "MYANMAR 🇲🇲": "95XXX",
    "NIGERIA 🇳🇬": "234XXX",
    "USA 🇺🇸": "1XXX",
    "DEFAULT": "26134" # default UK
}

def get_range_id(country):
    country = country.upper().strip()
    for key, rid in RANGE_MAP.items():
        if key in country or country in key:
            return rid.replace("XXX","").replace("XX","")
    # Jodi exact na mile, first 5 digit ber koro (jemon 26134)
    return RANGE_MAP["DEFAULT"]

def create_order(service, country):
    """
    NP Network theke number allocate korbe
    """
    range_id = get_range_id(country)
    # Jodi range e XXX thake, clean koro
    range_id = range_id.replace("XXX","").replace("XX","")

    try:
        payload = {"action": "getnum", "range": range_id}
        r = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=15)
        data = r.json()

        if data.get("meta", {}).get("code") == 200:
            full = data["data"]["full_number"]
            print(f"[NP] Number allocated: {full} for {country} range {range_id}")
            return {"number": full, "id": full, "raw": data["data"]} # id hisebe number tai use korbo OTP khojar jonno
        
        elif data.get("meta", {}).get("code") == 2946:
            print(f"[NP] Out of stock for range {range_id}")
            return None
        else:
            print(f"[NP] Error: {data}")
            return None

    except Exception as e:
        print(f"[NP] Exception getnum: {e}")
        return None

def get_number(service, country):
    order = create_order(service, country)
    if order:
        return order["number"]
    return None

def get_otp(order_id):
    """
    order_id = phone number (447404333228)
    NP er /api/user?action=otp theke OTP ber korbe
    """
    try:
        # order_id theke only number rakho (no +)
        num = order_id.replace("+","")
        
        r = requests.get(f"{BASE_URL}?action=otp", headers=HEADERS, timeout=10)
        data = r.json()

        if data.get("meta", {}).get("code") == 200:
            otps = data.get("data", {}).get("otps", [])
            for otp_entry in otps:
                # OTP entry er number match korle OTP return
                entry_num = otp_entry.get("number","").replace("+","")
                if entry_num == num or num in entry_num or entry_num in num:
                    # message theke OTP code ber koro
                    msg = otp_entry.get("message","")
                    # OTP usually 4-8 digit
                    import re
                    m = re.search(r'\b(\d{4,8})\b', msg)
                    if m:
                        return m.group(1)
                    return msg # full message return if no code
        return None

    except Exception as e:
        print(f"[NP] Exception get_otp: {e}")
        return None

# Test
if __name__ == "__main__":
    print("Testing NP API...")
    order = create_order("FACEBOOK", "UK 🇬🇧")
    print(order)
