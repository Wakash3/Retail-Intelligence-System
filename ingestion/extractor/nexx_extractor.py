"""
NexxRetail Profitability Report Extractor
==========================================
- Logs in to both NEXX accounts automatically
- Caches tokens to avoid repeated logins
- Downloads profitability Excel report per branch
- Saves to data/raw/{branch}/profitability_{date}.xlsx
"""

import os, base64, hashlib, json, requests, socket
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv

load_dotenv()

BASE_URL      = "http://nexx.rubiskenya.com:9632/NexxRetail"
TIMEZONE      = "Africa/Nairobi"
ENCRYPT_KEY   = "compulynxsachu"
OUTPUT_FOLDER = "data/raw"
TOKEN_CACHE   = ".nexx_tokens.json"  # stores tokens between runs

try:
    CLIENT_IP = socket.gethostbyname(socket.gethostname())
except Exception:
    CLIENT_IP = "127.0.0.1"

ACCOUNTS = [
    {
        "username": os.getenv("NEXX_USERNAME_1", "betty"),
        "password": os.getenv("NEXX_PASSWORD_1", ""),
        "branches": [
            {"name": "Membley",  "nexx_name": "ENJOY EMMA BRENDA MEMBLEY", "id": 1746348285, "structId": 151},
            {"name": "Thome",    "nexx_name": "ENJOY EMMA BRENDA 1",        "id": 1817147085, "structId": 151},
            {"name": "Kimbo",    "nexx_name": "ENJOY EMMA BRENDA 2",        "id": 1817147086, "structId": 151},
        ]
    },
    {
        "username": os.getenv("NEXX_USERNAME_2", "joy"),
        "password": os.getenv("NEXX_PASSWORD_2", ""),
        "branches": [
            {"name": "Jogoo Road", "nexx_name": "ENJOY EMMA BRENDA JOGOO RD", "id": 1955047435, "structId": 151},
            {"name": "Tigoni",     "nexx_name": "ENJOY EMMA BRENDA TIGONI",   "id": 380850050,  "structId": 151},
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

# ── Token Cache ───────────────────────────────────────────────────────────────
def load_token_cache():
    try:
        if os.path.exists(TOKEN_CACHE):
            return json.load(open(TOKEN_CACHE))
    except Exception:
        pass
    return {}

def save_token_cache(cache):
    try:
        json.dump(cache, open(TOKEN_CACHE, "w"))
    except Exception:
        pass

# ── Session ───────────────────────────────────────────────────────────────────
class NexxSession:
    def __init__(self, username, password):
        self.username  = username
        self.password  = password
        self.token     = None
        self.entity_id = None
        self.tenant_id = None
        self.s = requests.Session()
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
            "FC_Client_Ip":    CLIENT_IP,
            "Fc_client_ip":    CLIENT_IP,
        })

    def _apply_token(self, token, entity_id, tenant_id):
        """Apply token to session headers — no login needed."""
        self.token     = token
        self.entity_id = entity_id
        self.tenant_id = tenant_id
        self.s.headers.update({
            "Fc_authorization":  self.token,
            "Fc_tenant_entity":  self.tenant_id,
            "Fc_entity":         self.entity_id,
            "Fc_module":         "5",
            "Fc_menu":           "75",
            "Menu":              "75",
            "Module_id":         "5",
            "Fc_client_time":    str(int(datetime.now().timestamp() * 1000)),
            "FC_ActiveLanguage": "1",
            "Fc_activelanguage": "1",
            "Reporttype":        "XLSX",
            "ReportType":        "XLSX",
            "Structureid":       "151",
            "field_id":          "0",
            "Parenttenant":      "false",
        })
        self.s.headers.pop("Authorization", None)

    def login(self):
        """Login and get fresh token — only called when cache is empty/expired."""
        print(f"  Logging in as {self.username}...")
        login_obj = json.dumps({"userName": self.username, "password": self.password})
        r = self.s.post(
            f"{BASE_URL}/login?timeZone={TIMEZONE}",
            json={"value": encrypt_aes(login_obj)}
        )
        print(f"  Login status: {r.status_code}")
        if r.status_code != 200:
            print(f"  Response: {r.text[:300]}")
        r.raise_for_status()
        d = r.json()
        if not d.get("success"):
            raise RuntimeError(f"Login failed: {d.get('message')}")

        self._apply_token(d["token"], str(d["id"]), str(d["tenantEntity"]["id"]))

        # Save token to cache
        cache = load_token_cache()
        cache[self.username] = {
            "token":     self.token,
            "entity_id": self.entity_id,
            "tenant_id": self.tenant_id,
            "saved_at":  datetime.now().isoformat()
        }
        save_token_cache(cache)
        print(f"  ✓ Logged in as {d['fullName']} (token cached)")
        return self

    def connect(self):
        """Use cached token if available, otherwise login."""
        cache = load_token_cache()
        if self.username in cache:
            c = cache[self.username]
            saved_at = datetime.fromisoformat(c["saved_at"])
            age_hours = (datetime.now() - saved_at).total_seconds() / 3600
            if age_hours < 8:  # reuse token if less than 8 hours old
                print(f"  ✓ Using cached token for {self.username} (age: {age_hours:.1f}h)")
                self._apply_token(c["token"], c["entity_id"], c["tenant_id"])
                return self
            else:
                print(f"  Token expired for {self.username} — logging in fresh...")
        return self.login()

    def post_encrypted(self, path, payload, binary=False, branch_id=None):
        # Set Fc_entity to branch ID for report requests
        if branch_id:
            self.s.headers.update({"Fc_entity": str(branch_id)})
        url = f"{BASE_URL}/{path}?timeZone={TIMEZONE}"
        r   = self.s.post(url, json={"value": encrypt_aes(json.dumps(payload))})
        if r.status_code == 401:
            # Token expired — clear cache and re-login once
            print(f"  Token rejected — clearing cache and re-logging in...")
            cache = load_token_cache()
            cache.pop(self.username, None)
            save_token_cache(cache)
            self.login()
            r = self.s.post(url, json={"value": encrypt_aes(json.dumps(payload))})
        if r.status_code != 200:
            print(f"  ⚠ Server response ({r.status_code}): {r.text[:300]}")
        r.raise_for_status()
        return r.content if binary else r.json()

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_day_timestamps(date):
    start = datetime(date.year, date.month, date.day, 0, 0, 0)
    end   = datetime(date.year, date.month, date.day, 23, 59, 59)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)

