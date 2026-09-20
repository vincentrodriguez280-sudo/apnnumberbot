
import os
import requests
import time
import random
import re
from bs4 import BeautifulSoup

# ========== SIMPLE PANEL - GITHUB FILE + PANEL OTP ==========
# Flow:
# 1. Number github file e rakho (numbers_151.txt)
# 2. Member click korle 8 ta number oi file theke jabe
# 3. OTP panel theke watcher diye user + OTP group e jabe

NEW_PANEL_URL = "http://151.80.19.204"
NEW_PANEL_LOGIN = f"{NEW_PANEL_URL}/ints/login"

PANEL_151_USER = os.getenv("PANEL_151_USER", "")
PANEL_151_PASS = os.getenv("PANEL_151_PASS", "")

_session_151 = None
_orders_store = {}

def solve_math_captcha(text, soup=None):
    """Jog biyog captcha solve"""
    try:
        m = re.search(r'(\d+)\s*([\+\-])\s*(\d+)', text)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            ans = a + b if op == '+' else a - b
            print(f"[CAPTCHA] {a} {op} {b} = {ans}")
            return ans
        if soup:
            for elem in soup.find_all(text=re.compile(r'\d+\s*[\+\-]\s*\d+')):
                m = re.search(r'(\d+)\s*([\+\-])\s*(\d+)', str(elem))
                if m:
                    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
                    ans = a + b if op == '+' else a - b
                    return ans
        return None
    except:
        return None

def get_session_151():
    """Login to panel with captcha"""
    global _session_151
    try:
        if _session_151:
            try:
                test = _session_151.get(f"{NEW_PANEL_URL}/ints/", timeout=5)
                if test.status_code == 200 and "login" not in test.url.lower():
                    return _session_151
            except:
                pass
        
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        
        login_page = session.get(NEW_PANEL_LOGIN, timeout=15)
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        csrf_token = None
        for name in ['_token', 'csrf_token', '_csrf']:
            inp = soup.find('input', {'name': name})
            if inp:
                csrf_token = inp.get('value')
                break
        
        captcha_ans = solve_math_captcha(login_page.text, soup)
        print(f"[151 LOGIN] Captcha ans: {captcha_ans}")
        
        # Login variants
        user_fields = ['username', 'email', 'user', 'login']
        pass_fields = ['password', 'pass']
        captcha_fields = ['captcha', 'answer', 'result', 'captcha_result', 'security_code']
        
        variants = []
        for uf in user_fields:
            for pf in pass_fields:
                base = {uf: PANEL_151_USER, pf: PANEL_151_PASS}
                if csrf_token:
                    base['_token'] = csrf_token
                if captcha_ans is not None:
                    for cf in captcha_fields:
                        v = base.copy()
                        v[cf] = str(captcha_ans)
                        variants.append(v)
                variants.append(base.copy())
        
        for i, data in enumerate(variants[:10]):
            try:
                resp = session.post(NEW_PANEL_LOGIN, data=data, timeout=15, allow_redirects=True)
                if "login" not in resp.url.lower() and resp.status_code in [200, 302]:
                    lower = resp.text.lower()
                    if any(x in lower for x in ['logout', 'dashboard', 'number', 'sms']):
                        print(f"[151 LOGIN SUCCESS]")
                        _session_151 = session
                        return session
            except:
                continue
        
        print("[151 LOGIN FAILED]")
        return None
    except Exception as e:
        print(f"[151 SESSION ERR] {e}")
        return None

def get_otp_from_panel(order_id):
    """OTP panel theke anbe - watcher user + OTP group e pathabe"""
    try:
        session = get_session_151()
        if not session:
            print("[OTP] No session")
            return None
        
        # Try inbox/sms pages
        endpoints = [
            f"{NEW_PANEL_URL}/ints/",
            f"{NEW_PANEL_URL}/ints/sms",
            f"{NEW_PANEL_URL}/ints/inbox",
            f"{NEW_PANEL_URL}/ints/dashboard",
        ]
        
        for endpoint in endpoints:
            try:
                resp = session.get(endpoint, timeout=15)
                if resp.status_code != 200:
                    continue
                
                # Find OTP 4-8 digit near keywords
                # Look for all 4-8 digit codes
                text = resp.text
                
                # Try to find OTP patterns
                # Common: "123456 is your code", "OTP: 1234"
                otps = re.findall(r'\b\d{4,8}\b', text)
                for otp in otps:
                    if 4 <= len(otp) <= 8:
                        pos = text.find(otp)
                        ctx = text[max(0, pos-100):pos+100].lower()
                        # Check if near OTP keywords
                        if any(k in ctx for k in ['code', 'otp', 'facebook', 'fb', 'verification', 'whatsapp', 'tiktok', 'your code']):
                            print(f"[OTP FOUND] {otp} from {endpoint}")
                            return otp
                
                # Also check JSON or specific elements
                try:
                    soup = BeautifulSoup(text, 'html.parser')
                    # Look for table rows with OTP
                    for row in soup.find_all('tr'):
                        row_text = row.get_text()
                        if any(c.isdigit() for c in row_text):
                            m = re.search(r'\b\d{4,8}\b', row_text)
                            if m:
                                otp = m.group(0)
                                if 4 <= len(otp) <= 8:
                                    print(f"[OTP FOUND TABLE] {otp}")
                                    return otp
                except:
                    pass
                    
            except Exception as e:
                print(f"[OTP ENDPOINT {endpoint} ERR] {e}")
                continue
        
        return None
    except Exception as e:
        print(f"[OTP ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

# ========== FILE BASED NUMBERS - GITHUB FILE ==========

def get_numbers_file_path(country_code):
    """Github file er path - /data e sync hoy"""
    base = "/data" if os.path.exists("/data") else "."
    
    # Map country to file - tumi github e je file rakba
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
        # Common file for 151 panel
        "151": "numbers_151.txt",
        "OTHER": "numbers_151.txt",
    }
    
    fname = file_map.get(country_code.upper(), "numbers_151.txt")
    
    # Try country specific first, then fallback to numbers_151.txt
    fpath = os.path.join(base, fname)
    if os.path.exists(fpath):
        return fpath
    
    # Fallback to numbers_151.txt (main github file)
    fallback = os.path.join(base, "numbers_151.txt")
    if os.path.exists(fallback):
        return fallback
    
    # Fallback to numbers.txt
    fallback2 = os.path.join(base, "numbers.txt")
    if os.path.exists(fallback2):
        return fallback2
    
    return fpath

