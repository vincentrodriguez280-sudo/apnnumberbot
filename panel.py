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
GITHUB_RANGES = "ranges.json"

def load_ranges():
    data = {"FACEBOOK": {}, "WHATSAPP": {}}
    for path in [RANGES_FILE, GITHUB_RANGES]:
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
    if not info: return None
    panel = PANELS[info["panel"]]
    rid = info["id"]
    try:
        headers = {"mauthapi": panel["key"], "Content-Type": "application/json"}
        r = requests.post(panel["allocate"], headers=headers, json={"rid": rid}, timeout=20)
        print(f"[voltx] {rid}: {r.text[:1000]}")
        data = r.json()
        if data.get("meta", {}).get("code") == 200 and data.get("data"):
            full = data["data"]["full_number"]
            return {"number": full, "id": f"{info['panel']}|{full}"}
        return None
    except Exception as e:
        print(f"[CREATE ERR] {e}")
        return None

def get_otp(order_id):
    try:
        panel_name, number = order_id.split("|", 1) if "|" in order_id else ("voltx", order_id)
        panel = PANELS[panel_name]
        num_digits = re.sub(r'\D', '', number)
        r = requests.get(panel["otp"], headers={"mauthapi": panel["key"]}, timeout=15)
        # print(f"[OTP API RAW] {r.text[:2000]}")
        data = r.json()
        if data.get("meta", {}).get("code") == 200:
            for otp_item in data.get("data", {}).get("otps", []):
                en = re.sub(r'\D', '', str(otp_item.get("number","")))
                if en == num_digits or num_digits in en or en in num_digits or (len(en)>=8 and en[-8:] == num_digits[-8:]):
                    m = re.search(r'(\d{4,8})', otp_item.get("message",""))
                    if m:
                        print(f"[OTP MATCH] {number} -> {m.group(1)}")
                        return m.group(1)
        return None
    except Exception as e:
        print(f"[GET_OTP ERR] {e}")
        return None