def build_payload(branch, from_ts, to_ts):
    nexx_name = branch["nexx_name"]
    bo = {
        "fieldValueId": branch["id"], "fieldId": 454,
        "name": "BRANCH NAME", "value": nexx_name,
        "isDefault": True, "required": True, "type": "textarea",
        "id": branch["id"]
    }
    return {
        "structId": branch["structId"], "levelId": 0, "branch": bo,
        "itemId": [{
            "id": branch["id"], "name": nexx_name,
            "hierarchyLevel": 0, "structureId": branch["structId"],
            "values": [bo]
        }],
        "toDate": to_ts, "fromDate": from_ts,
        "summary": True, "saleType": "POS Issues",
        "isolation": True, "level": 3
    }

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
            print(f"\n  ⚠ Skipping {account['username']} — password not set in .env")
            continue

        print(f"\n  Account: {account['username']}")
        try:
            session = NexxSession(account["username"], account["password"]).connect()
        except Exception as e:
            print(f"  ✗ Could not connect: {e}")
            continue

        for branch in account["branches"]:
            print(f"\n  Downloading: {branch['name']}...")
            try:
                content = session.post_encrypted(
                    "inventory-reports/report/profitability",
                    build_payload(branch, from_ts, to_ts),
                    binary=True,
                    branch_id=branch["id"]
                )
                if content[:2] == b'PK':
                    save_excel(content, branch["name"], target_date)
                    total += 1
                else:
                    print(f"  ⚠ Unexpected response: {content[:200]}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")

    print(f"\n{'=' * 50}")
    print(f"EXTRACTION COMPLETE  {total} files saved to {OUTPUT_FOLDER}/")
    print("=" * 50)
    return total > 0

if __name__ == "__main__":
    run_extraction()