"""
NexxRetail Profitability Report Extractor
==========================================
- Logs in to both NEXX accounts automatically
- Loops through all 5 branches
- Downloads profitability Excel report per branch
- Saves to data/raw/{branch}/profitability_{date}.xlsx
"""

import os, base64, hashlib, json, requests
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv

load_dotenv()

BASE_URL      = "http://nexx.rubiskenya.com:9632/NexxRetail"
TIMEZONE      = "Africa/Nairobi"
ENCRYPT_KEY   = "compulynxsachu"
OUTPUT_FOLDER = "data/raw"

# Two NEXX accounts — fill branch IDs after first run discovers them
ACCOUNTS = [
    {
        "username": os.getenv("NEXX_USERNAME_1", "BETTY"),
        "password": os.getenv("NEXX_PASSWORD_1", ""),
        "branches": [
            {"name": "Membley", "id": 1746348285, "structId": 151},
            {"name": "Thome",   "id": None,        "structId": None},
            {"name": "Kingo",   "id": None,        "structId": None},
        ]
    },
    {
        "username": os.getenv("NEXX_USERNAME_2", ""),
        "password": os.getenv("NEXX_PASSWORD_2", ""),
        "branches": [
            {"name": "Jogoo Road", "id": None, "structId": None},
            {"name": "Tigoni",     "id": None, "structId": None},
        ]
    }
]

# ── AES (CryptoJS-compatible) ─────────────────────────────────────────────────
def _derive_key_iv(passphrase, salt):
    p, d, di = passphrase.encode(), b"", b""
    while len(d) < 48:
        di = hashlib.md5(di + p + salt).digest()
        d += di
    return d[:32], d[32:48]

def encrypt_aes(plain):
    salt = get_random_bytes(8)
    key, iv = _derive_key_iv(ENCRYPT_KEY, salt)
    pad = 16 - len(plain.encode()) % 16
    padded = plain.encode() + bytes([pad] * pad)
    ct = AES.new(key, AES.MODE_CBC, iv).encrypt(padded)
    return base64.b64encode(b"Salted__" + salt + ct).decode()

def decrypt_aes(b64):
    raw = base64.b64decode(b64)
    key, iv = _derive_key_iv(ENCRYPT_KEY, raw[8:16])
    dec = AES.new(key, AES.MODE_CBC, iv).decrypt(raw[16:])
    return dec[:-dec[-1]].decode()

# ── Session ───────────────────────────────────────────────────────────────────
class NexxSession:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = None
        self.s = requests.Session()
        self.s.headers.update({"Content-Type": "application/json", "Accept": "application/json, */*"})

    def login(self):
        import socket
        try:
            client_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            client_ip = "127.0.0.1"
        self.s.headers.update({
            "Content-Type":    "application/json",
            "Accept":          "application/json, text/plain, */*",
            "Origin":          "http://nexx.rubiskenya.com:9632",
            "Referer":         "http://nexx.rubiskenya.com:9632/",
            "Host":            "nexx.rubiskenya.com:9632",
            "Connection":      "keep-alive",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "FC_Client_Ip":    client_ip,
            "Fc_client_ip":    client_ip,
        })

        # Must send {userName, password} as JSON object — not password alone
        login_obj = json.dumps({"userName": self.username, "password": self.password})
        encrypted = encrypt_aes(login_obj)
        print(f"  Encrypted payload length: {len(encrypted)}")

        r = self.s.post(
            f"{BASE_URL}/login?timeZone={TIMEZONE}",
            json={"value": encrypted}
        )
        print(f"  Login status: {r.status_code}")
        if r.status_code != 200:
            print(f"  Response: {r.text[:300]}")
        r.raise_for_status()
        d = r.json()
        if not d.get("success"):
            raise RuntimeError(f"Login failed: {d.get('message')}")
        self.token = d["token"]
        self.s.headers.update({
            "Authorization":    f"Bearer {self.token}",
            "Fc_authorization": self.token,
            "Fc_tenant_entity": str(d["tenantEntity"]["id"]),
            "Fc_entity":        str(d["id"]),
            "Fc_module":        "5",
            "Fc_client_time":   str(int(datetime.now().timestamp() * 1000)),
        })
        print(f"  ✓ Logged in as {d['fullName']}")
        return self

    def post_encrypted(self, path, payload, binary=False):
        if not self.token:
            self.login()
        url = f"{BASE_URL}/{path}?timeZone={TIMEZONE}"
        r = self.s.post(url, json={"value": encrypt_aes(json.dumps(payload))})
        if r.status_code == 401:
            self.login()
            r = self.s.post(url, json={"value": encrypt_aes(json.dumps(payload))})
        r.raise_for_status()
        return r.content if binary else r.json()

    def get_branches(self):
        r = self.s.get(f"{BASE_URL}/merchandising/org-hierarchy?timeZone={TIMEZONE}&_active=true&noPage=true")
        r.raise_for_status()
        d = r.json()
        return d if isinstance(d, list) else d.get("data", [])

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_day_timestamps(date):
    start = datetime(date.year, date.month, date.day, 0, 0, 0)
    end   = datetime(date.year, date.month, date.day, 23, 59, 59)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)

