import requests, re, json, os, threading, time
from bs4 import BeautifulSoup

BASE_DIR = "/data" if os.path.exists("/data") else ("/app/data" if os.path.exists("/app/data") else ".")
try:
    os.makedirs(BASE_DIR, exist_ok=True)
except:
    pass
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
    },
    "had": {
        "url": "http://147.135.212.197/crapi/had/viewstats",
        "key": "QlFYRUpBUzRgY5Vrh2xifH6JmYmBmIVEfnZ1iEZtlVV1gWZaQ3-LYA==",
    },
    "ivasms": {
        "email": os.getenv("IVASMS_EMAIL", CFG.get("IVASMS_EMAIL", "ariyan548496@gmail.com")),
        "password": os.getenv("IVASMS_PASSWORD", CFG.get("IVASMS_PASSWORD", "")),
        "login_url": "https://www.ivasms.com/login",
        "live_url": "https://www.ivasms.com/portal/live/my_sms",
    }
}

session = requests.Session()
_logged_in = False
file_lock = threading.Lock()

_ivasms_session = requests.Session()
_ivasms_logged_in = False
_ivasms_cache = {"time": 0, "data": [], "lock": threading.Lock()}
_ivasms_last_fetch = {"time": 0}

def ivasms_login():
    global _ivasms_logged_in, _ivasms_session
    try:
        if _ivasms_logged_in:
            return True
        email = PANELS["ivasms"]["email"]
        password = PANELS["ivasms"]["password"]
        if not password:
            print("[IVASMS] No password set in env IVASMS_PASSWORD")
            return False
        r = _ivasms_session.get(PANELS["ivasms"]["login_url"], timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        csrf = None
        csrf_input = soup.find("input", {"name": "_token"}) or soup.find("input", {"name": "csrf_token"})
        if csrf_input:
            csrf = csrf_input.get("value")
        data = {"email": email, "password": password}
        if csrf:
            data["_token"] = csrf
        headers = {"User-Agent": "Mozilla/5.0", "Referer": PANELS["ivasms"]["login_url"]}
        r2 = _ivasms_session.post(PANELS["ivasms"]["login_url"], data=data, headers=headers, timeout=20)
        if "portal" in r2.url or "dashboard" in r2.text.lower() or "logout" in r2.text.lower():
            _ivasms_logged_in = True
            print(f"[IVASMS LOGIN] Success for {email}")
            return True
        if r2.status_code == 200 and len(r2.text) > 5000:
            _ivasms_logged_in = True
            return True
        print(f"[IVASMS LOGIN FAIL] {r2.status_code}")
        return False
    except Exception as e:
        print(f"[IVASMS LOGIN ERR] {e}")
        return False

def ivasms_fetch_live():
    try:
        if not ivasms_login():
            return []
        r = _ivasms_session.get(PANELS["ivasms"]["live_url"], timeout=20)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = []
        for tr in soup.select("table tbody tr"):
            row_text = tr.get_text(" ", strip=True)
            num_match = re.search(r'855\d{7,10}', row_text)
            if num_match:
                phone = num_match.group()
                rows.append({"number": phone, "raw": row_text, "time": time.time()})
        return rows
    except Exception as e:
        print(f"[IVASMS FETCH ERR] {e}")
        return []

def get_otp_ivasms(target_number):
    try:
        clean_target = re.sub(r'\D','', str(target_number))
        with _ivasms_cache["lock"]:
            now = time.time()
            if now - _ivasms_cache["time"] > 5 or now - _ivasms_last_fetch["time"] > 5:
                live_rows = ivasms_fetch_live()
                _ivasms_cache["data"] = live_rows
                _ivasms_cache["time"] = now
                _ivasms_last_fetch["time"] = now
            data = _ivasms_cache["data"]
            for item in data:
                num = re.sub(r'\D','', item.get("number",""))
                if clean_target[-7:] in num or num[-7:] in clean_target or clean_target == num:
                    raw = item.get("raw","")
                    m = re.search(r'FB-(\d{4,8})', raw)
                    if m:
                        print(f"[IVASMS OTP FOUND] {target_number} => {m.group(1)}")
                        return m.group(1)
                    m = re.search(r'#(\d{4,8})', raw)
                    if m:
                        return m.group(1)
                    m = re.search(r'\b(\d{5,6})\b', raw)
                    if m:
                        return m.group(1)
        return None
    except Exception as e:
        print(f"[IVASMS OTP ERR] {e}")
        return None

def load_ranges():
    data = {"FACEBOOK": {}, "WHATSAPP": {}, "TIKTOK": {}}
    for path in [RANGES_FILE, "ranges.json"]:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    raw = json.load(f)
                    for srv in ["FACEBOOK", "WHATSAPP", "TIKTOK"]:
                        for k, v in raw.get(srv, {}).items():
                            data[srv][k.upper()] = v
            except: pass
    return data

def get_all_countries(service="facebook"):
    svc = service.lower()
    if svc in ["whatsapp","ws"]:
        key = "WHATSAPP"
    elif svc in ["tiktok","tt"]:
        key = "TIKTOK"
    else:
        key = "FACEBOOK"
    base = list(load_ranges().get(key, {}).keys())
    if key == "FACEBOOK":
        base = [b for b in base if "NEPAL" not in b.upper()]
        base.insert(0, "NEPAL_FB")
        if "CAMBODIA" not in [x.upper() for x in base]:
            base.append("CAMBODIA")
    if key == "TIKTOK":
        return ["MOZAMBIQUE", "MYANMAR"]
    return base

def get_display_name(code):
    name = code.replace("_FB","").replace("_WS","").replace("_2","").replace("_"," ").title()
    name = ''.join([c for c in name if not c.isdigit()]).strip()
    return name if name else code.title()

def get_range_info(code):
    data = load_ranges()
    for srv in ["FACEBOOK", "WHATSAPP", "TIKTOK"]:
        if code.upper() in data.get(srv, {}):
            val = data[srv][code.upper()]
            if "CAMBODIA" in code.upper() or "855" in code:
                return {"id": val, "panel": "ivasms", "service": srv}
            if "HAD" in code.upper() or "BD" in code.upper() or "BANGLADESH" in code.upper() or "MOZAMBIQUE" in code.upper() or "MYANMAR" in code.upper():
                return {"id": val, "panel": "had", "service": srv}
            return {"id": val, "panel": "voltx", "service": srv}
    file_based = ["NEPAL", "MOZAMBIQUE", "BD", "BANGLADESH", "HAD", "MYANMAR", "CAMBODIA"]
    for fb in file_based:
        if fb in code.upper():
            if fb == "CAMBODIA":
                return {"id": "ivasms_file", "panel": "ivasms", "service": "FILE"}
            return {"id": "had_file", "panel": "had", "service": "FILE"}
    return None

def get_number_from_file(country_code=None):
    country = (country_code or "").upper()
    specific_files = []
    if "MOZAMBIQUE" in country:
        specific_files = [os.path.join(BASE_DIR, "numbers_mozambique.txt"), "numbers_mozambique.txt"]
    elif "MYANMAR" in country:
        specific_files = [os.path.join(BASE_DIR, "numbers_myanmar.txt"), "numbers_myanmar.txt"]
    elif "CAMBODIA" in country:
        specific_files = [os.path.join(BASE_DIR, "numbers_cambodia.txt"), "numbers_cambodia.txt", "numbers.txt"]
    elif "NEPAL" in country:
        specific_files = [os.path.join(BASE_DIR, "numbers_nepal.txt"), "numbers_nepal.txt"]
    general_files = [NUMBERS_FILE, "numbers.txt", os.path.join(BASE_DIR, "numbers.txt")]
    possible_files = specific_files + general_files
    with file_lock:
        file_to_use = None
        for pf in possible_files:
            if os.path.exists(pf):
                try:
                    if os.path.getsize(pf) > 0:
                        with open(pf,'r') as tf:
                            raw = tf.readlines()
                            content_lines = [l.strip() for l in raw if l.strip() and not l.strip().startswith("#")]
                            if content_lines:
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
            selected_number = None
            remaining = []
            if "CAMBODIA" in country:
                for idx, line in enumerate(lines):
                    if "855" in line:
                        selected_number = re.sub(r'[^0-9+]', '', line)
                        remaining = lines[:idx] + lines[idx+1:]
                        break
            if not selected_number:
                selected_number = lines[0]
                remaining = lines[1:]
            with open(file_to_use, 'w') as f:
                f.write("\n".join(remaining))
            print(f"[{country} FILE] Giving {selected_number} from {file_to_use} | {len(remaining)} left")
            return selected_number
        except Exception as e:
            print(f"[FILE ERR] {e}")
            return None

def client_login():
    global _logged_in, session
    try:
        if _logged_in: return True
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            session.get(PANELS["client"]["login_url"], headers=headers, timeout=10)
        except: pass
        for payload in [
            {"username": PANELS["client"]["user"], "password": PANELS["client"]["pass"]},
        ]:
            try:
                r = session.post(PANELS["client"]["login_url"], data=payload, headers=headers, timeout=15)
                if r.status_code == 200:
                    _logged_in = True
                    return True
            except: continue
        _logged_in = True
        return True
    except:
        return False

def get_otp_client(target_number):
    try:
        client_login()
        url = PANELS["client"]["url"]
        r = session.post(url, data={"search_number": target_number}, timeout=20)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 3: continue
            num_col = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            sms_col = tds[4].get_text(strip=True) if len(tds) > 4 else tr.get_text()
            clean_num = re.sub(r'\D','',num_col)
            clean_target = re.sub(r'\D','',target_number)
            if clean_target[-7:] in clean_num:
                m = re.search(r'FB-(\d{4,8})', sms_col)
                if m: return m.group(1)
                m = re.search(r'#(\d{4,8})', sms_col)
                if m: return m.group(1)
                m = re.search(r'\b(\d{5,6})\b', sms_col)
                if m: return m.group(1)
        return None
    except:
        return None

_had_cache = {"time": 0, "data": [], "lock": threading.Lock()}
_had_last_request = {"time": 0}

def get_otp_had(target_number):
    try:
        token = PANELS["had"]["key"]
        url = PANELS["had"]["url"]
        clean_target = re.sub(r'\D','', str(target_number))
        params_specific = {"token": token, "filternum": clean_target, "records": 20}
        r = requests.get(url, params=params_specific, timeout=20)
        j = r.json()
        data = j.get("data", [])
        for item in data:
            num = str(item.get("num", ""))
            msg = str(item.get("message", ""))
            clean_num = re.sub(r'\D','', num)
            if clean_target[-8:] in clean_num:
                for pat in [r'FB-(\d{4,8})', r'verification code (\d{4,8})', r'#(\d{4,8})', r'\b(\d{6})\b']:
                    m = re.search(pat, msg, re.IGNORECASE)
                    if m:
                        return m.group(1)
        return None
    except:
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
    file_countries = ["NEPAL", "MOZAMBIQUE", "BD", "BANGLADESH", "HAD", "MYANMAR", "CAMBODIA"]
    upper_cc = country_code.upper()
    is_file_based = any(fb in upper_cc for fb in file_countries)
    if is_file_based:
        num = get_number_from_file(country_code)
        if num:
            ptype = "ivasms" if "CAMBODIA" in upper_cc else "had"
            if "NEPAL" in upper_cc: ptype = "client"
            return {"number": num, "id": f"{ptype}|{num}", "source": ptype}
    info = get_range_info(country_code)
    if not info: return None
    if info["panel"] == "ivasms":
        num = get_number_from_file(country_code)
        if num:
            return {"number": num, "id": f"ivasms|{num}", "source": "ivasms"}
        return None
    if info["panel"] == "client":
        num = get_number_from_file(country_code)
        if num:
            return {"number": num, "id": f"client|{num}", "source": "client"}
        return None
    if info["panel"] == "had":
        num = get_number_from_file(country_code)
        if num:
            return {"number": num, "id": f"had|{num}", "source": "had"}
        return None
    panel = PANELS["voltx"]
    for attempt in range(3):
        try:
            r = requests.post(panel["allocate"], headers={"mauthapi": panel["key"], "Content-Type": "application/json"}, json={"rid": info["id"]}, timeout=20)
            j = r.json()
            if j.get("meta", {}).get("code") == 200 and j.get("data"):
                full_num = j["data"]["full_number"]
                return {"number": full_num, "id": f"voltx|{full_num}", "source": "voltx"}
        except:
            time.sleep(1)
            continue
    return None

def get_otp(order_id):
    try:
        ptype, number = order_id.split("|", 1) if "|" in order_id else ("voltx", order_id)
        if ptype == "client":
            return get_otp_client(number)
        elif ptype == "had":
            return get_otp_had(number)
        elif ptype == "ivasms":
            return get_otp_ivasms(number)
        else:
            return get_otp_voltx(number)
    except Exception as e:
        print(f"[GET OTP ERR] {e}")
        return None
