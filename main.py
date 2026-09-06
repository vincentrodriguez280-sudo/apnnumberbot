import os, json, asyncio, shutil, re
from datetime import datetime, date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from panel import create_order, get_otp, get_all_countries, get_display_name

TOKEN = os.getenv("BOT_TOKEN")
MUST_JOIN = ["@APNOfficial", "@APNOTP", "@Proxystore999"]
CH1 = "https://t.me/APNOfficial"
CH2 = "https://t.me/APNOTP"
CH3 = "https://t.me/Proxystore999"
OTP_GROUP = "https://t.me/APNOTP"
OTP_GROUP_ID = "@APNOTP"
SUPPORT_ID = "https://t.me/PolasChandra"
SERVICES = ["FACEBOOK", "WHATSAPP"]

BASE_DIR = "/app/data" if os.path.exists("/app/data") else "."
BAL_FILE = os.path.join(BASE_DIR, "balances.json")
TRAFFIC_FILE = os.path.join(BASE_DIR, "traffic.json")
SUCCESS_FILE = os.path.join(BASE_DIR, "success_traffic.json")
RANGES_FILE = os.path.join(BASE_DIR, "ranges.json")
MAINT_FILE = os.path.join(BASE_DIR, "maintenance.json")
ACTIVE_FILE = os.path.join(BASE_DIR, "active_numbers.json")
WALLET_FILE = os.path.join(BASE_DIR, "wallets.json")

if not os.path.exists(RANGES_FILE) and os.path.exists("ranges.json"):
    try:
        os.makedirs(BASE_DIR, exist_ok=True)
        shutil.copy("ranges.json", RANGES_FILE)
    except: pass

ADMIN_ID = 1853202569
FLAGS = {
    "NEPAL": "🇳🇵", "NEPAL_FB": "🇳🇵",
    "CAMEROON": "🇨🇲", "GUINEA": "🇬🇳", "GUNIEA": "🇬🇳",
    "MADAGASCAR": "🇲🇬", "MONTENEGRO": "🇲🇪", "UKRAINE": "🇺🇦",
    "HAITI": "🇭🇹", "SIERRA_LEONE": "🇸🇱", "USA": "🇺🇸", "USA_FB": "🇺🇸",
    "MOROCCO": "🇲🇦", "NIGERIA": "🇳🇬", "MOZAMBIQUE": "🇲🇿", "ISRAEL": "🇮🇱",
}
PRICES = {
    "NEPAL": "0.005$", "NEPAL_FB": "0.005$",
    "MOROCCO": "0.003$", "NIGERIA": "0.003$", "MOZAMBIQUE": "0.003$",
    "CAMEROON": "0.003$", "GUINEA": "0.003$", "MADAGASCAR": "0.003$",
    "MONTENEGRO": "0.003$", "UKRAINE": "0.003$", "HAITI": "0.003$",
    "SIERRA_LEONE": "0.003$", "USA": "0.003$", "USA_FB": "0.003$",
    "DEFAULT": "0.003$",
}

def load_json(f, default):
    if os.path.exists(f):
        try:
            with open(f,'r') as fp: return json.load(fp)
        except: return default
    return default

def save_json(f, data):
    os.makedirs(os.path.dirname(f) if os.path.dirname(f) else ".", exist_ok=True)
    with open(f,'w') as fp: json.dump(data, fp, indent=2)

def is_maintenance():
    return load_json(MAINT_FILE, {"enabled": False}).get("enabled", False)

def get_user(uid):
    db = load_json(BAL_FILE, {})
    uid=str(uid)
    if uid not in db:
        db[uid]={"balance":0.0,"requests":[],"total":0,"ref":0,"referrals":0,"level":1,"wallet_method":None,"wallet_address":None,"referred_by":None}
        save_json(BAL_FILE, db)
    # migrate old users
    if "referrals" not in db[uid]: db[uid]["referrals"]=0
    if "level" not in db[uid]: db[uid]["level"]=1
    if "wallet_method" not in db[uid]: db[uid]["wallet_method"]=None
    if "wallet_address" not in db[uid]: db[uid]["wallet_address"]=None
    if "referred_by" not in db[uid]: db[uid]["referred_by"]=None
    if "balance" not in db[uid]: db[uid]["balance"]=0.0
    return db[uid]

