"""
Extra features for HolderBot, same architecture (requests + sqlite):
  1) Billing  : sum allocated/used traffic for an admin's users from index N
  2) Protocol : add/remove a protocol on all active + on_hold users
  3) Reset    : baseline storage helpers (used by reseter.py)
All functions are synchronous (requests). Call them via asyncio.to_thread
from the async holder.py handlers so the bot never blocks.
"""

import sqlite3
import json
import uuid as uuidlib
import secrets
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from Function.db import DEF_IMPORT_DATA, DEF_PANEL_ACCESS

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

ACTIVE_STATUSES = ("active", "on_hold")


def _new_proxy_settings(proto):
    """Return fresh, unique settings for a protocol so xray never sees a
    duplicate identifier. vmess/vless need a unique UUID; trojan/ss a password."""
    if proto in ("vmess", "vless"):
        return {"id": str(uuidlib.uuid4())}
    if proto == "trojan":
        return {"password": secrets.token_hex(8)}
    if proto == "shadowsocks":
        return {"password": secrets.token_hex(8)}
    return {}


# ---------- DB setup for new features ----------

def DEF_FEATURES_INIT():
    """Create tables for reset baseline + billing history (run once)."""
    conn = sqlite3.connect("holder.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reset_state (
            username TEXT PRIMARY KEY,
            used_traffic INTEGER,
            checked_at REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS billing_history (
            id INTEGER PRIMARY KEY,
            admin TEXT,
            from_idx INTEGER,
            to_idx INTEGER,
            from_user TEXT,
            to_user TEXT,
            allocated_gb REAL,
            used_gb REAL,
            user_count INTEGER,
            created_at REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reset_alert (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            status TEXT
        )
    """)
    c.execute("INSERT OR IGNORE INTO reset_alert (id, status) VALUES (1, 'off')")
    conn.commit()
    conn.close()


def DEF_RESET_ALERT_STATUS():
    """Return 'on' or 'off'."""
    try:
        conn = sqlite3.connect("holder.db")
        c = conn.cursor()
        c.execute("SELECT status FROM reset_alert WHERE id = 1")
        row = c.fetchone()
        conn.close()
        return row[0] if row else "off"
    except Exception:
        return "off"


def DEF_RESET_ALERT_TOGGLE():
    """Flip status, return new status."""
    cur = DEF_RESET_ALERT_STATUS()
    new = "off" if cur == "on" else "on"
    conn = sqlite3.connect("holder.db")
    c = conn.cursor()
    c.execute("UPDATE reset_alert SET status = ? WHERE id = 1", (new,))
    conn.commit()
    conn.close()
    return new


# ---------- Helpers ----------

def _panel(CHATID):
    """Return (domain, headers) or (None, None)."""
    PANEL_USER, PANEL_PASS, PANEL_DOMAIN = DEF_IMPORT_DATA(CHATID)
    headers = DEF_PANEL_ACCESS(PANEL_USER, PANEL_PASS, PANEL_DOMAIN)
    if not headers:
        return None, None
    return PANEL_DOMAIN, headers


def _get_all_users(domain, headers, session=None, status=None, admin=None):
    """Fetch all users via pagination. Optional server-side status/admin filter."""
    s = session or requests
    out = []
    offset = 0
    limit = 500
    while True:
        url = f"{domain}/api/users?offset={offset}&limit={limit}"
        if status:
            url += f"&status={status}"
        if admin:
            url += f"&admin={admin}"
        r = s.get(url, headers=headers, verify=False)
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


def _gb(b):
    return round((b or 0) / (1024 ** 3), 2)


# ---------- BILLING ----------

def DEF_BILLING_ADMINS(CHATID):
    """Return list of admin usernames."""
    domain, headers = _panel(CHATID)
    if not domain:
        return []
    r = requests.get(f"{domain}/api/admins", headers=headers, verify=False)
    if r.status_code != 200:
        return []
    admins = r.json()
    return [a.get("username") for a in admins if a.get("username")]


def DEF_BILLING_USERS(CHATID, ADMIN):
    """Return sorted list of an admin's usernames (by creation order from API)."""
    domain, headers = _panel(CHATID)
    if not domain:
        return []
    # Server-side filter by admin = fast
    url = f"{domain}/api/users?admin={ADMIN}"
    r = requests.get(url, headers=headers, verify=False)
    if r.status_code != 200:
        return []
    data = r.json()
    users = data.get("users", []) if isinstance(data, dict) else data
    return users  # full dicts; caller indexes them


def DEF_BILLING_CALC(CHATID, ADMIN, START):
    """
    Sum allocated (data_limit) and used (used_traffic) from index START to end.
    START can be an int index or a username string.
    Returns a result dict or {'error': msg}.
    """
    users = DEF_BILLING_USERS(CHATID, ADMIN)
    if not users:
        return {"error": "no users"}

    # resolve START -> index
    if isinstance(START, str) and not START.isdigit():
        idx = None
        for i, u in enumerate(users):
            if u.get("username", "").lower() == START.lower():
                idx = i
                break
        if idx is None:
            return {"error": f"user '{START}' not found"}
    else:
        idx = int(START)
        if idx < 0 or idx >= len(users):
            return {"error": f"index out of range 0-{len(users)-1}"}

    subset = users[idx:]
    alloc = sum((u.get("data_limit") or 0) for u in subset)
    used = sum((u.get("used_traffic") or 0) for u in subset)

    result = {
        "admin": ADMIN,
        "from_idx": idx,
        "to_idx": len(users) - 1,
        "from_user": users[idx].get("username", "?"),
        "to_user": users[-1].get("username", "?"),
        "count": len(subset),
        "allocated_gb": _gb(alloc),
        "used_gb": _gb(used),
        "left_gb": _gb(alloc - used),
    }

    # save history
    try:
        import time
        conn = sqlite3.connect("holder.db")
        cc = conn.cursor()
        cc.execute("""
            INSERT INTO billing_history
            (admin, from_idx, to_idx, from_user, to_user, allocated_gb, used_gb, user_count, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (ADMIN, result["from_idx"], result["to_idx"], result["from_user"],
              result["to_user"], result["allocated_gb"], result["used_gb"],
              result["count"], time.time()))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return result


def DEF_BILLING_LAST(CHATID, ADMIN):
    """Return last billing (to_idx, to_user) for an admin or None."""
    try:
        conn = sqlite3.connect("holder.db")
        c = conn.cursor()
        c.execute("""
            SELECT to_idx, to_user FROM billing_history
            WHERE admin=? ORDER BY created_at DESC LIMIT 1
        """, (ADMIN,))
        row = c.fetchone()
        conn.close()
        return row
    except Exception:
        return None


# ---------- PROTOCOL MANAGEMENT ----------

def DEF_PROTOCOLS(CHATID):
    """Return {protocol: [tags]} from /api/inbounds."""
    domain, headers = _panel(CHATID)
    if not domain:
        return {}
    r = requests.get(f"{domain}/api/inbounds", headers=headers, verify=False)
    if r.status_code != 200:
        return {}
    inbounds = r.json()
    if not isinstance(inbounds, dict):
        return {}
    out = {}
    for proto, items in inbounds.items():
        tags = [it.get("tag") for it in items if it.get("tag")]
        if tags:
            out[proto] = tags
    return out


def DEF_PROTOCOL_COUNT_TARGETS(CHATID, statuses=ACTIVE_STATUSES, admin=None, proto=None, action=None):
    """
    Count users that WILL be affected:
      - action 'add'    -> users that do NOT have `proto`
      - action 'remove' -> users that DO have `proto`
      - proto/action None -> just count all in statuses
    """
    domain, headers = _panel(CHATID)
    if not domain:
        return 0
    count = 0
    for st in statuses:
        users = _get_all_users(domain, headers, status=st, admin=admin)
        for u in users:
            proxies = u.get("proxies", {}) or {}
            if proto and action == "add":
                if proto not in proxies:
                    count += 1
            elif proto and action == "remove":
                if proto in proxies:
                    count += 1
            else:
                count += 1
    return count


def DEF_PROTOCOL_APPLY(CHATID, PROTO, TAGS, ACTION, statuses=ACTIVE_STATUSES, admin=None, progress_cb=None):
    """
    Add or remove a protocol on users in the given statuses (optional admin filter).
      - 'add'    : only users WITHOUT the protocol (others skipped). Fresh unique UUID.
      - 'remove' : only users WITH the protocol (others skipped).
    Returns (ok, fail, skipped).
    """
    domain, headers = _panel(CHATID)
    if not domain:
        return 0, 0, 0

    session = requests.Session()
    session.verify = False
    session.headers.update(headers)

    targets = []
    for st in statuses:
        targets.extend(_get_all_users(domain, headers, session=session, status=st, admin=admin))

    total = len(targets)
    ok = fail = skipped = 0
    done = 0

    for u in targets:
        username = u.get("username")
        proxies = u.get("proxies", {}) or {}
        inbounds = u.get("inbounds", {}) or {}

        do_put = True
        if ACTION == "add":
            if PROTO in proxies:          # already has it -> skip
                skipped += 1
                do_put = False
            else:
                proxies[PROTO] = _new_proxy_settings(PROTO)
                cur = set(inbounds.get(PROTO, []))
                cur.update(TAGS)
                inbounds[PROTO] = list(cur)
        else:  # remove
            if PROTO not in proxies:      # doesn't have it -> skip
                skipped += 1
                do_put = False
            else:
                inbounds.pop(PROTO, None)
                proxies.pop(PROTO, None)

        if do_put:
            body = {"proxies": proxies, "inbounds": inbounds}
            try:
                r = session.put(f"{domain}/api/user/{username}", json=body)
                if r.status_code == 200:
                    ok += 1
                else:
                    fail += 1
            except Exception:
                fail += 1

        done += 1
        if progress_cb:
            progress_cb(done, total)

    session.close()
    return ok, fail, skipped


# ---------- GIVE EXPIRE DATE TO TIME-UNLIMITED USERS ----------

def DEF_GIVE_DATE_COUNT(CHATID, ADMIN):
    """Count users of ADMIN who have no expire (expire = 0/None)."""
    domain, headers = _panel(CHATID)
    if not domain:
        return 0
    users = _get_all_users(domain, headers, admin=ADMIN)
    return sum(1 for u in users if not u.get("expire"))


def DEF_GIVE_DATE_APPLY(CHATID, ADMIN, DAYS, progress_cb=None):
    """
    Set expire = now + DAYS for every user of ADMIN that currently has no expire.
    Only touches time-unlimited users (expire == 0/None). Returns (ok, fail, skipped).
    """
    import time as _t
    domain, headers = _panel(CHATID)
    if not domain:
        return 0, 0, 0

    session = requests.Session()
    session.verify = False
    session.headers.update(headers)

    users = _get_all_users(domain, headers, session=session, admin=ADMIN)
    new_expire = int(_t.time()) + int(DAYS) * 86400

    total = len(users)
    ok = fail = skipped = 0
    done = 0
    for u in users:
        username = u.get("username")
        if u.get("expire"):  # already has a date -> skip
            skipped += 1
        else:
            body = {"expire": new_expire}
            try:
                r = session.put(f"{domain}/api/user/{username}", json=body)
                if r.status_code == 200:
                    ok += 1
                else:
                    fail += 1
            except Exception:
                fail += 1
        done += 1
        if progress_cb:
            progress_cb(done, total)

    session.close()
    return ok, fail, skipped


# ---------- FIND UNLIMITED USERS ----------

def DEF_FIND_UNLIMITED(CHATID, admin=None):
    """
    Return (time_unlimited, data_unlimited) lists of usernames.
    time_unlimited: expire == 0/None
    data_unlimited: data_limit == 0/None
    """
    domain, headers = _panel(CHATID)
    if not domain:
        return [], []
    users = _get_all_users(domain, headers, admin=admin)
    time_unl = [u.get("username") for u in users if not u.get("expire")]
    data_unl = [u.get("username") for u in users if not u.get("data_limit")]
    return time_unl, data_unl
