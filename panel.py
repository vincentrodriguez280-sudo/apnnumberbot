
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
_session_time = 0

def solve_math_captcha(text):
    try:
        m = re.search(r'What is (\d+)\s*([\+\-])\s*(\d+)\s*=\s*\?', text, re.I)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            return a + b if op == '+' else a - b
        m = re.search(r'(\d+)\s*([\+\-])\s*(\d+)\s*=\s*\?', text)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            if a < 100 and b < 100:
                return a + b if op == '+' else a - b
        return None
    except:
        return None

def get_session_151():
    global _session_151, _session_time
    try:
        # Use cached session if < 10 min old
        if _session_151 and (time.time() - _session_time < 600):
            try:
                test = _session_151.get(f"{NEW_PANEL_URL}/ints/agent/SMSDashboard", timeout=8)
                if test.status_code == 200 and "login" not in test.url.lower():
                    return _session_151
            except:
                pass
        
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        
        print(f"[151] GET login")
        resp = session.get(NEW_PANEL_LOGIN, timeout=15)
        print(f"[151] Login page len={len(resp.text)}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        csrf_token = None
        inp = soup.find('input', {'name': '_token'})
        if inp:
            csrf_token = inp.get('value')
        
        captcha_ans = solve_math_captcha(resp.text)
        print(f"[151] Captcha={captcha_ans} User={PANEL_151_USER}")
        
        data = {}
        if csrf_token:
            data['_token'] = csrf_token
        data['username'] = PANEL_151_USER
        data['password'] = PANEL_151_PASS
        if captcha_ans is not None:
            data['capt'] = str(captcha_ans)
        
        # POST to signin - this is the correct endpoint per your log
        for url in [NEW_PANEL_SIGNIN, f"{NEW_PANEL_URL}/ints/signin"]:
            try:
                r = session.post(url, data=data, timeout=15, allow_redirects=True, headers={
                    "Referer": NEW_PANEL_LOGIN,
                    "Origin": NEW_PANEL_URL,
                })
                print(f"[151] POST {url} -> {r.status_code} final={r.url} len={len(r.text)}")
                if "login" not in r.url.lower():
                    if "logout" in r.text.lower() or "dashboard" in r.text.lower() or "sms" in r.text.lower():
                        print(f"[151 LOGIN SUCCESS] {url}")
                        _session_151 = session
                        _session_time = time.time()
                        return session
            except Exception as e:
                print(f"[151 POST ERR] {e}")
                time.sleep(1)
        
        print("[151 LOGIN FAILED]")
        return None
    except Exception as e:
        print(f"[151 ERR] {e}")
        return None

def get_otp_from_panel(order_id):
    try:
        session = get_session_151()
        if not session:
            print("[OTP] No session")
            return None
        
        # Your log shows dashboard is /ints/agent/SMSDashboard - this is where OTP is!
        endpoints = [
            f"{NEW_PANEL_URL}/ints/agent/SMSDashboard",
            f"{NEW_PANEL_URL}/ints/agent/SMSDashboard?search=",
            f"{NEW_PANEL_URL}/ints/",
            f"{NEW_PANEL_URL}/ints/sms",
            f"{NEW_PANEL_URL}/ints/inbox",
        ]
        
        for endpoint in endpoints:
            try:
                print(f"[OTP] Fetching {endpoint}")
                resp = session.get(endpoint, timeout=15)
                if resp.status_code != 200:
                    print(f"[OTP] {endpoint} status={resp.status_code}")
                    continue
                if "login" in resp.url.lower():
                    print(f"[OTP] Redirected to login from {endpoint}")
                    continue
                
                text = resp.text
                # Debug len
                print(f"[OTP] {endpoint} len={len(text)}")
                
                # Look for OTP - Facebook code is usually 5-8 digits
                # Pattern: Look for numbers near "Facebook" or "code"
                
                # Try to find in table rows
                soup = BeautifulSoup(text, 'html.parser')
                
                # Method 1: Look for OTP in table cells
                # SMSDashboard likely has table with Number and Message
                rows = soup.find_all('tr')
                for row in rows:
                    row_text = row.get_text()
                    # Check if row contains facebook or code
                    if any(k in row_text.lower() for k in ['facebook', 'fb', 'code', 'otp', 'verification']):
                        # Find 4-8 digit number in row
                        otps = re.findall(r'\b\d{4,8}\b', row_text)
                        for otp in otps:
                            # Avoid numbers that are part of phone number (longer context)
                            if 4 <= len(otp) <= 8:
                                print(f"[OTP FOUND] {otp} in row: {row_text[:100]}")
                                return otp
                
                # Method 2: Regex with context
                # Find patterns like "Your Facebook code is 123456"
                patterns = [
                    r'Facebook.*?code.*?is.*?(\d{4,8})',
                    r'FB.*?code.*?is.*?(\d{4,8})',
                    r'code.*?is.*?(\d{4,8})',
                    r'(\d{4,8})\s*is your.*?(?:facebook|code)',
                ]
                
                for pat in patterns:
                    matches = re.findall(pat, text, re.I)
                    for m in matches:
                        otp = m if isinstance(m, str) else m[0] if isinstance(m, tuple) else str(m)
                        if 4 <= len(otp) <= 8:
                            print(f"[OTP FOUND] {otp} via pattern {pat[:30]}")
                            return otp
                
                # Method 3: Any 5-6 digit number near facebook keyword (within 100 chars)
                all_numbers = re.findall(r'\b\d{4,8}\b', text)
                for otp in all_numbers:
                    pos = text.find(otp)
                    ctx = text[max(0, pos-150):pos+150].lower()
                    if any(k in ctx for k in ['facebook', 'fb', 'code', 'otp', 'verification']):
                        # Make sure it's not part of phone number
                        # Phone numbers are 10+ digits, we already filter 4-8
                        print(f"[OTP FOUND] {otp} via context search")
                        return otp
                
            except requests.exceptions.ConnectionError as e:
                print(f"[OTP] Connection refused to {endpoint} - panel may be rate limiting, retrying...")
                time.sleep(2)
                continue
            except Exception as e:
                print(f"[OTP] {endpoint} ERR: {e}")
                continue
        
        print("[OTP] Not found in any endpoint")
        return None
    except Exception as e:
        print(f"[OTP ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

# ========== FILE NUMBERS - 8 per click ==========

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
    print(f"[GET OTP] {order_id}")
    otp = get_otp_from_panel(order_id)
    if otp:
        print(f"[GET OTP] Found: {otp}")
        return otp
    return None

print("[PANEL] FINAL WORKING - Login fixed to signin, OTP from SMSDashboard")
print(f"[PANEL] User={PANEL_151_USER} PassSet={bool(PANEL_151_PASS)}")
