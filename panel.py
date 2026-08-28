import requests, re

PANELS = {
    "yesms": {
        "type": "yesms",
        "key": "4d7e8a90d19b1dc5",
        "allocate": "https://yesms.online/api/allocate_number",
        "otp": "https://yesms.online/api/user_numbers",
    },
    "voltx": {
        "type": "token",
        "key": "M5UMMJFPS49",
        "allocate": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum",
        "otp": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp",
    }
}

# FB - 3 ta range
FB_RANGES = {
    "MONTENEGRO": {"id": "38267437402", "panel": "voltx"},
    "SIERRA_LEONE_23274_FB": {"id": "23274", "panel": "voltx"},
    "MADAGASCAR_2613857": {"id": "2613857", "panel": "voltx"},
}

# WS - 2 ta range
WS_RANGES = {
    "SIERRA_LEONE_23276": {"id": "23276", "panel": "voltx"},
    "SIERRA_LEONE_23274": {"id": "23274", "panel": "voltx"},
}

DISPLAY_NAME = {
    "MONTENEGRO": "Montenegro",
    "SIERRA_LEONE_23274_FB": "Sierra Leone",
    "MADAGASCAR_2613857": "Madagascar",
    "SIERRA_LEONE_23276": "Sierra Leone",
    "SIERRA_LEONE_23274": "Sierra Leone",
}

def get_all_countries(service="facebook"):
    if service.lower() in ["whatsapp", "ws"]:
        return list(WS_RANGES.keys())
    return list(FB_RANGES.keys())

def get_display_name(code):
    return DISPLAY_NAME.get(code, code.replace("_"," ").title())

def get_range_info(code):
    return {**FB_RANGES, **WS_RANGES}.get(code.upper())

def create_order(service, country_code):
    info = get_range_info(country_code)
    if not info: return None
    panel = PANELS[info["panel"]]
    rid = info["id"]
    try:
        if panel["type"] == "yesms":
            headers = {"authkey": panel["key"], "Content-Type": "application/json"}
            r = requests.post(panel["allocate"], headers=headers, json={"range_id": rid}, timeout=20)
            data = r.json()
            if data.get("success"):
                return {"number": data["data"]["full_number"], "id": f"{info['panel']}|{data['data']['full_number']}"}
        else:
            headers = {"mauthapi": panel["key"], "Content-Type": "application/json"}
            r = requests.post(panel["allocate"], headers=headers, json={"rid": rid}, timeout=20)
            print(f"[{info['panel']}] {rid}: {r.text}")
            data = r.json()
            if data.get("meta", {}).get("code") == 200 and data.get("data"):
                return {"number": data["data"]["full_number"], "id": f"{info['panel']}|{data['data']['full_number']}"}
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_otp(order_id):
    try:
        panel_name, number = order_id.split("|", 1) if "|" in order_id else ("voltx", order_id)
        panel = PANELS.get(panel_name, PANELS["voltx"])
        num = number.replace("+","").replace(" ","")
        if panel["type"] == "yesms":
            r = requests.get(panel["otp"], headers={"authkey": panel["key"]}, timeout=15)
            data = r.json()
            if data.get("success"):
                for entry in data.get("logs", []):
                    en = str(entry.get("number","")).replace("+","").replace(" ","")
                    if en == num or num in en or en in num:
                        return entry.get("otp_code")
        else:
            r = requests.get(panel["otp"], headers={"mauthapi": panel["key"]}, timeout=15)
            data = r.json()
            if data.get("meta", {}).get("code") == 200:
                for otp in data.get("data", {}).get("otps", []):
                    en = str(otp.get("number","")).replace("+","").replace(" ","")
                    if en == num or num in en or en in num:
                        m = re.search(r'(\d{4,8})', otp.get("message",""))
                        if m: return m.group(1)
        return None
    except:
        return None