def save_user(uid, data):
    db = load_json(BAL_FILE, {})
    db[str(uid)]=data
    save_json(BAL_FILE, db)

def add_request(uid, country):
    user = get_user(uid)
    user["requests"].append(datetime.now().isoformat())
    user["total"]+=1
    save_user(uid, user)
    tr = load_json(TRAFFIC_FILE, {})
    tr[country] = tr.get(country,0)+1
    save_json(TRAFFIC_FILE, tr)

def add_success(country):
    tr = load_json(SUCCESS_FILE, {})
    tr[country] = tr.get(country,0)+1
    save_json(SUCCESS_FILE, tr)

def save_active_number(uid, number, country, service):
    db = load_json(ACTIVE_FILE, {})
    uid=str(uid)
    if uid not in db: db[uid]=[]
    db[uid].append({"number": number, "country": country, "service": service, "time": datetime.now().isoformat()})
    db[uid]=db[uid][-20:]
    save_json(ACTIVE_FILE, db)

def get_active_numbers(uid):
    db = load_json(ACTIVE_FILE, {})
    return db.get(str(uid), [])

def mask_number(num):
    n = num.replace(" ", "").replace("+", "").strip()
    if len(n) <= 6: return "+" + n
    return f"+{n[:4]}XXXXXX{n[-3:]}"

def format_for_inbox(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    country_name = clean.replace("_", " ").title()
    flag = FLAGS.get(clean, FLAGS.get(clean.split("_")[0], "🌍"))
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    # Earn logic: Nepal 0.005$, others 0.003$
    if "NEPAL" in clean.upper():
        earn_text = "+$0.005"
    else:
        earn_text = "+$0.003"
    text = f"{flag} {country_name}\n📞 `{full_number}`\n💳 Earned: {earn_text}\n\n🔑 OTP: `{otp_digits}`"
    keyboard = [[InlineKeyboardButton(f"📋 {otp_digits}", callback_data=f"copy_{otp_digits}")]]
    return text, InlineKeyboardMarkup(keyboard)

def format_for_group(country_code, full_number, service, otp_code):
    clean = country_code.upper().replace("_FB","").replace("_WS","").replace("_2","")
    masked = mask_number(full_number)
    otp_digits = ''.join(filter(str.isdigit, str(otp_code)))
    service_display = "TikTok" if service.upper() == "FACEBOOK" else service.title()
    text = f"APN NUMBER BOT\n💳 #{clean} 📱 {service_display}\n\n╭─────────────────╮\n  {masked}  📱 {otp_digits}\n╰─────────────────╯\n\n🗣 Language: #English"
    keyboard = [[InlineKeyboardButton(f"🔓 {otp_digits}", callback_data=f"copy_{otp_digits}")], [InlineKeyboardButton("🧪 Panel", url="https://t.me/APNOfficial"), InlineKeyboardButton("📢 CHANNEL", url=CH1)]]
    return text, InlineKeyboardMarkup(keyboard)

async def is_joined(user_id, context):
    if user_id == ADMIN_ID: return True
    for ch in MUST_JOIN:
        try:
            m = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ['left','kicked']: return False
        except: continue
    return True

async def otp_watcher(bot, order_id, user_id, number, service, country_code):
    print(f"[WATCHER START] {number} {order_id}")
    for i in range(180):
        await asyncio.sleep(5)
        try:
            otp = await asyncio.to_thread(get_otp, order_id)
            if otp:
                print(f"[OTP FOUND] {number} -> {otp}")
                text_inbox, markup_inbox = format_for_inbox(country_code, number, service, otp)
                text_group, markup_group = format_for_group(country_code, number, service, otp)
                try:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox, parse_mode="Markdown")
                except:
                    await bot.send_message(chat_id=user_id, text=text_inbox, reply_markup=markup_inbox)
                try:
                    await bot.send_message(chat_id=OTP_GROUP_ID, text=text_group, reply_markup=markup_group, parse_mode="Markdown")
                except Exception as e:
                    print(f"[FAIL GROUP] {e}")
                user = get_user(user_id)
                # Nepal 0.005$, baki country 0.003$ per OTP
                if "NEPAL" in country_code.upper():
                    earn = 0.005
                else:
                    earn = 0.003
                user["balance"]+=earn
                save_user(user_id, user)
                print(f"[BALANCE] User {user_id} +${earn} -> ${user['balance']:.4f} | {country_code} {service}")
                # commission to referrer
                if user.get("referred_by"):
                    ref_user = get_user(user["referred_by"])
                    # commission based on level
                    refs = ref_user.get("referrals",0)
                    if refs >= 5000: comm = 0.0100
                    elif refs >= 2000: comm = 0.0070
                    elif refs >= 500: comm = 0.0006
                    elif refs >= 100: comm = 0.0005
                    else: comm = 0.0002
                    ref_user["balance"]+=comm
                    save_user(user["referred_by"], ref_user)
                add_success(country_code)
                return
        except Exception as e:
            print(f"[WATCHER ERR] {e}")
    print(f"[TIMEOUT] {number}")

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    reason = " ".join(context.args) if context.args else "Scheduled maintenance"
    save_json(MAINT_FILE, {"enabled": True, "reason": reason})
    await update.message.reply_text("🔴 Bot OFF")

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    save_json(MAINT_FILE, {"enabled": False})
    await update.message.reply_text("🟢 Bot ON")

