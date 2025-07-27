import json
import datetime
from aiogram import Bot, Dispatcher, executor, types
from config import BOT_TOKEN, ADMIN_IDS

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(user_id):
    return user_id in ADMIN_IDS

@dp.message_handler()
async def handle_message(message: types.Message):
    data = load_data()
    parts = message.text.strip().split()
    if not parts:
        return

    cmd = parts[0].lower()
    user_id = str(message.from_user.id)
    username = message.from_user.full_name

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "name": username,
            "zvanie": 0,
            "warns": 0,
            "vygovors": 0,
            "muted_until": None,
            "banned": False
        }

    user_data = data["users"][user_id]

    # ⏱ Авторазмут
    now = datetime.datetime.now()
    muted_until_str = user_data.get("muted_until")
    if muted_until_str:
        try:
            muted_until = datetime.datetime.fromisoformat(muted_until_str)
            if now >= muted_until:
                user_data["muted_until"] = None
                await message.reply("⏱ Мут снят автоматически.")
            else:
                remaining = (muted_until - now).seconds // 60
                return await message.reply(f"❌ Вы в муте ещё {remaining} мин.")
        except:
            user_data["muted_until"] = None
            save_data(data)
            return await message.reply("⚠️ Ошибка с мутом. Он был сброшен.")

    if cmd == "кто" and len(parts) > 1 and parts[1] == "я":
        await message.reply(f"👤 Имя: {username}\n🆔 ID: {user_id}\n🎖 Звание: {user_data['zvanie']}\n⚠️ Вары: {user_data['warns']}\n📍 Выговоры: {user_data['vygovors']}")

    elif cmd == "мое" and parts[1] == "звание":
        await message.reply(f"🎖 Ваше звание: {user_data['zvanie']}")

    elif cmd == "мои" and parts[1] == "выговоры":
        await message.reply(f"📍 У вас {user_data['vygovors']} выговоров.")

    elif cmd == "мут":
        if not is_admin(message.from_user.id):
            return await message.reply("❌ Нет прав.")
        target_id, minutes, reason = parts[1], int(parts[2]), " ".join(parts[3:])
        until_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).isoformat() if minutes > 0 else "9999-12-31T23:59:59"
        data["users"].setdefault(target_id, {"name": "Unknown", "zvanie": 0, "warns": 0, "vygovors": 0, "muted_until": None, "banned": False})
        data["users"][target_id]["muted_until"] = until_time
        await message.reply(f"🔇 Мут выдан {target_id} на {minutes} мин.\nПричина: {reason}")

    elif cmd == "размут":
        if not is_admin(message.from_user.id):
            return await message.reply("❌ Нет прав.")
        target_id = parts[1]
        data["users"].setdefault(target_id, {"name": "Unknown", "zvanie": 0, "warns": 0, "vygovors": 0, "muted_until": None, "banned": False})
        data["users"][target_id]["muted_until"] = None
        await message.reply(f"🔈 Мут снят у пользователя {target_id}.")

    elif cmd == "выдать" and parts[1] == "звание":
        if not is_admin(message.from_user.id):
            return await message.reply("❌ Нет прав.")
        target_id, level = parts[2], int(parts[3])
        data["users"].setdefault(target_id, {"name": "Unknown", "zvanie": 0, "warns": 0, "vygovors": 0, "muted_until": None, "banned": False})
        data["users"][target_id]["zvanie"] = level
        await message.reply(f"✅ Звание {level} выдано пользователю {target_id}.")

    elif cmd == "добавить" and parts[1] == "выговор":
        if not is_admin(message.from_user.id):
            return await message.reply("❌ Нет прав.")
        target_id = parts[2]
        data["users"].setdefault(target_id, {"name": "Unknown", "zvanie": 0, "warns": 0, "vygovors": 0, "muted_until": None, "banned": False})
        data["users"][target_id]["vygovors"] += 1
        await message.reply(f"📍 Выговор добавлен {target_id}.")

    save_data(data)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
