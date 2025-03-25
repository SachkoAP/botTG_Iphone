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
        "📝 Пожалуйста, введите ваше Имя и Фамилию.\nЭто необходимо для сверки вас в базе зарегестрированных пользователей Тинькофф через нашу реферальную ссылку"
        "Пример: Иван Иванов\n",
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
        
    # Сохранение данных
    data[user_id] = {
        "full_name": full_name,
        "username": message.from_user.username
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
