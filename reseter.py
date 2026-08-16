from pyrogram import *
from Function.db import *
from Function.myfeatures import DEF_RESET_ALERT_STATUS
import time, sqlite3, requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Separate DB so heavy per-user writes never lock holder.db (keeps the bot fast)
RESET_DB = "reset.db"

def init_reset_db():
    conn = sqlite3.connect(RESET_DB)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""CREATE TABLE IF NOT EXISTS reset_state (
        username TEXT PRIMARY KEY, used_traffic INTEGER )""")
    conn.commit()
    conn.close()

init_reset_db()

app = Client(
    "reseter",
    api_id=26410400,
    api_hash="408bf51732560cb81a0e32533b858cbf",
    bot_token=DEF_GET_BOT_TOKEN())


def load_all_states():
    """Read every previous state at once -> dict."""
    conn = sqlite3.connect(RESET_DB)
    c = conn.cursor()
    c.execute("SELECT username, used_traffic FROM reset_state")
    rows = c.fetchall()
    conn.close()
    return {u: t for u, t in rows}


def save_all_states(pairs):
    """Replace the whole table with the CURRENT users only, in ONE transaction.
    Any user no longer present in the panel is automatically dropped."""
    conn = sqlite3.connect(RESET_DB)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("DELETE FROM reset_state")
    conn.executemany(
        "INSERT OR REPLACE INTO reset_state (username, used_traffic) VALUES (?,?)",
        pairs)
    conn.commit()
    conn.close()


def fetch_all_users(domain, headers):
    out = []
    offset = 0
    limit = 500
    while True:
        url = f"{domain}/api/users?offset={offset}&limit={limit}"
        r = requests.get(url, headers=headers, verify=False)
        if r.status_code != 200:
            break
        data = r.json()
        batch = data.get("users", []) if isinstance(data, dict) else data
        if not batch:
            break
        out.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return out


with app:
    while True:
        try:
            if DEF_RESET_ALERT_STATUS() != "on":
                time.sleep(60)
                continue

            BOSS_CHATID, NODE_STATUS, CHECK_NORMAL, CHECK_ERROR = DEF_MONITORING_DATA()
            PANEL_USER, PANEL_PASS, PANEL_DOMAIN = DEF_IMPORT_DATA(BOSS_CHATID)
            PANEL_TOKEN = DEF_PANEL_ACCESS(PANEL_USER, PANEL_PASS, PANEL_DOMAIN)
            if not PANEL_TOKEN:
                time.sleep(30)
                continue

            users = fetch_all_users(PANEL_DOMAIN, PANEL_TOKEN)

            prev_states = load_all_states()
            new_pairs = []
            resets = []  # (username, prev_used) to notify

            for USER in users:
                username = USER.get("username")
                if not username:
                    continue
                used = USER.get("used_traffic") or 0
                new_pairs.append((username, used))

                prev = prev_states.get(username)
                if prev is None:
                    continue
                if prev > 0 and used < prev:
                    resets.append((username, prev))

            # Save baseline/state once (batch, separate DB)
            if new_pairs:
                save_all_states(new_pairs)

            # Notify resets (usually few)
            for username, prev_used in resets:
                admin_name = "?"
                data_limit = 0
                try:
                    r = requests.get(f"{PANEL_DOMAIN}/api/user/{username}",
                                     headers=PANEL_TOKEN, verify=False)
                    if r.status_code == 200:
                        full = r.json()
                        adm = full.get("admin")
                        if isinstance(adm, dict):
                            admin_name = adm.get("username", "?")
                        elif adm:
                            admin_name = adm
                        data_limit = full.get("data_limit") or 0
                except Exception:
                    pass

                if data_limit and data_limit > 0:
                    quota_gb = round(data_limit / (1024 ** 3), 2)
                    quota_line = f"<b>📦 Quota :</b> <code>{quota_gb} GB</code>\n"
                else:
                    quota_line = "<b>📦 Quota :</b> <code>Unlimited</code>\n"

                freed_gb = round(prev_used / (1024 ** 3), 2)
                TEXT = (f"<b>🔄 Traffic reset</b>\n\n"
                        f"<b>👤 User :</b> <code>{username}</code>\n"
                        f"<b>📊 Owner :</b> <code>{admin_name}</code>\n"
                        f"{quota_line}"
                        f"<b>📥 Used before reset :</b> <code>{freed_gb} GB</code>")
                try:
                    app.send_message(chat_id=BOSS_CHATID, text=TEXT,
                                     parse_mode=enums.ParseMode.HTML,
                                     disable_notification=True)
                except Exception:
                    pass

            time.sleep(60)

        except Exception as e:
            try:
                app.send_message(chat_id=BOSS_CHATID,
                                 text=f"<b>❌ (Checker) Reseter Error :</b>\n<pre>{str(e)}</pre>",
                                 parse_mode=enums.ParseMode.HTML)
            except Exception:
                pass
            time.sleep(60)