async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    status = "🔴 OFF" if is_maintenance() else "🟢 ON"
    await update.message.reply_text(f"Bot Status: {status}")

async def add_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        rid = context.args[2]
        if service == "FB": service = "FACEBOOK"
        if service == "WS": service = "WHATSAPP"
        data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
        if service not in data: data[service] = {}
        data[service][name] = rid
        save_json(RANGES_FILE, data)
        await update.message.reply_text(f"✅ Added {service} - {name} = {rid}")
    except:
        await update.message.reply_text("❌ Use: /add FB CAMEROON 23762")

async def del_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        service = context.args[0].upper()
        name = context.args[1].upper()
        if service == "FB": service = "FACEBOOK"
        if service == "WS": service = "WHATSAPP"
        data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
        if name in data.get(service, {}):
            del data[service][name]
            save_json(RANGES_FILE, data)
            await update.message.reply_text(f"🗑 Deleted {name}")
        else:
            await update.message.reply_text("❌ Not found")
    except:
        await update.message.reply_text("❌ Use: /del FB CAMEROON")

async def list_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    data = load_json(RANGES_FILE, {"FACEBOOK":{}, "WHATSAPP":{}})
    txt = f"📋 Ranges ({BASE_DIR}):\n\n"
    for srv, ranges in data.items():
        txt += f"{srv}:\n"
        for n, r in ranges.items():
            txt += f"- {n} = {r}\n"
        txt += "\n"
    await update.message.reply_text(txt)

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Your ID: {update.effective_user.id}")

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Get Number", callback_data="services"), InlineKeyboardButton("🌍 Status", callback_data="live")],
        [InlineKeyboardButton("📊 Active Number", callback_data="active"), InlineKeyboardButton("👨‍💼 Support", callback_data="support")],
        [InlineKeyboardButton("👥 Refer", callback_data="refer"), InlineKeyboardButton("💰 Wallet", callback_data="wallet")]
    ])

