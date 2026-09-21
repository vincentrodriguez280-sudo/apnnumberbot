
import os
import requests
import time
import random
import re
import threading
from bs4 import BeautifulSoup

NEW_PANEL_URL = "http://151.80.19.204"
NEW_PANEL_LOGIN = f"{NEW_PANEL_URL}/ints/login"
NEW_PANEL_SIGNIN = f"{NEW_PANEL_URL}/ints/signin"

PANEL_151_USER = os.getenv("PANEL_151_USER", "")
PANEL_151_PASS = os.getenv("PANEL_151_PASS", "")

_session_151 = None
_session_time = 0
_session_lock = threading.Lock()
_last_hit = 0
_hit_lock = threading.Lock()
_orders_store = {}

def rate_limit():
    global _last_hit
    with _hit_lock:
        now = time.time()
        diff = now - _last_hit
        if diff < 8:
            wait = 8 - diff
            print(f"[RATE] Waiting {wait:.1f}s")
            time.sleep(wait)
        _last_hit = time.time()

def solve_captcha(text):
    try:
        m = re.search(r'What is (\d+)\s*([\+\-])\s*(\d+)', text, re.I)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            ans = a + b if op == '+' else a - b
            print(f"[CAPTCHA] {a} {op} {b} = {ans}")
            return ans
        return None
    except:
        return None

def get_session_151():
    global _session_151, _session_time
    with _session_lock:
        if _session_151 and (time.time() - _session_time < 1200):
            try:
                rate_limit()
                test = _session_151.get(f"{NEW_PANEL_URL}/ints/agent/SMSDashboard", timeout=15)
                if test.status_code == 200 and "login" not in test.url.lower():
                    print("[151] Using cached session")
                    return _session_151
            except:
                pass
        
        print("[151] New session - GET login")
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        
        if not PANEL_151_USER or not PANEL_151_PASS:
            return None
        
        # 5 retries with increasing wait
        resp = None
        for i in range(5):
            try:
                rate_limit()
                resp = session.get(NEW_PANEL_LOGIN, timeout=20)
                break
            except requests.exceptions.ConnectionError:
                wait = (i+1)*8
                print(f"[151] Conn refused GET retry {i+1}/5 wait {wait}s")
                if i == 4:
                    return None
                time.sleep(wait)
        
        if not resp:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf = None
        inp = soup.find('input', {'name': '_token'})
        if inp:
            csrf = inp.get('value')
        
        capt = solve_captcha(resp.text)
        print(f"[151] Capt={capt} User={PANEL_151_USER}")
        
        data = {}
        if csrf:
            data['_token'] = csrf
        data['username'] = PANEL_151_USER
        data['password'] = PANEL_151_PASS
        if capt is not None:
            data['capt'] = str(capt)
        
        for attempt in range(3):
            try:
                rate_limit()
                r = session.post(NEW_PANEL_SIGNIN, data=data, timeout=20, allow_redirects=True, headers={
                    "Referer": NEW_PANEL_LOGIN,
                    "Origin": NEW_PANEL_URL,
                })
                print(f"[151] POST signin -> {r.status_code} url={r.url} len={len(r.text)}")
                if "login" not in r.url.lower():
                    if any(x in r.text.lower() for x in ['logout','dashboard','sms']):
                        print("[151 LOGIN SUCCESS]")
                        _session_151 = session
                        _session_time = time.time()
                        return session
            except requests.exceptions.ConnectionError:
                print(f"[151] Conn refused POST retry {attempt+1}")
                time.sleep(10)
                continue
        
        print("[151 LOGIN FAILED]")
        return None

