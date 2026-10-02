import asyncio
import json
import random
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

BOT_TOKEN = "8793518757:AAHLsjrwZgwY0KujqNSiQNjqDKRDflVqdY8"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def init_db():
    conn = sqlite3.connect("quiz.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score TEXT,
            percentage REAL,
            grade TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_result(user_id, score, percentage, grade):
    conn = sqlite3.connect("quiz.db")
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute(
        "INSERT INTO results (user_id, score, percentage, grade, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, score, percentage, grade, date_str)
    )
    conn.commit()
    conn.close()

def get_results(user_id):
    conn = sqlite3.connect("quiz.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT score, percentage, grade, date FROM results WHERE user_id = ? ORDER BY id DESC LIMIT 5",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def load_questions():
    with open("bot.json", "r", encoding="utf-8") as f:
        return json.load(f)

class QuizStates(StatesGroup):
    answering = State()

def get_grade(percentage):
    if percentage >= 90: return "A'lo 🌟"
    if percentage >= 70: return "Yaxshi 👍"
    if percentage >= 50: return "Qoniqarli 👌"
    return "Yomon  Qayta urinib ko'ring!"

def start_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Testni boshlash 🚀")
    builder.button(text="Natijalarim 📊")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

async def send_question(message_or_call, state: FSMContext):
    data = await state.get_data()
    questions = data['questions']
    current_index = data['current_index']
    
    if current_index >= len(questions):
        correct = data['correct']
        total = len(questions)
        percentage = (correct / total) * 100
        grade = get_grade(percentage)
        score_text = f"{correct}/{total}"
        
        user_id = message_or_call.from_user.id
        save_result(user_id, score_text, percentage, grade)
        
        text = (
            f"🏁 **Test yakunlandi!**\n\n"
            f"📊 Natijangiz: `{score_text}`\n"
            f"📈 Foiz: `{percentage:.1f}%`\n"
            f"📝 Baho: **{grade}**"
        )
        await state.clear()
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.message.answer(text, parse_mode="Markdown", reply_markup=start_keyboard())
        else:
            await message_or_call.answer(text, parse_mode="Markdown", reply_markup=start_keyboard())
        return

    q = questions[current_index]
    options = list(q['options'])
    random.shuffle(options)  
    
    builder = InlineKeyboardBuilder()
    for opt in options:
        builder.button(text=opt, callback_data=f"ans_{opt}")
    builder.adjust(1)
    
    text = f"❓ **{current_index + 1}-savol:**\n\n{q['question']}"
    
    if isinstance(message_or_call, types.CallbackQuery):
        await message_or_call.message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        await message_or_call.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Salom! Bilimingizni sinab ko'rishga tayyormisiz? Pastdagi tugmani bosing.",
        reply_markup=start_keyboard()
    )
@dp.message(F.text == "Testni boshlash 🚀")
async def start_quiz(message: types.Message, state: FSMContext):
    questions = load_questions()
    random.shuffle(questions)
    
    await state.set_state(QuizStates.answering)
    await state.update_data(
        questions=questions,
        current_index=0,
        correct=0,
        answered=False 
    )
    await message.answer("Test boshlandi! Omad yor bo'lsin.", reply_markup=types.ReplyKeyboardRemove())
    await send_question(message, state)

@dp.callback_query(QuizStates.answering, F.data.startswith("ans_"))
async def handle_answer(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    if data.get('answered'):
        await call.answer("Siz bu savolga javob berib bo'ldingiz!", show_alert=True)
        return
        
    await state.update_data(answered=True) 
    
    chosen_answer = call.data[4:]
    questions = data['questions']
    current_index = data['current_index']
    correct_answer = questions[current_index]['answer']
    
    await call.message.edit_reply_markup(reply_markup=None)
    
    if chosen_answer == correct_answer:
        await state.update_data(correct=data['correct'] + 1)
        await call.message.answer(f"✅ To'g'ri! Siz tanladingiz: {chosen_answer}")
    else:
        await call.message.answer(f"❌ Noto'g'ri!\nSiz tanladingiz: {chosen_answer}\nTo'g'ri javob: {correct_answer}")
        
    # Keyingi savolga o'tish
    await state.update_data(current_index=current_index + 1, answered=False)
    await asyncio.sleep(1.5) 
    await send_question(call, state)
    await call.answer()

@dp.message(F.text == "Natijalarim 📊")
@dp.message(Command("natijalarim"))
async def show_results(message: types.Message):
    results = get_results(message.from_user.id)
    if not results:
        await message.answer("Sizda hali saqlangan urinishlar yo'q. Testni boshlang!")
        return
        
    text = "📊 **Oxirgi 5 ta urinishingiz natijalari:**\n\n"
    for i, res in enumerate(results, 1):
        text += f"{i}. 📅 {res[3]} | Natija: `{res[0]}` ({res[1]:.1f}%) | Baho: {res[2]}\n"
        
    await message.answer(text, parse_mode="Markdown")

async def main():
    init_db()
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())