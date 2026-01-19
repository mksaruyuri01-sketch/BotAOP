import importlib, subprocess, sys, os, time, json, re
from datetime import datetime
import requests

# ======== CONFIG ========
API_URL = "http://www.dinodonut.shop/log/dump.php"
CONFIG_FILE = "config.json"

# ======== WRITE PERMISSION CHECK ========
def check_writable(path="."):
    try:
        testfile = os.path.join(path, f".writetest_{int(time.time())}.tmp")
        with open(testfile, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(testfile)
        return True
    except Exception:
        return False

if not check_writable():
    print("\033[1;31m❌ ไม่มีสิทธิ์เขียนไฟล์ในโฟลเดอร์นี้\033[0m")
    print("👉 กรุณารันเป็นแอดมิน หรือย้ายไฟล์ไปที่ Downloads/Documents")
    sys.exit(1)

# ======== AUTO INSTALL MODULES ========
def ensure_package(pkg):
    try:
        importlib.import_module(pkg)
    except ImportError:
        print(f"📦 Installing missing package: {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

def check_and_install_once():
    flag = False
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                flag = json.load(f).get("auto_install_done", False)
        except Exception:
            pass
    if not flag:
        print("🚀 ตรวจสอบโมดูลที่จำเป็นครั้งแรก ...")
        ensure_package("requests")
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"auto_install_done": True}, f, ensure_ascii=False, indent=2)
        print("✅ ติดตั้งสำเร็จแล้ว จะไม่ทำซ้ำอีก\n")

check_and_install_once()

# ======== BANNER ========
def banner():
    print("\033[1;33m" + "═" * 60)
    print("🦖  \033[1;33mDinoDonut API Client  \033[0;37m|  API by DinoShop™")
    print("\033[1;33m" + "═" * 60)
    print("\033[0;36mพร้อมทำงานในโหมด Loop — กด Ctrl + C เพื่อออกจากโปรแกรม\033[0m\n")

# ======== CONFIG KEY ========
def load_api_key():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("api_key", "").strip()
        except Exception:
            pass
    return ""

def save_api_key(key):
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["api_key"] = key
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\033[1;32m💾 บันทึก API Key แล้วที่ {CONFIG_FILE}\033[0m\n")
    except Exception as e:
        print(f"\033[1;31m⚠️ ไม่สามารถบันทึก API Key ได้:\033[0m {e}\n")

# ======== VERIFY KEY ========
def verify_api_key(api_key):
    for attempt in range(3):
        try:
            r = requests.get(API_URL, params={"q": "test", "key": api_key}, timeout=8)
            if r.status_code != 200:
                print(f"❌ API HTTP {r.status_code}")
                continue
            js = r.json()
            if js.get("status") == "success":
                return True
            msg = js.get("message", "")
            print(f"⚠️ {msg or 'Invalid response'}")
            return False
        except Exception as e:
            print(f"⚠️ ตรวจสอบคีย์ล้มเหลว ({attempt+1}/3): {e}")
            time.sleep(1)
    return False

# ======== QUERY ========
def query_dinodonut(q, t, api_key):
    try:
        start = time.perf_counter()
        print(f"⏳ กำลังดึงข้อมูลจาก API: {q} (mode={t}) ...")

        r = requests.get(API_URL, params={"q": q, "t": t, "key": api_key}, timeout=180)

        # ตรวจสอบสถานะ HTTP ก่อน parse JSON
        if r.status_code == 404:
            print("\033[1;31m❌ ไม่พบข้อมูลใน (รอแอดมินอัปเดตฐานข้อมูลใหม่)\033[0m\n")
            return
        elif r.status_code == 403:
            print("\033[1;31m⛔ Error: HTTP 403 — ไม่มีสิทธิ์เข้าถึง API (โปรดตรวจสอบ API Key)\033[0m\n")
            return
        elif r.status_code >= 500:
            print(f"\033[1;31m💥 Error: HTTP {r.status_code} — เซิร์ฟเวอร์มีปัญหา กรุณาลองใหม่ภายหลัง\033[0m\n")
            return
        elif r.status_code != 200:
            print(f"\033[1;31m❌ Error: HTTP {r.status_code} — ไม่สามารถเชื่อมต่อ API ได้\033[0m\n")
            return

        # พยายามแปลงเป็น JSON
        try:
            data = r.json()
        except json.decoder.JSONDecodeError:
            print("\033[1;31m❌ Error: ไม่สามารถอ่านข้อมูลจาก API (อาจไม่ใช่ JSON หรือ API ปิดปรับปรุง)\033[0m\n")
            return

        # ตรวจจับ error message ที่มาจาก API เอง
        msg = str(data.get("message", "")).lower()
        if "404" in msg or "not found" in msg:
            print("\033[1;31m❌ ไม่พบข้อมูลใน (รอแอดมินอัปเดตฐานข้อมูลใหม่)\033[0m\n")
            return

        if data.get("status") != "success":
            print(f"\033[1;31m❌ Error:\033[0m {data.get('message','Unknown error')}\n")
            return

        elapsed = (time.perf_counter() - start) * 1000
        rows = data.get("rows", 0)
        print(f"\n\033[1;32m✅ สำเร็จ!\033[0m ค้นหา {q} ใน {elapsed:.2f} ms ({rows:,} rows)\n")

        results = data.get("data", [])
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", q) or "result"
        save_name = f"{safe_name}.txt"

        with open(save_name, "w", encoding="utf-8") as f:
            f.write("\n".join(results))
        print(f"💾 บันทึกผลลัพธ์แล้ว: {os.path.abspath(save_name)}\n")

    except Exception as e:
        print(f"\033[1;31m❌ Error:\033[0m {e}\n")

# ======== MAIN LOOP ========
if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    banner()

    api_key = load_api_key()
    while True:
        if not api_key:
            api_key = input("\033[1;35m🔑 ใส่ API Key สำหรับเชื่อมต่อ DinoShop: \033[0m").strip()
        print("🔍 กำลังตรวจสอบ API Key ...")
        if verify_api_key(api_key):
            print("\033[1;32m✅ API Key ถูกต้อง พร้อมใช้งาน!\033[0m\n")
            save_api_key(api_key)
            break
        else:
            print("\033[1;31m⛔ API Key ไม่ถูกต้อง กรุณาใส่ใหม่อีกครั้ง\n\033[0m")
            api_key = ""

    try:
        while True:
            q = input("\033[1;33m🔍 ใส่คำค้น (URL/โดเมน): \033[0m").strip()
            if not q:
                continue
            t = input("\033[1;33m📌 เลือกโหมด (0=login:pass, 1=url:login:pass) [ไม่เลือก=1]: \033[0m").strip()
            t = int(t) if t in ["0", "1"] else 1
            print()
            query_dinodonut(q, t, api_key)
            print("\033[1;30m" + "-" * 60 + "\033[0m\n")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\033[1;35m👋 ออกจากโปรแกรมแล้วครับ — ขอบคุณที่ใช้ DinoShop API!\033[0m")
        sys.exit(0)
