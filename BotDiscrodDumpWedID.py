# ===== Auto Install Missing Modules =====
import importlib, subprocess, sys

def ensure_package(pkg: str):
    try:
        importlib.import_module(pkg)
    except ImportError:
        print(f"📦 Installing missing package: {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

for pkg in ["aiohttp", "discord.py", "requests"]:
    ensure_package(pkg)

# ===== Imports =====
import os, io, asyncio, aiohttp, discord
from datetime import datetime
from discord.ext import commands

# ================== CONFIG ==================
DISCORD_TOKEN = "MTQ2MjUyODc5NTIwNTY5NzYzNg.GOk8UK.WdpI4bwZUiQjYdRzzLufQ87H4-vlPp8LfgmDT0" # 🔑 ใสไ1�7 TOKEN DISCORD
API_URL = "http://www.dinodonut.shop/log/dump.php" # ห้ามแก้ไค1�7 API
API_KEY = "dinoshop_T9zRh6uPwB" # 🔑 ใสไ1�7 API Key สำหรับ๢�ชื่อมต่อ DinoShop

COMMAND_PREFIX = "!"
ALLOWED_CHANNEL_IDS = {1462530634621648988} # ห้องที่จะให้งาค1�7 คำสั่งใช้งาน !panel
HISTORY_CHANNEL_ID = 1381652863947636846 # ห้อง๢�ก็บประวัติ

MAX_FILE_MB = 10 # ห้ามแก้ไขจำกัดการส่งไฟล์
CREDIT_NAME = "MKSARUShOP" # ๢�ครดิตแก้ไดไ1�7

# ================== BOT SETUP ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
session: aiohttp.ClientSession | None = None

@bot.event
async def on_ready():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180))
    print(f"✄1�7 บอค1�7 {bot.user} พร้อมใช้งานแล้ค1�7! ใชไ1�7 API {API_URL}")

# ================== UTILITIES ==================
def split_bytes(data: bytes, filename: str, max_mb: int) -> list:
    max_b = max_mb * 1024 * 1024
    if len(data) <= max_b:
        return [discord.File(io.BytesIO(data), filename=filename)]
    files, part = [], 1
    for i in range(0, len(data), max_b):
        chunk = data[i:i + max_b]
        files.append(discord.File(io.BytesIO(chunk), filename=f"{os.path.splitext(filename)[0]}_part{part}.txt"))
        part += 1
    return files

def safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

# ================== API ==================
async def query_api(keyword: str, t: int = 1) -> dict:
    assert session is not None
    params = {"q": keyword, "t": t, "key": API_KEY}
    async with session.get(API_URL, params=params) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        return await resp.json(content_type=None)

