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

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    
    # Проверка на повторную регистрацию
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
        "📝 Пожалуйста, введите ваше Имя и Фамилию.\nЭто необходимо для сверки вас в базе зарегестрированных пользователей Тинькофф через нашу реферальную ссылку\n"
        "Пример: Иван Иванов",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Form.name)

@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    data = load_data()
    user_id = str(message.from_user.id)
    full_name = message.text.strip()
    
    # Проверка формата ввода
    if len(full_name.split()) < 2:
        await message.answer("❗ Пожалуйста, введите и Имя, и Фамилию!")
        return
        
    # Проверка на существующую запись
    if any(user_id in entry for entry in data.values()):
        await message.answer("❗ Вы уже участвуете в розыгрыше!")
        await state.clear()
        return
    
    # Сохранение имени во временное состояние
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
    
    # Получаем данные из состояния
    user_data = await state.get_data()
    full_name = user_data["full_name"]
    
    # Проверка формата реферальной ссылки
    if referrer.lower() != "нет" and not referrer.startswith("@"):
        await message.answer("❗ Пожалуйста, укажите имя аккаунта в формате @example или напишите 'нет'")
        return
    
    # Сохранение данных
    data[user_id] = {
        "full_name": full_name,
        "username": message.from_user.username,
        "referrer": referrer if referrer.lower() != "нет" else None
    }
    save_data(data)
    
    referrer_text = f"\nПриглашен: {referrer}" if referrer.lower() != "нет" else ""
    await message.answer(
        f"✅ Спасибо, {full_name}!\n"
        f"Вы успешно зарегистрированы в розыгрыше! 🍀{referrer_text}",
        parse_mode="Markdown"
    )
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
        await state.clear()

@dp.message(Command("cancel"))
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено 😔", reply_markup=types.ReplyKeyboardRemove())

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
