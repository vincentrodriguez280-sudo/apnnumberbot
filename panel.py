
import os
import requests
import time
import random
import re
from bs4 import BeautifulSoup

NEW_PANEL_URL = "http://151.80.19.204"
NEW_PANEL_LOGIN = f"{NEW_PANEL_URL}/ints/login"
NEW_PANEL_SIGNIN = f"{NEW_PANEL_URL}/ints/signin"

PANEL_151_USER = os.getenv("PANEL_151_USER", "")
PANEL_151_PASS = os.getenv("PANEL_151_PASS", "")

_session_151 = None
_orders_store = {}

def solve_math_captcha(text):
    try:
        # What is 2 + 1 = ? :
        m = re.search(r'What is (\d+)\s*([\+\-])\s*(\d+)\s*=\s*\?', text, re.I)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            ans = a + b if op == '+' else a - b
            print(f"[CAPTCHA] {a} {op} {b} = {ans}")
            return ans
        # Fallback 1 + 3 = ?
        m = re.search(r'(\d+)\s*([\+\-])\s*(\d+)\s*=\s*\?', text)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            if a < 100 and b < 100:
                ans = a + b if op == '+' else a - b
                print(f"[CAPTCHA] {a} {op} {b} = {ans}")
                return ans
        return None
    except:
        return None

def get_session_151():
    global _session_151
    try:
        if _session_151:
            try:
                test = _session_151.get(f"{NEW_PANEL_URL}/ints/", timeout=5)
                if test.status_code == 200 and "login" not in test.url.lower():
                    if "logout" in test.text.lower() or "dashboard" in test.text.lower():
                        return _session_151
            except:
                pass
        
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        
        print(f"[151] GET login page")
        if not PANEL_151_USER or not PANEL_151_PASS:
            print("[151] USER/PASS not set!")
            return None
        
        resp = session.get(NEW_PANEL_LOGIN, timeout=15)
        print(f"[151] Login page len={len(resp.text)}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Get CSRF
        csrf_token = None
        csrf_name = '_token'
        inp = soup.find('input', {'name': '_token'})
        if inp:
            csrf_token = inp.get('value')
        
        # Get captcha
        captcha_ans = solve_math_captcha(resp.text)
        print(f"[151] Captcha ans={captcha_ans} User={PANEL_151_USER}")
        
        # EXACT FIX: action=signin, fields username/password/capt/_token
        # From your log: inputs=[('username','text'),('password','password'),('capt','number')]
        
        # Build data with exact fields
        data = {}
        if csrf_token:
            data[csrf_name] = csrf_token
        data['username'] = PANEL_151_USER
        data['password'] = PANEL_151_PASS
        if captcha_ans is not None:
            data['capt'] = str(captcha_ans)
        
        print(f"[151] Trying POST to signin with {list(data.keys())}")
        
        # Try POST to signin endpoint
        for url in [NEW_PANEL_SIGNIN, NEW_PANEL_LOGIN, f"{NEW_PANEL_URL}/ints/signin", f"{NEW_PANEL_URL}/signin"]:
            try:
                r = session.post(url, data=data, timeout=15, allow_redirects=True, headers={
                    "Referer": NEW_PANEL_LOGIN,
                    "Origin": NEW_PANEL_URL,
                })
                print(f"[151] POST {url} -> status={r.status_code} final_url={r.url} len={len(r.text)}")
                
                if "login" not in r.url.lower():
                    if "logout" in r.text.lower() or "dashboard" in r.text.lower():
                        print(f"[151 LOGIN SUCCESS] via {url}")
                        _session_151 = session
                        return session
                else:
                    # Check if error message
                    if len(r.text) != 5604 and len(r.text) != 5605:
                        print(f"[151] Different len - maybe error: {r.text[:500]}")
                    # Look for error
                    if "invalid" in r.text.lower() or "wrong" in r.text.lower() or "error" in r.text.lower():
                        soup2 = BeautifulSoup(r.text, 'html.parser')
                        err = soup2.find(class_=re.compile('alert|error|danger', re.I))
                        if err:
                            print(f"[151 ERROR] {err.get_text()[:200]}")
            except Exception as e:
                print(f"[151 POST {url} ERR] {e}")
        
        print("[151 LOGIN FAILED]")
        return None
    except Exception as e:
        print(f"[151 ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def get_otp_from_panel(order_id):
    try:
        session = get_session_151()
        if not session:
            print("[OTP] No session")
            return None
        for endpoint in [f"{NEW_PANEL_URL}/ints/", f"{NEW_PANEL_URL}/ints/sms", f"{NEW_PANEL_URL}/ints/inbox"]:
            try:
                r = session.get(endpoint, timeout=15)
                if r.status_code != 200 or "login" in r.url.lower():
                    continue
                otps = re.findall(r'\b\d{4,8}\b', r.text)
                for otp in otps:
                    if 4 <= len(otp) <= 8:
                        pos = r.text.find(otp)
                        ctx = r.text[max(0,pos-80):pos+80].lower()
                        if any(k in ctx for k in ['code','otp','facebook','fb']):
                            print(f"[OTP FOUND] {otp}")
                            return otp
            except:
                continue
        return None
    except:
        return None

# ========== FILE NUMBERS ==========

def get_numbers_file_path(country_code):
    base = "/data" if os.path.exists("/data") else "."
    file_map = {
        "MOZAMBIQUE": "numbers_mozambique.txt",
        "MOZAMBIQUE_TT": "numbers_mozambique.txt",
        "MYANMAR": "numbers_myanmar.txt",
        "MYANMAR_TT": "numbers_myanmar.txt",
        "NEPAL": "numbers_nepal.txt",
        "NEPAL_FB": "numbers_nepal.txt",
        "CAMEROON": "numbers_cameroon.txt",
        "USA": "numbers_usa.txt",
        "BD": "numbers_bd.txt",
        "CAMBODIA": "numbers_cambodia.txt",
    }
    fname = file_map.get(country_code.upper(), "numbers_151.txt")
    candidates = [os.path.join(base, fname), os.path.join(base, "numbers_151.txt"), os.path.join(base, "numbers.txt"), fname, "numbers_151.txt", "numbers.txt"]
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
    return get_otp_from_panel(order_id)

print("[PANEL] FIXED FINAL - action=signin username/password/capt/_token")
print(f"[PANEL] User={PANEL_151_USER} PassSet={bool(PANEL_151_PASS)}")
