import asyncio
import time
import math
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- КОНФИГУРАЦИЯ (Данные внесены) ---
TOKEN = '8765300244:AAGUklC0ZlKmvAkeP1Xu9I7esf18RIHkl5I'
ADMIN_ID = 7765181495  

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗЫ ДАННЫХ (В памяти) ---
users_db = {}
queue = []
active_chats = {} 
promos = {} 

def get_status(rep):
    if rep >= 45000: return "🏆 Николаевская Легенда"
    if rep >= 27500: return "👟 Прошаренный пешеход"
    if rep >= 20000: return "🏙️ Легенда Ситика"
    if rep >= 13500: return "🌳 Каштановский"
    if rep >= 7500: return "⛲ Знаток Соборной"
    if rep >= 2500: return "🌊 Знакомый с Намыва"
    if rep >= 500: return "🌉 Прохожий с Варваровки"
    return "🐣 Новичок"

def get_user_data(user_id, name="Пользователь"):
    if user_id not in users_db:
        users_db[user_id] = {
            "name": name, "lang": "rus", "reputation": 0,
            "chats_count": 0, "start_time": time.time(),
            "last_bonus": None, "accepted_rules": False
        }
    return users_db[user_id]

def get_main_kb(lang):
    builder = ReplyKeyboardBuilder()
    if lang == "rus":
        btns = ["🔍 Найти собеседника", "⚙️ Настройки", "🏆 Рейтинг", "👤 Мой профиль", "🎁 Бонус", "🎫 Промокоды"]
    else:
        btns = ["🔍 Знайти співрозмовника", "⚙️ Налаштування", "🏆 Рейтинг", "👤 Мій профіль", "🎁 Бонус", "🎫 Промокоди"]
    for btn in btns: builder.add(types.KeyboardButton(text=btn))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

# --- АДМИНКА (ТОЛЬКО ДЛЯ ВАС) ---
@dp.message(Command("createpromo"))
async def create_promo(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID: return
    try:
        args = command.args.split()
        name, acts, reward = args[0], int(args[1]), int(args[2])
        promos[name] = {"activations": acts, "reward": reward, "users": []}
        await message.answer(f"✅ Промокод `{name}` успешно создан!\nАктиваций: {acts}\nНаграда: {reward} реп.")
    except:
        await message.answer("Ошибка! Формат: `/createpromo название кол_во реп`", parse_mode="Markdown")

# --- ПРОМОКОДЫ ---
@dp.message(F.text.in_(["🎫 Промокоды", "🎫 Промокоди"]))
async def promo_menu(message: types.Message):
    await message.answer("💬 Введите промокод сообщением в чат:")

@dp.message(lambda m: m.text in promos)
async def activate_promo(message: types.Message):
    u = get_user_data(message.from_user.id)
    p_code = message.text
    p = promos[p_code]
    if message.from_user.id in p["users"]:
        await message.answer("❌ Вы уже использовали этот код!")
    elif p["activations"] <= 0:
        await message.answer("❌ Промокод больше не действителен.")
    else:
        p["activations"] -= 1
        p["users"].append(message.from_user.id)
        u["reputation"] += p["reward"]
        await message.answer(f"✅ Активировано! +{p['reward']} репутации!\nВаш статус: {get_status(u['reputation'])}")

# --- СИСТЕМА СТАРТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_user_data(message.from_user.id, message.from_user.full_name)
    await message.answer("👋 **Добро пожаловать в Бота Николаевские Анонимы!**\n\nБот создан для анонимного общения с рандомными людьми из города Николаев.", parse_mode="Markdown")
    
    status_msg = (
        "📊 **Расценки и статусы Николаева:**\n"
        "▫️ 500 — Прохожий с Варваровки\n"
        "▫️ 2500 — Знакомый с Намыва\n"
        "▫️ 7500 — Знаток Соборной\n"
        "▫️ 13500 — Каштановский\n"
        "▫️ 20000 — Легенда Ситика\n"
        "▫️ 27500 — Прошаренный пешеход\n"
        "▫️ 45000 — Николаевская Легенда"
    )
    pinned = await message.answer(status_msg, parse_mode="Markdown")
    try: await bot.pin_chat_message(message.chat.id, pinned.message_id)
    except: pass

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="Прочитал ✅", callback_data="accept_rules"))
    await message.answer("⚖️ **Правила:** Будь вежлив, не спамь и уважай земляков!", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "accept_rules")
async def accept_rules(callback: types.CallbackQuery):
    u = get_user_data(callback.from_user.id)
    u["accepted_rules"] = True
    await callback.message.delete()
    await callback.message.answer("🎉 Приятного общения! Воспользуйся меню ниже:", reply_markup=get_main_kb(u["lang"]))

