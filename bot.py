import asyncio
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]

db = sqlite3.connect("anime.db")
db.execute("""
CREATE TABLE IF NOT EXISTS anime (
    code TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    video TEXT
)
""")
db.commit()


class AddAnime(StatesGroup):
    code = State()
    title = State()
    description = State()
    video = State()


bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎌 DIYOR ANIME botiga xush kelibsiz!\n\n"
        "Anime kodini yuboring va videoni oling.\n"
        "Masalan: 001"
    )


@dp.message(Command("myid"))
async def myid(message: Message):
    await message.answer(f"Sizning Telegram ID: {message.from_user.id}")


@dp.message(Command("add"))
async def add(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu buyruq faqat admin uchun.")
        return

    await state.set_state(AddAnime.code)
    await message.answer("Anime kodini yuboring:")


@dp.message(AddAnime.code)
async def get_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip())
    await state.set_state(AddAnime.title)
    await message.answer("Anime nomini yuboring:")


@dp.message(AddAnime.title)
async def get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddAnime.description)
    await message.answer("Anime haqida qisqacha ma'lumot yozing yoki /skip yuboring:")


@dp.message(AddAnime.description)
async def get_description(message: Message, state: FSMContext):
    description = "" if message.text == "/skip" else message.text
    await state.update_data(description=description)
    await state.set_state(AddAnime.video)
    await message.answer("Endi anime videosini yuboring:")


@dp.message(AddAnime.video, F.video)
async def get_video(message: Message, state: FSMContext):
    data = await state.get_data()
    video_id = message.video.file_id

    try:
        db.execute(
            "INSERT OR REPLACE INTO anime VALUES (?, ?, ?, ?)",
            (data["code"], data["title"], data["description"], video_id)
        )
        db.commit()
        await message.answer("✅ Anime muvaffaqiyatli qo‘shildi!")
    except Exception:
        await message.answer("Xatolik yuz berdi. Qayta urinib ko‘ring.")

    await state.clear()


@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Amal bekor qilindi.")


@dp.message(F.text)
async def find_anime(message: Message):
    code = message.text.strip()
    result = db.execute(
        "SELECT title, description, video FROM anime WHERE code = ?",
        (code,)
    ).fetchone()

    if result:
        title, description, video = result
        await message.answer(f"🎬 {title}\n\n{description}")
        await message.answer_video(video)
    else:
        await message.answer("❌ Bunday koddagi anime topilmadi.")


async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN sozlanmagan!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())