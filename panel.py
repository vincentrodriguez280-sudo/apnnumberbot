import requests, re, json, os

PANELS = {
    "voltx": {
        "type": "token",
        "key": "M5UMMJFPS49",
        "allocate": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum",
        "otp": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp",
    }
}

BASE_DIR = "/app/data" if os.path.exists("/app/data") else "."
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
# GitHub file fallback
GITHUB_RANGES = "ranges.json"

def load_ranges():
    data = {"FACEBOOK": {}, "WHATSAPP": {}}
    # Try persistent first, then github
    for path in [RANGES_FILE, GITHUB_RANGES]:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    raw = json.load(f)
                    for srv in ["FACEBOOK", "WHATSAPP"]:
                        for k, v in raw.get(srv, {}).items():
                            data[srv][k.upper()] = v
            except Exception as e:
                print(f"[RANGE LOAD ERROR {path}] {e}")
    return data

def get_all_countries(service="facebook"):
    data = load_ranges()
    key = "WHATSAPP" if service.lower() in ["whatsapp","ws"] else "FACEBOOK"
    return list(data.get(key, {}).keys())

def get_display_name(code):
    name = code.replace("_FB","").replace("_WS","").replace("_2","").replace("_"," ").title()
    name = ''.join([c for c in name if not c.isdigit()]).strip()
    return name if name else code.title()

def get_range_info(code):
    data = load_ranges()
    for srv in ["FACEBOOK", "WHATSAPP"]:
        if code.upper() in data.get(srv, {}):
            return {"id": data[srv][code.upper()], "panel": "voltx", "service": srv}
    return None

def create_order(service, country_code):
    info = get_range_info(country_code)
    if not info:
        print(f"[NO RANGE] {country_code}")
        return None
    panel = PANELS[info["panel"]]
    rid = info["id"]
    try:
        headers = {"mauthapi": panel["key"], "Content-Type": "application/json"}
        r = requests.post(panel["allocate"], headers=headers, json={"rid": rid}, timeout=20)
        print(f"[voltx] {rid}: {r.text[:500]}")
        data = r.json()
        if data.get("meta", {}).get("code") == 200 and data.get("data"):
            return {"number": data["data"]["full_number"], "id": f"{info['panel']}|{data['data']['full_number']}"}
        return None
    except Exception as e:
        print(f"[CREATE ERROR] {e}")
        return None

def get_otp(order_id):
    try:
        panel_name, number = order_id.split("|", 1) if "|" in order_id else ("voltx", order_id)
        panel = PANELS[panel_name]
        num = re.sub(r'\D', '', number)
        r = requests.get(panel["otp"], headers={"mauthapi": panel["key"]}, timeout=15)
        data = r.json()
        if data.get("meta", {}).get("code") == 200:
            for otp_item in data.get("data", {}).get("otps", []):
                en = re.sub(r'\D', '', str(otp_item.get("number","")))
                if en == num or num in en or en in num or (len(en)>8 and len(num)>8 and en[-8:] == num[-8:]):
                    m = re.search(r'(\d{4,8})', otp_item.get("message",""))
                    if m:
                        return m.group(1)
        return None
    except Exception as e:
        print(f"[GET_OTP ERROR] {e}")
        return None