# --- РЕЙТИНГ ---
@dp.message(F.text.in_(["🏆 Рейтинг"]))
async def view_rating(message: types.Message):
    top_users = sorted(users_db.items(), key=lambda x: x[1]['start_time'])[:5]
    res = "👑 **ТОП-5 ЛЮДЕЙ В БОТЕ** 👑\n\n"
    medals = ["🥇", "🥈", "🥉", "👤", "👤"]
    for i, (uid, data) in enumerate(top_users):
        hours = int((time.time() - data["start_time"]) // 3600)
        res += (
            f"{medals[i]} **{data['name']}**\n"
            f"┣ 🏷 Статус: _{get_status(data['reputation'])}_\n"
            f"┣ ⏳ Время: `{hours} ч.`\n"
            f"┣ 💎 Репутация: `{data['reputation']}`\n"
            f"┗ 💬 Чатов: `{data['chats_count']}`\n"
            f"{'—' * 15}\n"
        )
    await message.answer(res, parse_mode="Markdown")

# --- ПРОФИЛЬ ---
@dp.message(F.text.in_(["👤 Мой профиль", "👤 Мій профіль"]))
async def view_profile(message: types.Message):
    u = get_user_data(message.from_user.id)
    hours = int((time.time() - u["start_time"]) // 3600)
    text = (
        f"👤 **ЛИЧНЫЙ ПРОФИЛЬ**\n\n"
        f"┣ **Имя:** `{u['name']}`\n"
        f"┣ **Статус:** _{get_status(u['reputation'])}_\n"
        f"┣ **Репутация:** `{u['reputation']}`\n"
        f"┣ **Время в боте:** `{hours} ч.`\n"
        f"┗ **Всего чатов:** `{u['chats_count']}`\n"
    )
    await message.answer(text, parse_mode="Markdown")

# --- НАСТРОЙКИ ---
@dp.message(F.text.in_(["⚙️ Настройки", "⚙️ Налаштування"]))
async def settings(message: types.Message):
    u = get_user_data(message.from_user.id)
    builder = InlineKeyboardBuilder()
    text_btn = "🌐 Зміна мови (UA/RU)" if u['lang'] == "ukr" else "🌐 Смена языка (RU/UA)"
    builder.add(types.InlineKeyboardButton(text=text_btn, callback_data="change_lang"))
    await message.answer("⚙️ **Настройки бота:**", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "change_lang")
async def change_lang(callback: types.CallbackQuery):
    u = get_user_data(callback.from_user.id)
    u["lang"] = "ukr" if u["lang"] == "rus" else "rus"
    msg = "Мову змінено! 🇺🇦" if u["lang"] == "ukr" else "Язык изменен! 🇷🇺"
    await callback.message.edit_text(msg)
    await callback.message.answer("Клавиатура обновлена 👇", reply_markup=get_main_kb(u["lang"]))
    await callback.answer()

# --- БОНУС ---
@dp.message(F.text.in_(["🎁 Бонус"]))
async def get_bonus(message: types.Message):
    u = get_user_data(message.from_user.id)
    now = datetime.now()
    if u["last_bonus"] and (now - u["last_bonus"]) < timedelta(hours=24):
        await message.answer("❌ Заходи за бонусом завтра!")
    else:
        u["reputation"] += 250
        u["last_bonus"] = now
        await message.answer(f"✅ Тебе начислено 250 репутации!\nТвой статус: {get_status(u['reputation'])}")

# --- ЛОГИКА ЧАТА ---
@dp.message(F.text.in_(["🔍 Найти собеседника", "🔍 Знайти співрозмовника"]))
async def search_partner(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_chats: return await message.answer("Вы уже в чате! Напишите /stop")
    if user_id not in queue:
        if queue:
            p_id = queue.pop(0)
            now = time.time()
            active_chats[user_id] = {"partner": p_id, "start_time": now}
            active_chats[p_id] = {"partner": user_id, "start_time": now}
            users_db[user_id]["chats_count"] += 1
            users_db[p_id]["chats_count"] += 1
            await bot.send_message(user_id, "🤝 Собеседник найден! Можно общаться. Для выхода напиши /stop")
            await bot.send_message(p_id, "🤝 Собеседник найден! Можно общаться. Для выхода напиши /stop")
        else:
            queue.append(user_id)
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(text="Отменить поиск ❌", callback_data="cancel_search"))
            await message.answer("🔎 Ищем собеседника из Николаева...", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cancel_search")
async def cancel_search(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in queue:
        queue.remove(user_id)
        await callback.message.edit_text("❌ Поиск отменен.")
    else:
        await callback.answer("Поиск уже не активен.")

@dp.message(F.text == "/stop")
async def stop_chat(message: types.Message):
    uid = message.from_user.id
    if uid in active_chats:
        info = active_chats.pop(uid)
        pid = info["partner"]
        active_chats.pop(pid, None)
        mins = max(1, math.ceil((time.time() - info["start_time"]) / 60))
        gain = mins * 25
        for i in [uid, pid]:
            users_db[i]["reputation"] += gain
            await bot.send_message(i, f"❌ Чат завершен.\n**Получено репутации:** {gain} (за {mins} мин.)", parse_mode="Markdown")
    else: await message.answer("Вы не в чате.")

@dp.message()
async def chat_handler(message: types.Message):
    uid = message.from_user.id
    if uid in active_chats:
        if message.text: await bot.send_message(active_chats[uid]["partner"], message.text)

async def main():
    print(f"Бот запущен! Админ: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
