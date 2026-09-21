
import os
import requests
import time
import random
import re
from bs4 import BeautifulSoup

NEW_PANEL_URL = "http://151.80.19.204"
NEW_PANEL_LOGIN = f"{NEW_PANEL_URL}/ints/login"

PANEL_151_USER = os.getenv("PANEL_151_USER", "")
PANEL_151_PASS = os.getenv("PANEL_151_PASS", "")

_session_151 = None
_orders_store = {}

def solve_math_captcha(text, soup=None):
    try:
        if soup:
            for elem in soup.find_all(string=re.compile(r'\d+\s*[\+\-\*]\s*\d+')):
                txt = str(elem).strip()
                if len(txt) > 30:
                    continue
                m = re.search(r'(\d+)\s*([\+\-\*])\s*(\d+)', txt)
                if m:
                    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
                    if a < 100 and b < 100:
                        ans = a + b if op == '+' else a - b if op == '-' else a * b
                        print(f"[CAPTCHA] {a} {op} {b} = {ans} from '{txt[:50]}'")
                        return ans
        
        pattern = r'(\d+)\s*([\+\-])\s*(\d+)\s*=\s*\?'
        matches = re.findall(pattern, text)
        for a, op, b in matches:
            a, b = int(a), int(b)
            if a < 100 and b < 100:
                ans = a + b if op == '+' else a - b
                print(f"[CAPTCHA] {a} {op} {b} = {ans} (pattern ?=)")
                return ans
        
        all_matches = re.findall(r'(\d+)\s*([\+\-])\s*(\d+)', text)
        for a, op, b in all_matches:
            a, b = int(a), int(b)
            if a < 50 and b < 50:
                search_str = f"{a} {op} {b}"
                idx = text.find(search_str)
                if idx == -1:
                    search_str = f"{a}{op}{b}"
                    idx = text.find(search_str)
                if idx != -1:
                    ctx = text[max(0, idx-100):idx+100].lower()
                    if any(k in ctx for k in ['captcha', 'what', 'answer', 'security', 'verify', 'question', 'result']):
                        ans = a + b if op == '+' else a - b
                        print(f"[CAPTCHA] {a} {op} {b} = {ans} (context)")
                        return ans
        
        for a, op, b in all_matches:
            a, b = int(a), int(b)
            if a < 20 and b < 20:
                ans = a + b if op == '+' else a - b
                print(f"[CAPTCHA] {a} {op} {b} = {ans} (last resort)")
                return ans
        
        return None
    except Exception as e:
        print(f"[CAPTCHA ERR] {e}")
        return None

