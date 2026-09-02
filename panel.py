import requests, re, json, os
from bs4 import BeautifulSoup

BASE_DIR = "/app/data" if os.path.exists("/app/data") else "."
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
NUMBERS_FILE = os.path.join(BASE_DIR, "numbers.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Load config for Polaszone panel
CFG = {}
if os.path.exists("config.json"):
    try:
        with open("config.json","r") as f: CFG=json.load(f)
    except: pass
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE,"r") as f: CFG.update(json.load(f))
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

# -------- NUMBER FILE (CLIENT PANEL - NEW) --------
def get_number_from_file():
    # Github + Railway support - 2 jayga check korbe
    possible_files = [NUMBERS_FILE, "numbers.txt", os.path.join(BASE_DIR, "numbers.txt"), "./numbers.txt", "/app/numbers.txt"]
    file_to_use = None
    for pf in possible_files:
        if os.path.exists(pf):
            try:
                if os.path.getsize(pf) > 0:
                    with open(pf,'r') as tf:
                        content = [l.strip() for l in tf.readlines() if l.strip() and not l.strip().startswith("#")]
                        if content:
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
        # Baki number gula rekhe dao
        with open(file_to_use, 'w') as f:
            f.write("\n".join(lines[1:]))
        print(f"[CLIENT FILE] Using {file_to_use} -> Giving {number}")
        return number
    except Exception as e:
        print(f"[FILE READ ERR] {e}")
        return None

# -------- CLIENT PANEL LOGIN + OTP (NEW) --------
def client_login():
    global _logged_in
    try:
        if _logged_in: return True
        session.get(PANELS["client"]["login_url"], timeout=10)
        for payload in [
            {"username": PANELS["client"]["user"], "password": PANELS["client"]["pass"]},
            {"client_username": PANELS["client"]["user"], "client_password": PANELS["client"]["pass"]},
            {"user": PANELS["client"]["user"], "pass": PANELS["client"]["pass"]},
            {"email": PANELS["client"]["user"], "password": PANELS["client"]["pass"]},
        ]:
            try:
                r = session.post(PANELS["client"]["login_url"], data=payload, timeout=10)
                if r.status_code == 200:
                    _logged_in = True
                    return True
            except: continue
        _logged_in = True
        return True
    except Exception as e:
        print(f"[CLIENT LOGIN ERR] {e}")
        return False

def get_otp_client(target_number):
    try:
        client_login()
        url = PANELS["client"]["url"]
        data = {"search_number": target_number, "sSearch": target_number}
        r = session.post(url, data=data, timeout=15)
        if "FB-" not in r.text:
            r = session.get(url, params={"search_number": target_number}, timeout=15)
        
        text = r.text
        soup = BeautifulSoup(text, 'html.parser')
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 5: continue
            num_col = tds[2].get_text(strip=True)
            sms_col = tds[4].get_text(strip=True)
            clean_num = re.sub(r'\D','',num_col)
            clean_target = re.sub(r'\D','',target_number)
            if clean_target[-7:] in clean_num or clean_num[-7:] in clean_target:
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
            if num_digits[-8:] not in en:
                continue
            msg = str(item.get("message",""))
            m = re.search(r'G-?(\d{4,8})|(\d{3}-\d{3})|(\d{4,8})', msg)
            if m:
                code = next((g for g in m.groups() if g), None)
                if code:
                    clean = code.replace("-", "")
                    print(f"[VOLTX OTP FOUND] {number} => {clean}")
                    return clean
        return None
    except Exception as e:
        print(f"[VOLTX OTP ERR] {e}")
        return None

# -------- MAIN FUNCTIONS USED BY BOT --------
def create_order(service, country_code):
    # Check which country should use file
    client_countries = CFG.get("CLIENT_COUNTRIES", ["NEPAL", "NEPAL_FB"])
    # Normalize: allow NEPAL to match NEPAL_FB, NEPAL_WS etc
    code_upper = country_code.upper()
    use_file = False
    for c in client_countries:
        c_up = c.upper()
        if c_up == code_upper or c_up in code_upper or code_upper.startswith(c_up.replace("_FB","").replace("_WS","")):
            # Also check base name: NEPAL matches NEPAL_FB
            if c_up.split("_")[0] == code_upper.split("_")[0]:
                use_file = True
                break
            if c_up == code_upper:
                use_file = True
                break
    # If exact match logic
    if code_upper in [x.upper() for x in client_countries]:
        use_file = True

    if use_file:
        print(f"[CLIENT MODE] {country_code} -> Trying numbers.txt")
        num_from_file = get_number_from_file()
        if num_from_file:
            return {"number": num_from_file, "id": f"client|{num_from_file}", "source": "client"}
        else:
            print(f"[CLIENT EMPTY] {country_code} file empty, falling back to voltx")
            # If file empty, fallback to voltx

    # STEP 2: Voltx system for all other countries
    info = get_range_info(country_code)
    if not info: 
        return None
    panel = PANELS[info["panel"]]
    try:
        r = requests.post(panel["allocate"], headers={"mauthapi": panel["key"], "Content-Type": "application/json"}, json={"rid": info["id"]}, timeout=20)
        j = r.json()
        if j.get("meta", {}).get("code") == 200 and j.get("data"):
            return {"number": j["data"]["full_number"], "id": f"{info['panel']}|{j['data']['full_number']}", "source": "voltx"}
        print(f"[OUT] {country_code} {j}")
        return None
    except Exception as e:
        print(f"[CREATE ERR] {e}")
        return None

def get_otp(order_id):
    try:
        ptype, number = order_id.split("|", 1) if "|" in order_id else ("voltx", order_id)
        if ptype == "client":
            return get_otp_client(number)
        else:
            return get_otp_voltx(number)
    except Exception as e:
        print(f"[OTP ERR] {e}")
        return None