def get_otp_from_panel(order_id):
    try:
        delay = random.uniform(2, 8)
        print(f"[OTP] {order_id} delay {delay:.1f}s")
        time.sleep(delay)
        
        session = get_session_151()
        if not session:
            print("[OTP] No session - panel blocked, retry in 30s")
            return None
        
        rate_limit()
        print(f"[OTP] Fetch SMSDashboard for {order_id}")
        try:
            resp = session.get(f"{NEW_PANEL_URL}/ints/agent/SMSDashboard", timeout=25)
        except requests.exceptions.ConnectionError:
            print("[OTP] Conn refused on SMSDashboard - waiting 30s")
            time.sleep(30)
            return None
        
        if resp.status_code != 200 or "login" in resp.url.lower():
            print(f"[OTP] Session expired or status {resp.status_code}")
            with _session_lock:
                global _session_151
                _session_151 = None
            return None
        
        text = resp.text
        print(f"[OTP] Dashboard len={len(text)}")
        
        soup = BeautifulSoup(text, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows:
            rt = row.get_text()
            if any(k in rt.lower() for k in ['facebook','fb','code']):
                nums = re.findall(r'\b\d{4,8}\b', rt)
                for otp in nums:
                    if 4 <= len(otp) <= 8 and rt.count('+') < 3:
                        print(f"[OTP FOUND] {otp}")
                        return otp
        
        # Fallback
        all_nums = re.findall(r'\b\d{5,6}\b', text)
        for otp in all_nums:
            pos = text.find(otp)
            ctx = text[max(0,pos-200):pos+200].lower()
            if 'facebook' in ctx or 'verification' in ctx:
                print(f"[OTP FOUND] {otp} via ctx")
                return otp
        
        print("[OTP] Not found yet")
        return None
    except Exception as e:
        print(f"[OTP ERR] {e}")
        return None

# File numbers - 8 per click

def get_numbers_file_path(country_code):
    base = "/data" if os.path.exists("/data") else "."
    file_map = {
        "MOZAMBIQUE": "numbers_mozambique.txt",
        "MYANMAR": "numbers_myanmar.txt",
        "NEPAL": "numbers_nepal.txt",
        "NEPAL_FB": "numbers_nepal.txt",
        "CAMEROON": "numbers_cameroon.txt",
        "USA": "numbers_usa.txt",
        "BD": "numbers_bd.txt",
        "CAMBODIA": "numbers_cambodia.txt",
    }
    fname = file_map.get(country_code.upper(), "numbers_151.txt")
    candidates = [os.path.join(base, fname), os.path.join(base, "numbers_151.txt"), os.path.join(base, "numbers.txt"), fname, "numbers_151.txt"]
    for fpath in candidates:
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r') as file:
                    lines = [l.strip() for l in file.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
                if len(lines) > 0:
                    return fpath
            except:
                continue
    for fpath in candidates:
        if os.path.exists(fpath):
            return fpath
    return os.path.join(base, fname)

def create_order_from_file(service, country_code):
    try:
        fpath = get_numbers_file_path(country_code)
        if not os.path.exists(fpath):
            base = "/data" if os.path.exists("/data") else "."
            alt = os.path.join(base, "numbers_151.txt")
            if os.path.exists(alt):
                fpath = alt
            else:
                return None
        with open(fpath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
        if not lines:
            return None
        number = lines[0]
        remaining = lines[1:]
        with open(fpath, 'w') as fw:
            for ln in remaining:
                fw.write(ln + "\n")
        order_id = f"151_{int(time.time())}_{random.randint(1000,9999)}"
        result = {"number": number, "id": order_id, "country": country_code, "service": service, "panel": "151_file"}
        print(f"[FILE ORDER] {country_code} -> {number} | Remaining: {len(remaining)}")
        return result
    except Exception as e:
        print(f"[FILE ERR] {e}")
        return None

def get_all_countries(service):
    return ["NEPAL_FB", "MOZAMBIQUE", "MYANMAR", "CAMEROON", "USA", "BD", "NEPAL", "MOZAMBIQUE_TT", "MYANMAR_TT", "CAMBODIA"]

def get_display_name(country_code):
    names = {"NEPAL": "Nepal", "NEPAL_FB": "Nepal", "MOZAMBIQUE": "Mozambique", "MYANMAR": "Myanmar", "CAMEROON": "Cameroon", "USA": "USA", "BD": "Bangladesh", "CAMBODIA": "Cambodia"}
    return names.get(country_code.upper(), country_code.replace("_", " ").title())

def create_order(service, country_code):
    result = create_order_from_file(service, country_code)
    if result:
        _orders_store[result["id"]] = result
        return result
    return None

def get_otp(order_id):
    print(f"[GET OTP] {order_id}")
    otp = get_otp_from_panel(order_id)
    if otp:
        print(f"[GET OTP] Found: {otp}")
        return otp
    return None

print("[PANEL] FINAL - Rate limit 8s + Cached session")
print(f"[PANEL] User={PANEL_151_USER} PassSet={bool(PANEL_151_PASS)}")