def get_session_151():
    global _session_151
    try:
        if _session_151:
            try:
                test = _session_151.get(f"{NEW_PANEL_URL}/ints/", timeout=5)
                if test.status_code == 200 and "login" not in test.url.lower():
                    if "logout" in test.text.lower() or "dashboard" in test.text.lower():
                        print("[151 SESSION] Using cached")
                        return _session_151
            except:
                pass
        
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        print(f"[151 LOGIN] GET {NEW_PANEL_LOGIN}")
        print(f"[151 CREDS CHECK] USER='{PANEL_151_USER}' PASS_SET={bool(PANEL_151_PASS)} PASS_LEN={len(PANEL_151_PASS) if PANEL_151_PASS else 0}")
        
        if not PANEL_151_USER or not PANEL_151_PASS:
            print("[151 ERROR] PANEL_151_USER or PANEL_151_PASS not set in Railway Variables!")
            print("[151 ERROR] Set them in Railway -> Variables -> PANEL_151_USER and PANEL_151_PASS")
            return None
        
        try:
            login_page = session.get(NEW_PANEL_LOGIN, timeout=15)
        except Exception as e:
            print(f"[151 GET ERR] {e}")
            return None
        
        print(f"[151 PAGE] status={login_page.status_code} url={login_page.url} len={len(login_page.text)}")
        
        # Print HTML snippet for debugging - very important
        html = login_page.text
        # Find captcha area
        captcha_idx = html.lower().find('captcha')
        if captcha_idx != -1:
            print(f"[151 HTML CAPTCHA AREA] {html[max(0,captcha_idx-200):captcha_idx+300]}")
        else:
            print(f"[151 HTML START] {html[:2000]}")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        forms = soup.find_all('form')
        print(f"[151 FORMS] {len(forms)} found")
        for i, form in enumerate(forms):
            action = form.get('action','')
            method = form.get('method','GET')
            inputs = []
            for inp in form.find_all('input'):
                inputs.append(f"{inp.get('name')}({inp.get('type')}) placeholder={inp.get('placeholder','')}")
            print(f"[151 FORM {i}] action={action} method={method}")
            print(f"[151 FORM {i} INPUTS] {inputs}")
            # Also print form HTML
            print(f"[151 FORM {i} HTML] {str(form)[:1000]}")
        
        csrf_token = None
        csrf_name = '_token'
        for name in ['_token', 'csrf_token', '_csrf', 'token']:
            inp = soup.find('input', {'name': name})
            if inp and inp.get('value'):
                csrf_token = inp.get('value')
                csrf_name = name
                print(f"[151 CSRF] {name} found len={len(csrf_token)}")
                break
        
        captcha_ans = solve_math_captcha(html, soup)
        print(f"[151 CAPTCHA ANS] {captcha_ans}")
        
        # Detect field names more carefully
        username_field = None
        password_field = None
        captcha_field = None
        
        all_inputs = soup.find_all('input')
        print(f"[151 ALL INPUTS] {[(inp.get('name'), inp.get('type'), inp.get('placeholder','')[:20]) for inp in all_inputs]}")
        
        for inp in all_inputs:
            name = inp.get('name','')
            if not name:
                continue
            name_l = name.lower()
            type_a = inp.get('type','').lower()
            placeholder = (inp.get('placeholder','') or '').lower()
            
            if 'token' in name_l or 'csrf' in name_l:
                continue
            
            if not username_field:
                if type_a in ['text','email',''] and any(x in name_l for x in ['email','user','login']):
                    if 'pass' not in name_l and 'captcha' not in name_l:
                        username_field = name
                elif 'email' in placeholder or 'username' in placeholder or 'user' in placeholder:
                    username_field = name
            
            if not password_field:
                if type_a == 'password' or 'pass' in name_l:
                    password_field = name
            
            if not captcha_field:
                if any(x in name_l for x in ['captcha','answer','result','security','verify']):
                    if type_a not in ['hidden']:
                        captcha_field = name
        
        if not username_field:
            for inp in all_inputs:
                name = inp.get('name','')
                type_a = inp.get('type','').lower()
                if type_a in ['text','email',''] and name and 'captcha' not in name.lower() and 'token' not in name.lower() and 'pass' not in name.lower():
                    username_field = name
                    break
            if not username_field:
                username_field = 'email'
        
        if not password_field:
            password_field = 'password'
        
        if not captcha_field and captcha_ans is not None:
            for inp in all_inputs:
                name = inp.get('name','')
                if name and name not in [username_field, password_field, csrf_name] and inp.get('type','').lower() not in ['hidden','submit','checkbox']:
                    captcha_field = name
                    break
            if not captcha_field:
                captcha_field = 'captcha'
        
        print(f"[151 FIELDS DETECTED] user={username_field} pass={password_field} captcha={captcha_field} csrf={csrf_name}")
        
        # Build attempts - try without captcha first, then with
        attempts = []
        
        # Try 1: Detected fields with captcha
        data_main = {}
        if csrf_token:
            data_main[csrf_name] = csrf_token
        data_main[username_field] = PANEL_151_USER
        data_main[password_field] = PANEL_151_PASS
        if captcha_ans is not None and captcha_field:
            data_main[captcha_field] = str(captcha_ans)
        attempts.append(("detected_with_captcha", data_main))
        
        # Try 2: Detected fields without captcha (maybe captcha field name wrong)
        data_main2 = {}
        if csrf_token:
            data_main2[csrf_name] = csrf_token
        data_main2[username_field] = PANEL_151_USER
        data_main2[password_field] = PANEL_151_PASS
        attempts.append(("detected_without_captcha", data_main2))
        
        # Common combos with captcha
        combos = [
            {'email': PANEL_151_USER, 'password': PANEL_151_PASS},
            {'username': PANEL_151_USER, 'password': PANEL_151_PASS},
            {'name': PANEL_151_USER, 'password': PANEL_151_PASS},
            {'user': PANEL_151_USER, 'password': PANEL_151_PASS},
        ]
        
        for combo in combos:
            base = {}
            if csrf_token:
                base[csrf_name] = csrf_token
            base.update(combo)
            if captcha_ans is not None:
                for cf in [captcha_field, 'captcha', 'answer', 'result', 'captcha_answer', 'security_code', 'code', 'verify', 'captcha_result']:
                    if cf and cf not in base:
                        d = base.copy()
                        d[cf] = str(captcha_ans)
                        attempts.append((f"combo_{list(combo.keys())[0]}_with_{cf}", d))
            attempts.append((f"combo_{list(combo.keys())[0]}_no_captcha", base))
        
        for idx, (desc, data) in enumerate(attempts[:15]):
            try:
                safe_log = {}
                for k,v in data.items():
                    if 'pass' in k.lower():
                        safe_log[k] = '***'
                    elif k == csrf_name:
                        safe_log[k] = str(v)[:15]+'...'
                    else:
                        safe_log[k] = v
                print(f"[151 TRY {idx+1} {desc}] {safe_log}")
                
                resp = session.post(NEW_PANEL_LOGIN, data=data, timeout=15, allow_redirects=True, headers={
                    "Referer": NEW_PANEL_LOGIN,
                    "Origin": NEW_PANEL_URL,
                    "Content-Type": "application/x-www-form-urlencoded",
                })
                
                print(f"[151 TRY {idx+1} RESP] status={resp.status_code} url={resp.url[:80]} len={len(resp.text)}")
                
                # If not on login page anymore, success
                if "login" not in resp.url.lower():
                    lower = resp.text.lower()
                    if any(x in lower for x in ['logout','dashboard','welcome','inbox','sms','balance']):
                        print(f"[151 LOGIN SUCCESS] Try {idx+1} {desc} - URL: {resp.url}")
                        _session_151 = session
                        return session
                    else:
                        print(f"[151 TRY {idx+1}] Redirected but not to dashboard - body: {resp.text[:500]}")
                else:
                    # Still on login - find error message
                    soup_resp = BeautifulSoup(resp.text, 'html.parser')
                    # Look for alert, error, invalid
                    error_selectors = ['.alert', '.error', '.invalid', '[class*=error]', '[class*=alert]', '.text-danger', '.help-block']
                    for sel in error_selectors:
                        err = soup_resp.select_one(sel)
                        if err:
                            print(f"[151 TRY {idx+1} ERROR MSG] {err.get_text()[:300]}")
                            break
                    # Also check for any text with error
                    if "invalid" in resp.text.lower() or "error" in resp.text.lower() or "wrong" in resp.text.lower() or "incorrect" in resp.text.lower():
                        # Find the sentence
                        for line in resp.text.split('\n'):
                            if any(x in line.lower() for x in ['invalid','error','wrong','incorrect','failed']):
                                if len(line.strip()) < 200:
                                    print(f"[151 TRY {idx+1} ERROR LINE] {line.strip()[:200]}")
                
            except Exception as e:
                print(f"[151 TRY {idx+1} EXC] {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("[151 LOGIN FAILED] All tries failed")
        print("[151 DEBUG] If you see 'captcha' errors, check if captcha field name is correct")
        print("[151 DEBUG] If you see 'invalid credentials', check USER/PASS in Railway Variables")
        print(f"[151 DEBUG] Current USER='{PANEL_151_USER}' - make sure it's correct (maybe need email not username?)")
        return None
    except Exception as e:
        print(f"[151 SESSION ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def get_otp_from_panel(order_id):
    try:
        session = get_session_151()
        if not session:
            print("[OTP] No session - login failed")
            return None
        
        endpoints = [
            f"{NEW_PANEL_URL}/ints/",
            f"{NEW_PANEL_URL}/ints/sms",
            f"{NEW_PANEL_URL}/ints/inbox",
        ]
        
        for endpoint in endpoints:
            try:
                resp = session.get(endpoint, timeout=15)
                if resp.status_code != 200:
                    continue
                if "login" in resp.url.lower():
                    print(f"[OTP] Redirected to login from {endpoint}")
                    continue
                
                text = resp.text
                otps = re.findall(r'\b\d{4,8}\b', text)
                for otp in otps:
                    if 4 <= len(otp) <= 8:
                        pos = text.find(otp)
                        ctx = text[max(0,pos-80):pos+80].lower()
                        if any(k in ctx for k in ['code','otp','facebook','fb','verification']):
                            print(f"[OTP FOUND] {otp} from {endpoint}")
                            return otp
            except Exception as e:
                print(f"[OTP {endpoint} ERR] {e}")
                continue
        print("[OTP] Not found")
        return None
    except Exception as e:
        print(f"[OTP ERR] {e}")
        import traceback
        traceback.print_exc()
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
    
    candidates = [
        os.path.join(base, fname),
        os.path.join(base, "numbers_151.txt"),
        os.path.join(base, "numbers_nepal.txt"),
        os.path.join(base, "numbers.txt"),
        fname,
        "numbers_151.txt",
        "numbers.txt",
    ]
    
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
        print(f"[FILE] {fpath} for {country_code}")
        
        if not os.path.exists(fpath):
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
        
        number = lines[0]
        remaining = lines[1:]
        
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
        }
        print(f"[FILE ORDER] {country_code} -> {number} | Remaining: {len(remaining)}")
        return result
    except Exception as e:
        print(f"[FILE ORDER ERR] {e}")
        import traceback
        traceback.print_exc()
        return None

def get_all_countries(service):
    return ["NEPAL_FB", "MOZAMBIQUE", "MYANMAR", "CAMEROON", "USA", "BD", "NEPAL", "MOZAMBIQUE_TT", "MYANMAR_TT", "CAMBODIA"]

def get_display_name(country_code):
    names = {
        "NEPAL": "Nepal",
        "NEPAL_FB": "Nepal",
        "MOZAMBIQUE": "Mozambique",
        "MYANMAR": "Myanmar",
        "CAMEROON": "Cameroon",
        "USA": "USA",
        "BD": "Bangladesh",
        "CAMBODIA": "Cambodia",
    }
    return names.get(country_code.upper(), country_code.replace("_", " ").title())

def create_order(service, country_code):
    print(f"[CREATE ORDER] {service} {country_code}")
    result = create_order_from_file(service, country_code)
    if result:
        _orders_store[result["id"]] = result
        return result
    print(f"[CREATE ORDER] No number for {country_code}")
    return None

def get_otp(order_id):
    print(f"[GET OTP] {order_id}")
    otp = get_otp_from_panel(order_id)
    if otp:
        print(f"[GET OTP] Found: {otp}")
        return otp
    return None

print("[PANEL] FINAL DEBUG - Detailed login debug")
print(f"[PANEL] User: '{PANEL_151_USER}' | Pass set: {bool(PANEL_151_PASS)} | Pass len: {len(PANEL_151_PASS) if PANEL_151_PASS else 0}")
