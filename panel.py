import requests, re

PANELS = {
    "yesms": {
        "type": "yesms",
        "key": "4d7e8a90d19b1dc5",
        "allocate": "https://yesms.online/api/allocate_number",
        "otp": "https://yesms.online/api/user_numbers",
    },
    "voltx": {
        "type": "token", # <-- voltx ekhon token api
        "key": "M5UMMJFPS49",
        "allocate": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum",
        "otp": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp",
    }
}

# Facebook - sudhu Nepal (yesms theke)
FB_RANGES = {
    "NEPAL": {"id": "977X97", "panel": "yesms"},
}

# WhatsApp - sudhu Sierra Leone (voltx theke)
WS_RANGES = {
    "SIERRA_LEONE": {"id": "23275", "panel": "voltx"}, # Token API te XXX chara
}

DISPLAY_NAME = {
    "NEPAL": "Nepal",
    "SIERRA_LEONE": "Sierra Leone",
}

def get_all_countries(service="facebook"):
    return list(WS_RANGES.keys()) if service == "whatsapp" else list(FB_RANGES.keys())

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
            print(r.text)
            data = r.json()
            if data.get("success"):
                return {"number": data["data"]["full_number"], "id": f"{info['panel']}|{data['data']['full_number']}"}
        else: # token - voltx
            headers = {"mauthapi": panel["key"], "Content-Type": "application/json"}
            clean_rid = rid.replace("X","")
            r = requests.post(panel["allocate"], headers=headers, json={"rid": clean_rid}, timeout=20)
            print(f"[voltx] {clean_rid}: {r.text}")
            data = r.json()
            if data.get("meta", {}).get("code") == 200 and data.get("data"):
                full = data["data"]["full_number"]
                return {"number": full, "id": f"{info['panel']}|{full}"}
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_otp(order_id):
    try:
        panel_name, number = order_id.split("|", 1) if "|" in order_id else ("yesms", order_id)
        panel = PANELS[panel_name]
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
                        msg = otp.get("message","")
                        m = re.search(r'(\d{4,8})', msg)
                        if m: return m.group(1)
        return None
    except Exception as e:
        print(f"OTP Error: {e}")
        return None