def create_order_from_file(service, country_code):
    """Github file theke 1 number debe - main.py 8 bar call korbe = 8 number"""
    try:
        fpath = get_numbers_file_path(country_code)
        print(f"[FILE] Trying {fpath} for {country_code}")
        
        if not os.path.exists(fpath):
            # Try numbers_151.txt
            base = "/data" if os.path.exists("/data") else "."
            alt = os.path.join(base, "numbers_151.txt")
            if os.path.exists(alt):
                fpath = alt
            else:
                print(f"[FILE] Not found: {fpath}")
                return None
        
        with open(fpath, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#") and any(c.isdigit() for c in l)]
        
        if not lines:
            print(f"[FILE] Empty: {fpath}")
            return None
        
        # Get first number
        number = lines[0]
        remaining = lines[1:]
        
        # Remove from file so not reused
        with open(fpath, 'w') as fw:
            for ln in remaining:
                fw.write(ln + "\n")
        
        order_id = f"151_{int(time.time())}_{random.randint(1000,9999)}"
        result = {
            "number": number,
            "id": order_id,
            "country": country_code,
            "service": service,
            "panel": "151_file",
            "file": fpath
        }
        
        print(f"[FILE ORDER] {country_code} -> {number} from {os.path.basename(fpath)} | Remaining: {len(remaining)}")
        return result
        
    except Exception as e:
        print(f"[FILE ORDER ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

# ========== MAIN BOT FUNCTIONS ==========

def get_all_countries(service):
    """Available countries"""
    return ["NEPAL_FB", "MOZAMBIQUE", "MYANMAR", "CAMEROON", "USA", "BD", "NEPAL", "MOZAMBIQUE_TT", "MYANMAR_TT"]

def get_display_name(country_code):
    names = {
        "NEPAL": "Nepal",
        "NEPAL_FB": "Nepal",
        "MOZAMBIQUE": "Mozambique",
        "MOZAMBIQUE_TT": "Mozambique",
        "MYANMAR": "Myanmar",
        "MYANMAR_TT": "Myanmar",
        "CAMEROON": "Cameroon",
        "USA": "USA",
        "BD": "Bangladesh",
    }
    return names.get(country_code.upper(), country_code.replace("_", " ").title())

def create_order(service, country_code):
    """
    SIMPLE FLOW:
    1. Github file (numbers_151.txt) theke number nibe
    2. 1 number per call - main.py 8 bar call korbe = 8 number member pabe
    """
    print(f"[CREATE ORDER] {service} {country_code}")
    
    result = create_order_from_file(service, country_code)
    if result:
        _orders_store[result["id"]] = result
        return result
    
    print(f"[CREATE ORDER] No number for {country_code}")
    return None

def get_otp(order_id):
    """
    SIMPLE FLOW:
    1. Panel theke OTP anbe (jog biyog captcha solve kore login)
    2. main.py er otp_watcher auto user inbox + @APNOTP group e pathabe
    """
    print(f"[GET OTP] For order {order_id}")
    
    otp = get_otp_from_panel(order_id)
    if otp:
        print(f"[GET OTP] Found OTP: {otp}")
        return otp
    
    return None

print("[PANEL] SIMPLE MODE LOADED")
print("[PANEL] Flow: Github file (numbers_151.txt) -> 8 numbers to member -> Panel OTP -> inbox + OTP group")
print(f"[PANEL] User: {PANEL_151_USER[:3]}... | Pass set: {bool(PANEL_151_PASS)}")