# ================== SEARCH CORE ==================
async def do_search(interaction: discord.Interaction, keyword: str, t: int = 1):
    # แสดงข้อความกำลังโหลด
    await interaction.response.send_message(
        f"⏄1�7 กำลังดึงข้อมูลจาค1�7 API สำหรับ `{keyword}` (โหมด={t}) ...",
        ephemeral=True
    )
    try:
        start = datetime.now()
        js = await query_api(keyword, t)
        if js.get("status") != "success":
            return await interaction.edit_original_response(
                content=f"❄1�7 ไม่พบข้อมูค1�7: {js.get('message')}"
            )

        lines = js.get("data", [])
        elapsed = (datetime.now() - start).total_seconds() * 1000
        user = interaction.user
        filename = f"{safe_filename(keyword)}.txt"

        # ✄1�7 แก้ข้อความ๢�ดิมให้๢�ป็นข้อความสรุปสำ๢�ร็ค1�7
        summary = (
            f"✄1�7 **DinoDonut สำ๢�ร็ค1�7!**\n"
            f" 1�7 คำค้ค1�7: `{keyword}`\n"
            f" 1�7 โหมด: `{t}`\n"
            f" 1�7 จำนวค1�7: `{len(lines):,}` บรรทัด\n"
            f" 1�7 ใช้เวลค1�7: `{elapsed:.2f} ms`\n"
            f"📬 ระบบได้ส่งไฟล์ให้คุณทาค1�7 **DM แล้ว**"
        )
        await interaction.edit_original_response(content=summary)

        # 📩 ส่งไฟล์เข้ค1�7 DM
        content = "\n".join(lines).encode("utf-8")
        files = split_bytes(content, filename, MAX_FILE_MB)

        embed = discord.Embed(
            title="📦 DinoDonut Log File",
            description=(
                f"คำค้ค1�7: `{keyword}`\n"
                f"โหมด: `{t}`\n"
                f"จำนวค1�7: `{len(lines):,}`\n"
                f"ใช้เวลค1�7: `{elapsed:.2f} ms`\n"
            ),
            color=discord.Color.green()
        ).set_footer(text=f"Powered by {CREDIT_NAME}")

        try:
            await user.send(embed=embed, files=files)
        except:
            await interaction.followup.send(
                "⚠️ ไม่สามารถส่งไฟล์ทาค1�7 DM ไดไ1�7 (อาจปิดข้อความส่วนตัว)",
                ephemeral=True
            )

        # 🧾 บันทึกประวัติในห้อค1�7
        history = bot.get_channel(HISTORY_CHANNEL_ID)
        if history:
            await history.send(
                embed=discord.Embed(
                    title="📜 ประวัติการค้นหค1�7",
                    description=f"👤 {user.mention}\n🔍 `{keyword}`\nโหมด: {t} | 📄 `{len(lines):,}` บรรทัด",
                    color=discord.Color.blue()
                )
            )

    except Exception as e:
        await interaction.edit_original_response(content=f"❄1�7 ๢�กิดข้อผิดพลาค1�7: `{e}`")


# ================== MODAL ==================
class SearchModal(discord.ui.Modal, title="🔎 ค้นหค1�7 Log ผ่าน DinoDonut"):
    keyword = discord.ui.TextInput(label="คำค้นหค1�7", placeholder="๢�ช่ค1�7 pointblank.zepetto.com", required=True)
    mode = discord.ui.TextInput(label="โหมด (0=login:pass, 1=url:login:pass)", placeholder="ค่าเริ่มต้ค1�7: 1", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        kw = self.keyword.value.strip()
        try:
            t = int(self.mode.value.strip()) if self.mode.value.strip() in ["0", "1"] else 1
        except:
            t = 1
        await do_search(interaction, kw, t)

# ================== PANEL VIEW ==================
class MainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔍 กรอกคำค้นหค1�7", style=discord.ButtonStyle.danger)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModal())

    @discord.ui.button(label="📘 วิธีใช้งาน", style=discord.ButtonStyle.success)
    async def howto(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📖 วิธีใชไ1�7 DinoDonut Bot",
            description=(
                "```"
                "1. กดปุ่ม 🔍 ๢�พื่อกรอกคำค้นหา\n"
                "2. พิมพไ1�7 keyword ๢�ช่ค1�7 pointblank.zepetto.com\n"
                "3. ๢�ลือกโหมด (0 หรือ 1)\n"
                "4. ระบบจะส่งไฟล์กลับทาง DM ๢�ท่านั้น\n"
                "```"
            ),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ================== PANEL COMMAND ==================
@bot.command()
async def panel(ctx):
    if ALLOWED_CHANNEL_IDS and ctx.channel.id not in ALLOWED_CHANNEL_IDS:
        return await ctx.send("❄1�7 ใช้ได้๢�ฉพาะห้องที่อนุญาตเท่านั้ค1�7")

    embed = discord.Embed(
        title="ꔫ・ DinoDonut Log Search",
        description=(
            "```"
            "🔎 ระบบค้นหค1�7 Log ผ่าน DinoDonut\n"
            "📬 ส่งไฟล์เข้ค1�7 DM ๢�ท่านั้ค1�7 (ปลอดภัค1�7)\n"
            "🔗 ตัวอย่างคำค้ค1�7: pointblank.zepetto.com\n"
            "```"
        ),
        color=discord.Color.purple()
    )
    embed.set_image(url="https://img2.pic.in.th/pic/-2000-x-600-px-1900-x-600-pxe4ab378b9446e2a0.png")
    await ctx.send(embed=embed, view=MainView())

# ================== START ==================
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)