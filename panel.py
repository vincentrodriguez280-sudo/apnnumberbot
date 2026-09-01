import requests, re, json, os

PANELS = {
    "voltx": {
        "key": "M5UMMJFPS49",
        "allocate": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum",
        "otp": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp",
    }
}

BASE_DIR = "/app/data" if os.path.exists("/app/data") else "."
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")

def load_ranges():
    data = {"FACEBOOK": {}, "WHATSAPP": {}}
    for path in [RANGES_FILE, "ranges.json"]:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    raw = json.load(f)
                    for srv in ["FACEBOOK", "WHATSAPP"]:
                        for k, v in raw.get(srv, {}).items():
                            data[srv][k.upper()] = v
            except: pass
    return data

def get_all_countries(service="facebook"):
    key = "WHATSAPP" if service.lower() in ["whatsapp","ws"] else "FACEBOOK"
    return list(load_ranges().get(key, {}).keys())

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
    if not info: return None
    panel = PANELS[info["panel"]]
    try:
        r = requests.post(panel["allocate"], headers={"mauthapi": panel["key"], "Content-Type": "application/json"}, json={"rid": info["id"]}, timeout=20)
        j = r.json()
        if j.get("meta", {}).get("code") == 200 and j.get("data"):
            return {"number": j["data"]["full_number"], "id": f"{info['panel']}|{j['data']['full_number']}"}
        print(f"[OUT] {country_code} {j}")
        return None
    except Exception as e:
        print(f"[CREATE ERR] {e}")
        return None

def get_otp(order_id):
    try:
        _, number = order_id.split("|", 1) if "|" in order_id else ("voltx", order_id)
        num_digits = re.sub(r'\D', '', number)
        r = requests.get(PANELS["voltx"]["otp"], headers={"mauthapi": PANELS["voltx"]["key"]}, timeout=15)
        data = r.json()
        if data.get("meta", {}).get("code")!= 200:
            return None
        for item in data.get("data", {}).get("otps", []):
            en = re.sub(r'\D', '', str(item.get("number","")))
            if num_digits[-8:] not in en:
                continue
            msg = str(item.get("message",""))
            # FB: 123456 | WS: G-123456, 123-456, WhatsApp code: 123456
            m = re.search(r'G-?(\d{4,8})|(\d{3}-\d{3})|(\d{4,8})', msg)
            if m:
                code = next((g for g in m.groups() if g), None)
                if code:
                    clean = code.replace("-", "")
                    print(f"[OTP FOUND] {number} => {clean}")
                    return clean
        return None
    except Exception as e:
        print(f"[OTP ERR] {e}")
        return None
