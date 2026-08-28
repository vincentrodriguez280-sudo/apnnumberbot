import requests, re, json, os

PANELS = {
    "voltx": {
        "type": "token",
        "key": "M5UMMJFPS49",
        "allocate": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum",
        "otp": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp",
    }
}

RANGES_FILE = "ranges.json"

def load_ranges():
    if not os.path.exists(RANGES_FILE):
        return {"FACEBOOK": {}, "WHATSAPP": {}}
    try:
        with open(RANGES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"FACEBOOK": {}, "WHATSAPP": {}}

def get_all_countries(service="facebook"):
    data = load_ranges()
    key = "WHATSAPP" if service.lower() in ["whatsapp","ws"] else "FACEBOOK"
    return list(data.get(key, {}).keys())

def get_display_name(code):
    # Button e clean name: MONTENEGRO -> Montenegro
    name = code.replace("_FB","").replace("_"," ").title()
    # 23276 er moto number thakle seta soray felbo button theke
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
        print(f"[voltx] {rid}: {r.text}")
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
        panel = PANELS[panel_name]
        num = number.replace("+","").replace(" ","")
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
