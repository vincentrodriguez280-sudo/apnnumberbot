import requests, re, json, os, threading
from bs4 import BeautifulSoup

BASE_DIR = "/data" if os.path.exists("/data") else ("/app/data" if os.path.exists("/app/data") else ".")
# Auto create for Railway volume
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
        "key": "QlBYSkVBUzRdVmdkV293WGCCVFZgg4CJh0-HYoVthGuHaIWJdJOSQQ==",
        "token": "QlBYSkVBUzRdVmdkV293WGCCVFZgg4CJh0-HYoVthGuHaIWJdJOSQQ==",
    }
}

session = requests.Session()
_logged_in = False
file_lock = threading.Lock()

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
    elif svc in ["tiktok","tt","tik_tok"]:
        key = "TIKTOK"
    else:
        key = "FACEBOOK"
    base = list(load_ranges().get(key, {}).keys())
    # Always add Nepal for FB from file - only once
    if key == "FACEBOOK":
        base = [b for b in base if "NEPAL" not in b.upper()]
        base.insert(0, "NEPAL_FB")
    # For TikTok - ONLY Mozambique and Myanmar as requested
    if key == "TIKTOK":
        # Only 2 countries: Mozambique and Myanmar - both file-based HAD panel
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
            if isinstance(val, str) and val.lower().startswith("had_"):
                return {"id": val, "panel": "had", "service": srv}
            if "HAD" in code.upper() or "BD" in code.upper() or "BANGLADESH" in code.upper() or "MOZAMBIQUE" in code.upper() or "NEPAL" in code.upper():
                return {"id": val, "panel": "had", "service": srv}
            return {"id": val, "panel": "voltx", "service": srv}
    # File-based countries - all go to HAD panel with file numbers
    file_based = ["NEPAL", "MOZAMBIQUE", "BD", "BANGLADESH", "HAD", "MYANMAR"]
    upper_code = code.upper()
    for fb in file_based:
        if fb in upper_code:
            return {"id": "had_file", "panel": "had", "service": "FILE"}
    return None

