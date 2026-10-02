import asyncio
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)


TOKEN = "8773056115:AAEfcYa0T7sE8Ba1N1rXdeuiKRpmeQFBkrw"
DB_NAME = "todo_bot.db"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
        (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def add_task(user_id, title, due_date):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (user_id, title, due_date) VALUES (?, ?, ?)",
        (user_id, title, due_date)
    )
    conn.commit()
    conn.close()

def get_user_tasks(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, due_date, status FROM tasks WHERE user_id = ?", (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_task_status(task_id, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
    pending = cursor.fetchone()[0]
    conn.close()
    return total, completed, pending


class TaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_due_date = State()

def get_main_menu():
    kb = [
        [KeyboardButton(text="➕ Vazifa qo'shish")],
        [KeyboardButton(text="📋 Vazifalarim"), KeyboardButton(text="📊 Statistika")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_skip_keyboard():
    kb = [[KeyboardButton(text="⏭ O'tkazib yuborish")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_task_inline_keyboard(task_id, status):
    buttons = []
    if status == 'pending':
        buttons.append(InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"done_{task_id}"))
    buttons.append(InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_{task_id}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@dp.message(CommandStart())
async def cmd_start(message: Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Salom, {message.from_user.full_name}! Vazifalar menejeri botiga xush kelibsiz.",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    total, completed, pending = get_stats(message.from_user.id)
    text = (
        "📊 **Sizning hisobotingiz:**\n\n"
        f"🔹 Jami vazifalar: {total} ta\n"
        f"✅ Bajarilgan: {completed} ta\n"
        f"⏳ Kutilmoqda: {pending} ta"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📋 Vazifalarim")
async def show_tasks(message: Message):
    tasks = get_user_tasks(message.from_user.id)
    if not tasks:
        await message.answer("Sizda hozircha hech qanday vazifalar mavjud emas. Yangi vazifa qo'shishingiz mumkin! 😉")
        return

    for task_id, title, due_date, status in tasks:
        status_emoji = "✅" if status == 'completed' else "⏳"
        date_str = f"\n📅 Muddat: {due_date}" if due_date else ""
        text = f"{status_emoji} **{title}**{date_str}"
        
        await message.answer(
            text, 
            reply_markup=get_task_inline_keyboard(task_id, status),
            parse_mode="Markdown"
        )

@dp.message(F.text == "➕ Vazifa qo'shish")
async def start_add_task(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_for_title)
    await message.answer(
        "Vazifa nomini kiriting:", 
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True)
    )

@dp.message(TaskStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Vazifa qo'shish bekor qilindi.", reply_markup=get_main_menu())
        return
        
    await state.update_data(title=message.text)
    await state.set_state(TaskStates.waiting_for_due_date)
    await message.answer(
        "Vazifa muddatini kiriting (Format: `KK.OO.YYYY`, masalan: 25.10.2026):\n"
        "Agar muddat shart bo'lmasa, pastdagi tugmani bosing.",
        reply_markup=get_skip_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(TaskStates.waiting_for_due_date)
async def process_due_date(message: Message, state: FSMContext):
    user_text = message.text
    due_date = None

    if user_text != "⏭ O'tkazib yuborish":
        try:
            parsed_date = datetime.strptime(user_text, "%d.%m.%Y").date()
            if parsed_date < datetime.today().date():
                await message.answer("❌ O'tib ketgan sanani kiritib bo'lmaydi! Iltimos, kelajakdagi sanani kiriting:")
                return
            due_date = user_text
        except ValueError:
            await message.answer("⚠️ Noto'g'ri format! Sanani `KK.OO.YYYY` formatida kiriting (masalan: 15.12.2026):", parse_mode="Markdown")
            return

    data = await state.get_data()
    add_task(message.from_user.id, data['title'], due_date)
    
    await state.clear()
    await message.answer("🎉 Vazifa muvaffaqiyatli saqlandi!", reply_markup=get_main_menu())

@dp.callback_query(F.data.startswith("done_"))
async def callback_task_done(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    update_task_status(task_id, 'completed')
    
    current_text = callback.message.text
    new_text = current_text.replace("⏳", "✅")
    
    await callback.message.edit_text(
        text=f"{new_text}\n\n*Bajarildi!*", 
        reply_markup=get_task_inline_keyboard(task_id, 'completed'),
        parse_mode="Markdown"
    )
    await callback.answer("Vazifa bajarildi deb belgilandi!")

@dp.callback_query(F.data.startswith("del_"))
async def callback_task_delete(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    delete_task(task_id)
    
    await callback.message.edit_text("🗑 Bu vazifa o'chirildi.")
    await callback.answer("Vazifa o'chirildi!")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())