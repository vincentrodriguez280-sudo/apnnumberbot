import requests, re, json, os
from bs4 import BeautifulSoup

BASE_DIR = "/app/data" if os.path.exists("/app/data") else "."
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
NUMBERS_FILE = os.path.join(BASE_DIR, "numbers.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

CFG = {}
for p in ["config.json", CONFIG_FILE]:
    if os.path.exists(p):
        try:
            with open(p,"r") as f: CFG.update(json.load(f))
        except: pass

PANELS = {
    "voltx": {
        "key": "M5UMMJFPS49",
        "allocate": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/getnum",
        "otp": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api/success-otp",
    },
    "client": {
        "url": CFG.get("PANEL_URL", "http://139.99.68.231/ints/client/SMSCDRStats"),
        "login_url": CFG.get("LOGIN_URL", "http://139.99.68.231/ints/client/login"),
        "user": CFG.get("PANEL_USER", "Polaszone"),
        "pass": CFG.get("PANEL_PASS", "Polaszone"),
    }
}

session = requests.Session()
_logged_in = False

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
    base = list(load_ranges().get(key, {}).keys())
    # Always add Nepal for FB from file - only once
    if key == "FACEBOOK":
        # Remove any existing Nepal variants to avoid duplicate
        base = [b for b in base if "NEPAL" not in b.upper()]
        base.insert(0, "NEPAL_FB")
    return base

def get_display_name(code):
    name = code.replace("_FB","").replace("_WS","").replace("_2","").replace("_"," ").title()
    name = ''.join([c for c in name if not c.isdigit()]).strip()
    return name if name else code.title()

def get_range_info(code):
    data = load_ranges()
    for srv in ["FACEBOOK", "WHATSAPP"]:
        if code.upper() in data.get(srv, {}):
            return {"id": data[srv][code.upper()], "panel": "voltx", "service": srv}
    # Nepal file-based
    if "NEPAL" in code.upper():
        return {"id": "file", "panel": "client", "service": "FILE"}
    return None

def get_number_from_file():
    possible_files = [NUMBERS_FILE, "numbers.txt", os.path.join(BASE_DIR, "numbers.txt"), "./numbers.txt", "/app/numbers.txt", "/app/data/numbers.txt"]
    file_to_use = None
    for pf in possible_files:
        if os.path.exists(pf):
            try:
                if os.path.getsize(pf) > 0:
                    with open(pf,'r') as tf:
                        lines = [l.strip() for l in tf if l.strip() and not l.strip().startswith("#")]
                        if lines:
                            file_to_use = pf
                            break
            except: continue
    if not file_to_use:
        return None
    try:
        with open(file_to_use, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
        if not lines:
            return None
        number = lines[0]
        with open(file_to_use, 'w') as f:
            f.write("\n".join(lines[1:]))
        print(f"[NEPAL FILE] Giving {number} from {file_to_use}")
        return number
    except Exception as e:
        print(f"[FILE ERR] {e}")
        return None

def client_login():
    global _logged_in
    try:
        if _logged_in: return True
        session.get(PANELS["client"]["login_url"], timeout=10)
        for payload in [
            {"username": PANELS["client"]["user"], "password": PANELS["client"]["pass"]},
            {"client_username": PANELS["client"]["user"], "client_password": PANELS["client"]["pass"]},
        ]:
            try:
                r = session.post(PANELS["client"]["login_url"], data=payload, timeout=10)
                if r.status_code == 200:
                    _logged_in = True
                    return True
            except: continue
        _logged_in = True
        return True
    except: return False

def get_otp_client(target_number):
    try:
        client_login()
        url = PANELS["client"]["url"]
        r = session.post(url, data={"search_number": target_number, "sSearch": target_number}, timeout=15)
        if "FB-" not in r.text:
            r = session.get(url, params={"search_number": target_number}, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 5: continue
            num_col = tds[2].get_text(strip=True)
            sms_col = tds[4].get_text(strip=True)
            if re.sub(r'\D','',target_number)[-7:] in re.sub(r'\D','',num_col):
                m = re.search(r'FB-(\d{4,8})', sms_col)
                if m: return m.group(1)
                m = re.search(r'#(\d{4,8})', sms_col)
                if m: return m.group(1)
                m = re.search(r'\b(\d{5,6})\b', sms_col)
                if m: return m.group(1)
        return None
    except Exception as e:
        print(f"[CLIENT OTP ERR] {e}")
        return None

def get_otp_voltx(number):
    try:
        num_digits = re.sub(r'\D', '', number)
        r = requests.get(PANELS["voltx"]["otp"], headers={"mauthapi": PANELS["voltx"]["key"]}, timeout=15)
        data = r.json()
        if data.get("meta", {}).get("code")!= 200:
            return None
        for item in data.get("data", {}).get("otps", []):
            en = re.sub(r'\D', '', str(item.get("number","")))
            if num_digits[-8:] not in en: continue
            msg = str(item.get("message",""))
            m = re.search(r'G-?(\d{4,8})|(\d{3}-\d{3})|(\d{4,8})', msg)
            if m:
                code = next((g for g in m.groups() if g), None)
                if code: return code.replace("-", "")
        return None
    except: return None

def create_order(service, country_code):
    # Nepal = file system
    if "NEPAL" in country_code.upper():
        print(f"[NEPAL MODE] {country_code} -> txt file")
        num = get_number_from_file()
        if num:
            return {"number": num, "id": f"client|{num}", "source": "client"}
        print("[NEPAL EMPTY] fallback to voltx if has range")

    info = get_range_info(country_code)
    if not info: return None
    if info["panel"] == "client":
        num = get_number_from_file()
        if num:
            return {"number": num, "id": f"client|{num}", "source": "client"}
        return None
    # Voltx for others
    panel = PANELS["voltx"]
    try:
        r = requests.post(panel["allocate"], headers={"mauthapi": panel["key"], "Content-Type": "application/json"}, json={"rid": info["id"]}, timeout=20)
        j = r.json()
        if j.get("meta", {}).get("code") == 200 and j.get("data"):
            return {"number": j["data"]["full_number"], "id": f"voltx|{j['data']['full_number']}", "source": "voltx"}
        return None
    except: return None

def get_otp(order_id):
    try:
        ptype, number = order_id.split("|", 1) if "|" in order_id else ("voltx", order_id)
        if ptype == "client":
            return get_otp_client(number)
        else:
            return get_otp_voltx(number)
    except: return None