def get_number_from_file(country_code=None):
    """
    Country-aware file reading
    - MOZAMBIQUE -> numbers_mozambique.txt (258...)
    - MYANMAR -> numbers_myanmar.txt (95...)
    - Fallback -> numbers.txt
    """
    # Determine country-specific files
    country = (country_code or "").upper()
    specific_files = []
    
    if "MOZAMBIQUE" in country:
        specific_files = [
            os.path.join(BASE_DIR, "numbers_mozambique.txt"),
            os.path.join(BASE_DIR, "numbers_MOZAMBIQUE.txt"),
            "numbers_mozambique.txt",
            "./numbers_mozambique.txt",
            "/data/numbers_mozambique.txt",
        ]
    elif "MYANMAR" in country:
        specific_files = [
            os.path.join(BASE_DIR, "numbers_myanmar.txt"),
            os.path.join(BASE_DIR, "numbers_MYANMAR.txt"),
            "numbers_myanmar.txt",
            "./numbers_myanmar.txt",
            "/data/numbers_myanmar.txt",
        ]
    elif "NEPAL" in country:
        specific_files = [
            os.path.join(BASE_DIR, "numbers_nepal.txt"),
            "numbers_nepal.txt",
        ]
    
    # General files as fallback
    general_files = [NUMBERS_FILE, "numbers.txt", os.path.join(BASE_DIR, "numbers.txt"), "./numbers.txt", "/app/numbers.txt", "/app/data/numbers.txt"]
    
    # Try specific files first, then general
    possible_files = specific_files + general_files
    
    with file_lock:
        file_to_use = None
        for pf in possible_files:
            if os.path.exists(pf):
                try:
                    if os.path.getsize(pf) > 0:
                        with open(pf,'r') as tf:
                            content_lines = [l.strip() for l in tf.readlines() if l.strip() and not l.strip().startswith("#")]
                            if content_lines:
                                # For general file, try to filter by prefix if country specified
                                if pf in general_files and country:
                                    # Filter by country prefix for general file
                                    if "MOZAMBIQUE" in country:
                                        filtered = [l for l in content_lines if l.startswith("258") or "258" in l]
                                        if filtered:
                                            file_to_use = pf
                                            break
                                    elif "MYANMAR" in country:
                                        filtered = [l for l in content_lines if l.startswith("95") or l.startswith("+95") or "959" in l]
                                        if filtered:
                                            file_to_use = pf
                                            break
                                    else:
                                        file_to_use = pf
                                        break
                                else:
                                    file_to_use = pf
                                    break
                except: continue
        
        if not file_to_use:
            print(f"[FILE] No file found for {country_code} - tried {possible_files[:2]}")
            return None
        
        try:
            with open(file_to_use, 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
            if not lines:
                return None
            
            # If general file and country specified, pick matching prefix
            selected_number = None
            remaining = []
            
            if file_to_use in general_files and country:
                if "MOZAMBIQUE" in country:
                    for idx, line in enumerate(lines):
                        if line.startswith("258"):
                            selected_number = line
                            remaining = lines[:idx] + lines[idx+1:]
                            break
                elif "MYANMAR" in country:
                    for idx, line in enumerate(lines):
                        clean = line.replace("+","")
                        if clean.startswith("95") or clean.startswith("959"):
                            selected_number = line
                            remaining = lines[:idx] + lines[idx+1:]
                            break
            
            # If no filtered number found, take first
            if not selected_number:
                selected_number = lines[0]
                remaining = lines[1:]
            
            with open(file_to_use, 'w') as f:
                f.write("\n".join(remaining))
            
            print(f"[{country} FILE] Giving {selected_number} from {file_to_use} | {len(remaining)} left")
            return selected_number
            
        except Exception as e:
            print(f"[FILE ERR] {e} for {country_code}")
            return None

def client_login():
    global _logged_in, session
    try:
        if _logged_in: 
            # Test if session still valid
            try:
                session.get(PANELS["client"]["login_url"], timeout=5)
            except:
                _logged_in = False
                session = requests.Session()
        if _logged_in: return True
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            session.get(PANELS["client"]["login_url"], headers=headers, timeout=10)
        except: pass
        for payload in [
            {"username": PANELS["client"]["user"], "password": PANELS["client"]["pass"]},
            {"client_username": PANELS["client"]["user"], "client_password": PANELS["client"]["pass"]},
            {"user": PANELS["client"]["user"], "pass": PANELS["client"]["pass"]},
        ]:
            try:
                r = session.post(PANELS["client"]["login_url"], data=payload, headers=headers, timeout=15)
                if r.status_code == 200 and ("dashboard" in r.text.lower() or "logout" in r.text.lower() or "smscdr" in r.text.lower() or len(r.text) > 500):
                    _logged_in = True
                    print("[CLIENT LOGIN] Success")
                    return True
            except Exception as e:
                print(f"[LOGIN TRY ERR] {e}")
                continue
        _logged_in = True
        return True
    except Exception as e:
        print(f"[CLIENT LOGIN ERR] {e}")
        return False

def get_otp_client(target_number):
    global session, _logged_in
    import time
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    for attempt in range(3):
        try:
            client_login()
            url = PANELS["client"]["url"]
            # Try POST first
            try:
                r = session.post(url, data={"search_number": target_number, "sSearch": target_number}, headers=headers, timeout=20)
            except Exception as e:
                print(f"[CLIENT POST ERR attempt {attempt+1}] {e}")
                # Recreate session on connection error
                session = requests.Session()
                _logged_in = False
                time.sleep(2)
                continue

            if "FB-" not in r.text and len(r.text) < 1000:
                # Try GET
                try:
                    r = session.get(url, params={"search_number": target_number}, headers=headers, timeout=20)
                except Exception as e:
                    print(f"[CLIENT GET ERR attempt {attempt+1}] {e}")
                    session = requests.Session()
                    _logged_in = False
                    time.sleep(2)
                    continue

            text = r.text
            if not text or len(text) < 100:
                print(f"[CLIENT EMPTY RESP attempt {attempt+1}] len={len(text)}")
                time.sleep(1)
                continue

            soup = BeautifulSoup(text, 'html.parser')
            found = False
            for tr in soup.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) < 3: continue
                try:
                    num_col = tds[2].get_text(strip=True) if len(tds) > 2 else ""
                    sms_col = tds[4].get_text(strip=True) if len(tds) > 4 else tr.get_text()
                except: continue
                clean_num = re.sub(r'\D','',num_col)
                clean_target = re.sub(r'\D','',target_number)
                if not clean_num: clean_num = re.sub(r'\D','', tr.get_text())
                if clean_target[-7:] in clean_num or clean_num[-7:] in clean_target or clean_target in clean_num:
                    found = True
                    m = re.search(r'FB-(\d{4,8})', sms_col)
                    if m: 
                        print(f"[CLIENT OTP FOUND] {target_number} => {m.group(1)}")
                        return m.group(1)
                    m = re.search(r'#(\d{4,8})', sms_col)
                    if m: return m.group(1)
                    m = re.search(r'\b(\d{5,6})\b', sms_col)
                    if m: return m.group(1)
            # If not found in table, try regex on whole page
            if not found:
                m = re.search(r'FB-(\d{4,8})', text)
                if m and target_number[-4:] in text:
                    return m.group(1)
            return None
        except Exception as e:
            err_str = str(e)
            if "RemoteDisconnected" in err_str or "Connection aborted" in err_str or "ConnectionReset" in err_str:
                print(f"[CLIENT OTP RETRY {attempt+1}/3] {e} - recreating session")
                session = requests.Session()
                _logged_in = False
                time.sleep(2 + attempt)
                continue
            print(f"[CLIENT OTP ERR] {e}")
            return None
    print(f"[CLIENT OTP FAIL] {target_number} after 3 attempts")
    return None