def build_payload(branch, from_ts, to_ts):
    bo = {"fieldValueId": branch["id"], "fieldId": 454, "name": "BRANCH NAME",
          "value": branch["name"].upper(), "isDefault": True, "required": True,
          "type": "textarea", "id": branch["id"]}
    return {"structId": branch["structId"], "levelId": 0, "branch": bo,
            "itemId": [{"id": branch["id"], "name": branch["name"].upper(),
                        "hierarchyLevel": 0, "structureId": branch["structId"], "values": [bo]}],
            "toDate": to_ts, "fromDate": from_ts,
            "summary": True, "saleType": "POS Issues", "isolation": True, "level": 3}

def resolve_branches(session, branches):
    try:
        api = session.get_branches()
        print(f"  Found {len(api)} branches in API")
        for b in branches:
            if b["id"]: continue
            for a in api:
                aname = (a.get("name") or a.get("value") or "").upper()
                if b["name"].upper() in aname or aname in b["name"].upper():
                    b["id"] = a.get("id")
                    b["structId"] = a.get("structureId") or a.get("structId") or 151
                    print(f"    Mapped: {b['name']} → ID {b['id']}")
                    break
            if not b["id"]:
                print(f"    ⚠ Not found: {b['name']} | Available: {[a.get('name') or a.get('value') for a in api[:8]]}")
    except Exception as e:
        print(f"  ⚠ Branch discovery failed: {e}")
    return branches

def save_excel(content, branch_name, date):
    folder = os.path.join(OUTPUT_FOLDER, branch_name)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"profitability_{date.strftime('%Y-%m-%d')}.xlsx")
    with open(path, "wb") as f:
        f.write(content)
    print(f"    ✓ Saved: {branch_name}/profitability_{date.strftime('%Y-%m-%d')}.xlsx ({len(content):,} bytes)")
    return path

# ── Main ──────────────────────────────────────────────────────────────────────
def run_extraction(days_back=1):
    print("=" * 50)
    print("NEXX EXTRACTOR  Starting...")
    print("=" * 50)

    target_date = datetime.now() - timedelta(days=days_back)
    from_ts, to_ts = get_day_timestamps(target_date)
    print(f"\n  Date: {target_date.strftime('%Y-%m-%d')}")

    total = 0
    for account in ACCOUNTS:
        if not account["password"]:
            print(f"\n  ⚠ Skipping {account['username']} — NEXX_PASSWORD not set in .env")
            continue

        print(f"\n  Account: {account['username']}")
        session = NexxSession(account["username"], account["password"]).login()
        branches = resolve_branches(session, account["branches"])

        for branch in branches:
            if not branch["id"]:
                print(f"  ⚠ Skipping {branch['name']} — ID not found")
                continue
            print(f"\n  Downloading: {branch['name']}...")
            try:
                content = session.post_encrypted(
                    "inventory-reports/report/profitability",
                    build_payload(branch, from_ts, to_ts),
                    binary=True
                )
                if content[:2] == b'PK':
                    save_excel(content, branch["name"], target_date)
                    total += 1
                else:
                    print(f"  ⚠ Unexpected response: {content[:80]}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")

    print(f"\n{'=' * 50}")
    print(f"EXTRACTION COMPLETE  {total} files saved to {OUTPUT_FOLDER}/")
    print("=" * 50)
    return total > 0

if __name__ == "__main__":
    run_extraction()