def bottom_keyboard():
    # UCHIHA style bottom persistent buttons - green/blue like in screenshot
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Get Number"), KeyboardButton("🌍 Status")],
            [KeyboardButton("📊 Active Number"), KeyboardButton("👨‍💼 Support")],
            [KeyboardButton("👥 Refer"), KeyboardButton("💰 Wallet")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # referral handling
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            ref_id = args[0].replace("ref_","")
            if str(ref_id) != str(uid):
                user = get_user(uid)
                if not user.get("referred_by"):
                    user["referred_by"]=str(ref_id)
                    save_user(uid, user)
                    # increase referrer count
                    ref_user = get_user(ref_id)
                    ref_user["referrals"]=ref_user.get("referrals",0)+1
                    # update level
                    r = ref_user["referrals"]
                    if r >= 5000: ref_user["level"]=5
                    elif r >= 2000: ref_user["level"]=4
                    elif r >= 500: ref_user["level"]=3
                    elif r >= 100: ref_user["level"]=2
                    else: ref_user["level"]=1
                    save_user(ref_id, ref_user)
                    try:
                        await context.bot.send_message(chat_id=int(ref_id), text=f"🎉 New referral! User {uid} joined via your link.\nTotal referrals: {ref_user['referrals']}")
                    except: pass
        except: pass

    if is_maintenance() and uid!= ADMIN_ID:
        await update.message.reply_text("🛠 System Under Maintenance")
        return
    get_user(uid)
    if await is_joined(uid, context):
        txt = "✅ Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
        await update.message.reply_text(txt, reply_markup=main_menu_keyboard())
        # Send bottom keyboard like UCHIHA bot
        await update.message.reply_text("👇 Use buttons below:", reply_markup=bottom_keyboard())
    else:
        txt = "⚠️ Access Denied!\nPlease join our channels to use the bot."
        kb = [
            [InlineKeyboardButton("Join Channel 1", url=CH1)],
            [InlineKeyboardButton("Join Channel 2", url=CH2)],
            [InlineKeyboardButton("Join Channel 3", url=CH3)],
            [InlineKeyboardButton("✅ Verify", callback_data="check")]
        ]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    # Check if awaiting wallet address
    method = context.user_data.get("awaiting_wallet_for")
    if method and text not in ["📱 Get Number", "🌍 Status", "📊 Active Number", "👨‍💼 Support", "👥 Refer", "💰 Wallet"]:
        if len(text) < 10:
            await update.message.reply_text("❌ Invalid address. Send valid address.")
            return
        user = get_user(uid)
        user["wallet_method"]=method
        user["wallet_address"]=text
        save_user(uid, user)
        context.user_data["awaiting_wallet_for"]=None
        txt = f"✅ Wallet Set!\n\n💵 Method: {method}\n✉️ Address:\n{text}"
        kb = [
            [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]
        ]
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        await update.message.reply_text("Menu:", reply_markup=main_menu_keyboard())
        return

    # Bottom keyboard handling - same as UCHIHA bot
    if text == "📱 Get Number":
        # Simulate services callback
        txt = "⚙️ কোন প্ল্যাটফর্মের জন্য নাম্বার নিবেন?"
        kb = []
        for s in SERVICES:
            icon = "📘" if s == "FACEBOOK" else "💬"
            name = "Facebook" if s == "FACEBOOK" else "WhatsApp"
            kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"s_{s}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="main")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text == "🌍 Status":
        succ_tr = load_json(SUCCESS_FILE, {})
        today = date.today().strftime("%-m/%-d/%Y")
        msg = "🔥 LIVE-STOCK STATUS.💥\n\n📘 Facebook\n"
        if succ_tr:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
                flag = FLAGS.get(c.split("_")[0], "🌍")
                price = PRICES.get(c.upper(), PRICES.get(c.split("_")[0], "0.003$"))
                msg += f"├─ {flag} {c.replace('_FB','').title()} — {price}\n"
        else:
            msg += "├─ 🇲🇦 Morocco — $0.003$\n├─ 🇳🇬 Nigeria — $0.003$\n├─ 🇳🇵 Nepal — Free\n"
        msg += "────────────────────\n"
        msg += f"📅 Date: {today}\n"
        msg += "────────────────────"
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
        return
    elif text == "📊 Active Number":
        actives = get_active_numbers(uid)
        if not actives:
            msg = "📊 Active Number\n\nNo active numbers. Get a number first."
            kb = [[InlineKeyboardButton("📱 Get Number", callback_data="services")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
            return
        last = actives[-1]
        flag = FLAGS.get(last['country'].split("_")[0], "🌍")
        msg = f"✅ Active Number\n\n{flag} {last['country'].replace('_FB','').title()}\nPlatform: {last['service']}\nNumber: {last['number']}"
        kb = [
            [InlineKeyboardButton(f"{last['number']}", callback_data=f"copy_{last['number']}")],
            [InlineKeyboardButton("📥 View OTP", url=OTP_GROUP), InlineKeyboardButton("🔄 Change", callback_data=f"c_{last['country']}")],
            [InlineKeyboardButton("🔙 Back", callback_data="main")]
        ]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text == "👨‍💼 Support":
        msg = "☎️ Contact support:"
        kb = [[InlineKeyboardButton("✉️ Contact Admin", url="https://t.me/PolasChandra")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text == "👥 Refer":
        user = get_user(uid)
        refs = user.get("referrals",0)
        level = user.get("level",1)
        balance = user.get("balance",0.0)
        if level==1: need=100
        elif level==2: need=500
        elif level==3: need=2000
        elif level==4: need=5000
        else: need=5000
        progress_bar = "█" * min(10, int(refs/20)) + "░" * (10-min(10, int(refs/20)))
        invite_link = f"https://t.me/{context.bot.username}?start=ref_{uid}"
        msg = f"👥 Referral Dashboard\n━━━━━━━━━━━━━━━━━━\n\n🔥 Rank: Level {level}\n👥 Referrals: {refs}\n💰 Balance: ${balance:.4f}\n📊 Progress: [{progress_bar}] {refs}/{need}\n\n━━━━━━━━━━━━━━━━━━\n💎 Commission Tiers\n━━━━━━━━━━━━━━━━━━\n\n🔥 L1  $0.0002/OTP  (0+ refs)  ✦\n🌊 L2  $0.0005/OTP  (100+ refs)\n🦁 L3  $0.0006/OTP  (500+ refs)\n🛡️ L4  $0.0070/OTP  (2000+ refs)\n👑 L5  $0.0100/OTP  (5000+ refs)\n\n🚀 Your Invite Link:\n{invite_link}"
        kb = [[InlineKeyboardButton("🔗 Copy Invite Link", callback_data=f"copy_{invite_link}")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return
    elif text == "💰 Wallet":
        user = get_user(uid)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        balance = user.get("balance",0.0)
        if method and address:
            masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
            if balance < 0.15:
                msg = f"💳 Method: {method}\n✉️ Address: {masked}\n\n❌ Insufficient Balance\n\n💰 Balance: ${balance:.4f}\n🔻 Minimum: $0.15"
            else:
                msg = f"💳 Method: {method}\n✉️ Address: {masked}\n\n💰 Balance: ${balance:.4f}\n✅ Ready to withdraw!"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        else:
            msg = f"💰 Wallet\n\n💰 Balance: ${balance:.4f}\n\nNo wallet set. Set your payment method first.\n🔻 Minimum withdraw: $0.15"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    uid = q.from_user.id
    try:
        await q.answer()
    except: pass

    if data.startswith("copy_"):
        val = data.split("copy_",1)[1]
        # Send copyable version
        try:
            await q.answer(f"📋 {val} Copied! Tap to copy below", show_alert=True)
            await context.bot.send_message(chat_id=uid, text=f"`{val}`\n👆 Tap to copy", parse_mode="Markdown")
        except:
            await q.answer(f"📋 {val} Copied!", show_alert=False)
        return

    if data.startswith("setmethod_"):
        method = data.replace("setmethod_","")
        context.user_data["awaiting_wallet_for"]=method
        await q.edit_message_text(f"✉️ Send your {method} wallet address:\n\nExample: 0x0Bc20843c4452C6fAcAf7E1b757a00c0F79D6268")
        return

    if is_maintenance() and uid!= ADMIN_ID:
        await q.edit_message_text("🛠 System Under Maintenance")
        return
    if data!= "check" and not await is_joined(uid, context):
        txt = "⚠️ Access Denied!\nPlease join our channels to use the bot."
        kb = [
            [InlineKeyboardButton("Join Channel 1", url=CH1)],
            [InlineKeyboardButton("Join Channel 2", url=CH2)],
            [InlineKeyboardButton("Join Channel 3", url=CH3)],
            [InlineKeyboardButton("✅ Verify", callback_data="check")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "check":
        if await is_joined(uid, context):
            txt = "✅ Verification Successful!\nWelcome to our platform.\nEnjoy a smooth and secure experience.\n\nMenu:"
            await q.edit_message_text(txt, reply_markup=main_menu_keyboard())
            try:
                await context.bot.send_message(chat_id=uid, text="👇 Use buttons below:", reply_markup=bottom_keyboard())
            except: pass
        else:
            await q.edit_message_text("❌ Not joined yet. Please join all channels and click Verify.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify", callback_data="check")]]))
        return

    if data == "main":
        await q.edit_message_text("Menu:", reply_markup=main_menu_keyboard())
        return

    if data == "wallet":
        user = get_user(uid)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        balance = user.get("balance",0.0)
        if method and address:
            masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
            # Always show Method, Address, Balance like UCHIHA screenshot
            if balance < 0.15:
                txt = f"💳 Method: {method}\n✉️ Address: {masked}\n\n❌ Insufficient Balance\n\n💰 Balance: ${balance:.4f}\n🔻 Minimum: $0.15"
            else:
                txt = f"💳 Method: {method}\n✉️ Address: {masked}\n\n💰 Balance: ${balance:.4f}\n✅ Ready to withdraw!"
            kb = [
                [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            txt = f"💰 Wallet\n\n💰 Balance: ${balance:.4f}\n\nNo wallet set. Set your payment method first.\n🔻 Minimum withdraw: $0.15"
            kb = [
                [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "set_wallet":
        txt = "💳 Set Payment Method\n\nSelect your preferred payment method:"
        kb = [
            [InlineKeyboardButton("⬜ BEP20", callback_data="setmethod_BEP20")],
            [InlineKeyboardButton("🟣 Bybit", callback_data="setmethod_Bybit"), InlineKeyboardButton("🔷 Bitget", callback_data="setmethod_Bitget")],
            [InlineKeyboardButton("🛡️ Trust Wallet", callback_data="setmethod_Trust Wallet"), InlineKeyboardButton("🟡 Binance", callback_data="setmethod_Binance")],
            [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "withdraw":
        user = get_user(uid)
        balance = user.get("balance",0.0)
        method = user.get("wallet_method")
        address = user.get("wallet_address")
        if not method or not address:
            txt = f"❌ No wallet set\n\n💰 Balance: ${balance:.4f}\n\nPlease set wallet first!"
            kb = [[InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet")], [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return
        masked = address[:8]+"••••••••••••"+address[-6:] if len(address)>20 else address
        if balance < 0.15:
            txt = f"💳 Method: {method}\n✉️ Address: {masked}\n\n❌ Insufficient Balance\n\n💰 Balance: ${balance:.4f}\n🔻 Minimum: $0.15"
            kb = [
                [InlineKeyboardButton("💳 Set Wallet", callback_data="set_wallet"), InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("⬅️ Back", callback_data="wallet")]
            ]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        else:
            txt = f"✅ Withdraw Requested\n\n💰 Amount: ${balance:.4f}\n💳 Method: {method}\n✉️ Address: {masked}\n\n⏳ Will be processed within 24h"
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]))
            # Reset balance after withdraw request
            user["balance"]=0.0
            save_user(uid, user)
        return

    if data == "refer":
        user = get_user(uid)
        refs = user.get("referrals",0)
        level = user.get("level",1)
        balance = user.get("balance",0.0)
        # progress to next level
        if level==1: need=100; prog=refs
        elif level==2: need=500; prog=refs
        elif level==3: need=2000; prog=refs
        elif level==4: need=5000; prog=refs
        else: need=5000; prog=5000
        progress_bar = "█" * min(10, int(prog/20)) + "░" * (10-min(10, int(prog/20)))
        invite_link = f"https://t.me/{context.bot.username}?start=ref_{uid}"
        txt = f"👥 Referral Dashboard\n━━━━━━━━━━━━━━━━━━\n\n🔥 Rank: Level {level}\n👥 Referrals: {refs}\n💰 Balance: ${balance:.4f}\n📊 Progress: [{progress_bar}] {refs}/{need}\n\n🎯 {100-refs if refs<100 else 500-refs if refs<500 else 2000-refs if refs<2000 else 5000-refs if refs<5000 else 0} more referrals → ✨ Level {level+1 if level<5 else 5}\n\n━━━━━━━━━━━━━━━━━━\n💎 Commission Tiers\n━━━━━━━━━━━━━━━━━━\n\n🔥 L1  $0.0002/OTP  (0+ refs)  ✦\n🌊 L2  $0.0005/OTP  (100+ refs)\n🦁 L3  $0.0006/OTP  (500+ refs)\n🛡️ L4  $0.0070/OTP  (2000+ refs)\n👑 L5  $0.0100/OTP  (5000+ refs)\n\n💡 Every OTP your referral receives\n= instant commission for you!\n\n🚀 Your Invite Link:\n{invite_link}"
        kb = [
            [InlineKeyboardButton("🔗 Copy Invite Link", callback_data=f"copy_{invite_link}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "support":
        txt = "☎️ Contact support:"
        kb = [[InlineKeyboardButton("✉️ Contact Admin", url="https://t.me/PolasChandra")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "active":
        actives = get_active_numbers(uid)
        if not actives:
            txt = "📊 Active Number\n\nNo active numbers. Get a number first."
            kb = [[InlineKeyboardButton("📱 Get Number", callback_data="services")], [InlineKeyboardButton("⬅️ Back", callback_data="main")]]
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
            return
        last = actives[-1]
        flag = FLAGS.get(last['country'].split("_")[0], "🌍")
        txt = f"✅ Active Number\n\n{flag} {last['country'].replace('_FB','').title()}\nPlatform: {last['service']}\nNumber: {last['number']}"
        kb = [
            [InlineKeyboardButton(f"{last['number']}", callback_data=f"copy_{last['number']}")],
            [InlineKeyboardButton("📥 View OTP", url=OTP_GROUP), InlineKeyboardButton("🔄 Change", callback_data=f"c_{last['country']}")],
            [InlineKeyboardButton("🔙 Back", callback_data="main")]
        ]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "live":
        succ_tr = load_json(SUCCESS_FILE, {})
        today = date.today().strftime("%-m/%-d/%Y")
        txt = "🔥 LIVE-STOCK STATUS.💥\n\n📘 Facebook\n"
        if succ_tr:
            for c, v in sorted(succ_tr.items(), key=lambda x: x[1], reverse=True)[:10]:
                flag = FLAGS.get(c.split("_")[0], "🌍")
                price = PRICES.get(c.upper(), PRICES.get(c.split("_")[0], "0.003$"))
                txt += f"├─ {flag} {c.replace('_FB','').title()} — {price}\n"
        else:
            txt += "├─ 🇳🇵 Nepal — $0.005$\n├─ 🇲🇦 Morocco — $0.003$\n├─ 🇳🇬 Nigeria — $0.003$\n"
        txt += "────────────────────\n"
        txt += f"📅 Date: {today}\n"
        txt += "────────────────────"
        kb = [[InlineKeyboardButton("⬅️ Back", callback_data="main")]]
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "services":
        txt = "⚙️ কোন প্ল্যাটফর্মের জন্য নাম্বার নিবেন?"
        kb = []
        for s in SERVICES:
            icon = "📘" if s == "FACEBOOK" else "💬"
            name = "Facebook" if s == "FACEBOOK" else "WhatsApp"
            kb.append([InlineKeyboardButton(f"{icon} {name}", callback_data=f"s_{s}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="main")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("s_"):
        service = data[2:]
        context.user_data['service'] = service
        countries = get_all_countries(service)
        if not countries and service.upper() == "FACEBOOK":
            countries = ["NEPAL_FB"]
        if not countries:
            await q.edit_message_text(f"❌ No ranges for {service}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="services")]]))
            return
        seen_base = set()
        unique_countries = []
        for c in countries:
            base = c.upper().split("_")[0]
            if base not in seen_base or "NEPAL" in base:
                if "NEPAL" in base:
                    if "NEPAL" not in seen_base:
                        unique_countries.append("NEPAL_FB")
                        seen_base.add("NEPAL")
                else:
                    unique_countries.append(c.upper())
                    seen_base.add(base)
        unique_countries = [c for c in unique_countries if "NEPAL" not in c]
        if service.upper() == "FACEBOOK":
            unique_countries.insert(0, "NEPAL_FB")
        countries_sorted = unique_countries
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        txt = f"💳 {platform_name} - দেশ সিলেক্ট করুন:"
        kb = []
        for code in countries_sorted:
            display = get_display_name(code)
            base_key = code.upper().split("_")[0]
            flag = FLAGS.get(code.upper(), FLAGS.get(base_key, "🌍"))
            price = PRICES.get(code.upper(), PRICES.get(base_key, PRICES.get("DEFAULT", "0.003$")))
            btn_text = f"{flag} {display} {price}"
            kb.append([InlineKeyboardButton(btn_text, callback_data=f"c_{code}")])
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="services")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("c_"):
        country_code = data[2:]
        service = context.user_data.get('service', 'FACEBOOK')
        display = get_display_name(country_code)
        flag = FLAGS.get(country_code.upper(), FLAGS.get(country_code.upper().split("_")[0], "🌍"))
        is_nepal = "NEPAL" in country_code.upper()
        num_count = 3 if is_nepal else 6
        await q.edit_message_text(f"⏳ Fetching {num_count} numbers for {display}...")
        nums = []
        for i in range(num_count):
            try:
                order = await asyncio.to_thread(create_order, service, country_code)
            except Exception as e:
                print(f"[CREATE THREAD ERR] {e}")
                order = None
            if order:
                nums.append(order)
                add_request(uid, display)
                save_active_number(uid, order['number'], country_code, service)
                context.application.create_task(otp_watcher(context.bot, order['id'], uid, order['number'], service, country_code))
                await asyncio.sleep(0.5)
        if not nums:
            await q.edit_message_text(f"❌ Out of Stock! {display}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Try Again", callback_data=f"s_{service}")]]))
            return
        platform_name = "Facebook" if service.upper() == "FACEBOOK" else service.title()
        header = f"────────── ⋆⋅☆⋅⋆ ──────────\n{flag} {display} Fresh Number 💸\n📱 {platform_name}\n────────── ⋆⋅☆⋅⋆ ──────────\n\n💫 Wait 5s Or Check The OTP Grup 🖤"
        txt = header
        kb = []
        for o in nums:
            try:
                kb.append([InlineKeyboardButton(f"{o['number']}", copy_text=CopyTextButton(o['number']))])
            except:
                kb.append([InlineKeyboardButton(f"{o['number']}", callback_data=f"copy_{o['number']}")])
        kb.append([InlineKeyboardButton("📥 View OTP", url=OTP_GROUP)])
        kb.append([InlineKeyboardButton("🔄 Change", callback_data=f"c_{country_code}"), InlineKeyboardButton("🔙 Back", callback_data=f"s_{service}")])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
        return

from telegram.request import HTTPXRequest
request = HTTPXRequest(connection_pool_size=20, connect_timeout=30, read_timeout=30, write_timeout=30, pool_timeout=30)
app = ApplicationBuilder().token(TOKEN).request(request).build()

async def error_handler(update, context):
    print(f"[BOT ERROR] {context.error}")
    try:
        if "Timed out" in str(context.error) or "ConnectTimeout" in str(context.error):
            return
    except: pass

app.add_error_handler(error_handler)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("id", get_my_id))
app.add_handler(CommandHandler("add", add_range))
app.add_handler(CommandHandler("del", del_range))
app.add_handler(CommandHandler("list", list_range))
app.add_handler(CommandHandler("off", bot_off))
app.add_handler(CommandHandler("on", bot_on))
app.add_handler(CommandHandler("botstatus", bot_status))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
app.add_handler(CallbackQueryHandler(handle))
app.run_polling(drop_pending_updates=True)