# ===== HAD PANEL - RATE LIMIT FIXED =====
_had_cache = {"time": 0, "data": [], "lock": threading.Lock()}
_had_last_request = {"time": 0}

def get_otp_had(target_number):
    """
    Fixed HAD panel with rate limit handling
    API: http://147.135.212.197/crapi/had/viewstats?token=XXX&records=1000
    Error: "Error, you've accessed this site too many times. Try again in 3 seconds."
    Fix: Global cache + 4 sec minimum interval + retry on rate limit
    """
    import time
    try:
        token = PANELS["had"].get("key") or PANELS["had"].get("token")
        if not token:
            for p in [CONFIG_FILE, "config.json", os.path.join(BASE_DIR, "config.json")]:
                if os.path.exists(p):
                    try:
                        with open(p,'r') as f:
                            cfg = json.load(f)
                            if cfg.get("HAD_API_KEY"):
                                token = cfg["HAD_API_KEY"]
                                break
                    except: pass
        if not token or token == "YOUR_API_KEY":
            print("[HAD] No API key set")
            return None
        
        url = PANELS["had"]["url"]
        params = {"token": token, "records": 1000}
        
        # ===== RATE LIMIT PROTECTION - GLOBAL LOCK =====
        with _had_cache["lock"]:
            now = time.time()
            # If cache is fresh (< 8 seconds), use cached data
            if _had_cache["data"] and (now - _had_cache["time"] < 8):
                print(f"[HAD CACHE] Using cached data ({int(now - _had_cache['time'])}s old) for {target_number}")
                data = _had_cache["data"]
            else:
                # Enforce minimum 4 seconds between API calls
                time_since_last = now - _had_last_request["time"]
                if time_since_last < 4:
                    sleep_time = 4 - time_since_last
                    print(f"[HAD RATE] Waiting {sleep_time:.1f}s to avoid rate limit...")
                    time.sleep(sleep_time)
                
                # Fetch with retry on rate limit
                for attempt in range(3):
                    try:
                        print(f"[HAD FETCH] Attempt {attempt+1}/3 for {target_number}")
                        r = requests.get(url, params=params, timeout=20)
                        _had_last_request["time"] = time.time()
                        
                        # Check for rate limit error (plain text)
                        if "too many times" in r.text.lower() or "try again in" in r.text.lower():
                            print(f"[HAD RATE LIMIT] Hit rate limit, waiting 4 sec... (attempt {attempt+1})")
                            time.sleep(4)
                            continue
                        
                        try:
                            j = r.json()
                        except:
                            # If not JSON but contains error text
                            if "error" in r.text.lower() or "too many" in r.text.lower():
                                print(f"[HAD] Rate limit text: {r.text[:200]} - waiting 4s")
                                time.sleep(4)
                                continue
                            print(f"[HAD] Invalid JSON: {r.text[:200]}")
                            return None
                        
                        if not j.get("status"):
                            print(f"[HAD] API status false: {j}")
                            # Check if it's rate limit in JSON
                            if "too many" in str(j).lower():
                                time.sleep(4)
                                continue
                            return None
                        
                        data = j.get("data", [])
                        # Update cache
                        _had_cache["data"] = data
                        _had_cache["time"] = time.time()
                        print(f"[HAD] Fetched {len(data)} messages, cached")
                        break
                        
                    except Exception as e:
                        print(f"[HAD FETCH ERR] Attempt {attempt+1}: {e}")
                        time.sleep(2)
                        continue
                else:
                    # All attempts failed, try using stale cache if available
                    if _had_cache["data"]:
                        print("[HAD] All fetch attempts failed, using stale cache")
                        data = _had_cache["data"]
                    else:
                        return None
        
        # ===== SEARCH IN DATA (outside lock for speed) =====
        if not data:
            return None
        
        clean_target = re.sub(r'\D','', str(target_number))
        
        for item in data:
            num = str(item.get("number", "") or item.get("num", "") or item.get("phone", ""))
            msg = str(item.get("message", "") or item.get("msg", "") or item.get("text", ""))
            
            clean_num = re.sub(r'\D','', num)
            if not clean_num:
                continue
            
            if clean_target[-8:] in clean_num or clean_num[-8:] in clean_target or clean_target == clean_num or clean_target[-10:] in clean_num:
                patterns = [
                    r'OTP code is (\d{4,8})',
                    r'code is (\d{4,8})',
                    r'FB-(\d{4,8})',
                    r'G-(\d{4,8})',
                    r'#(\d{4,8})',
                    r'\b(\d{6})\b',
                    r'\b(\d{5})\b',
                    r'\b(\d{4})\b',
                    r'(\d{3}-\d{3})',
                ]
                for pat in patterns:
                    m = re.search(pat, msg, re.IGNORECASE)
                    if m:
                        code = m.group(1).replace("-", "")
                        print(f"[HAD OTP FOUND] {target_number} => {code}")
                        return code
                
                m = re.search(r'(\d{4,8})', msg)
                if m:
                    return m.group(1)
        
        return None
    except Exception as e:
        print(f"[HAD OTP ERR] {e}")
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
    # All file-based countries - Nepal, Mozambique, BD etc -> HAD panel with file numbers
    file_countries = ["NEPAL", "MOZAMBIQUE", "BD", "BANGLADESH", "HAD", "MYANMAR"]
    upper_cc = country_code.upper()
    is_file_based = any(fb in upper_cc for fb in file_countries)
    
    if is_file_based:
        panel_name = "HAD" if "HAD" in upper_cc or "BD" in upper_cc or "BANGLADESH" in upper_cc or "MOZAMBIQUE" in upper_cc or "MYANMAR" in upper_cc else "CLIENT"
        print(f"[{panel_name} FILE MODE] {country_code} ({service}) -> file for {country_code}")
        num = get_number_from_file(country_code)
        if num:
            # Use had for BD/MOZAMBIQUE/MYANMAR, client for NEPAL
            ptype = "had" if any(x in upper_cc for x in ["BD", "BANGLADESH", "MOZAMBIQUE", "HAD", "MYANMAR"]) else "client"
            return {"number": num, "id": f"{ptype}|{num}", "source": ptype}
        print(f"[FILE EMPTY] No numbers for {country_code} - checked country-specific file")
        # Fallback
        num = get_number_from_file(country_code)
        if num:
            ptype = "had" if any(x in upper_cc for x in ["BD", "BANGLADESH", "MOZAMBIQUE", "HAD", "MYANMAR"]) else "client"
            return {"number": num, "id": f"{ptype}|{num}", "source": ptype}

    info = get_range_info(country_code)
    if not info: return None
    if info["panel"] == "client":
        num = get_number_from_file(country_code)
        if num:
            return {"number": num, "id": f"client|{num}", "source": "client"}
        return None
    if info["panel"] == "had":
        # HAD panel uses file for number, API for OTP
        num = get_number_from_file(country_code)
        if num:
            return {"number": num, "id": f"had|{num}", "source": "had"}
        # If no file, return None to show out of stock
        print(f"[HAD] No numbers in file for {country_code}")
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
        elif ptype == "had":
            return get_otp_had(number)
        else:
            return get_otp_voltx(number)
    except Exception as e:
        print(f"[GET OTP ERR] {e}")
        return None
