import logging
import random
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatMemberUpdated 
from aiogram.filters import Command 
from aiogram.enums import ChatMemberStatus 
from datetime import datetime

# 🔑 Bot tokeni va chat ID
BOT_TOKEN = '8018362621:AAFvWGJQjy37b724x83BYmCkdXpni53dbSs'
CHAT_ID = -1002349784905

# 🔧 Bot va dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 📂 SQLite bazani yaratish
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS subscribers (
    tg_id INTEGER PRIMARY KEY,
    full_name TEXT,
    subscribe_date TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS warnings (
    tg_id INTEGER PRIMARY KEY,
    warnings INTEGER DEFAULT 0
)
""")
conn.commit()


def is_advertisement(text: str) -> bool:
    """Reklamani tekshiruvchi funksiya"""
    return "@" in text or "http" in text.lower()


@dp.message(Command("start"))
async def start_handler(message: Message):
    """🟢 Foydalanuvchi /start bosganda ishlaydi."""
    if message.from_user is None:
        return

    tg_id = message.from_user.id
    full_name = message.from_user.full_name
    subscribe_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT * FROM subscribers WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO subscribers (tg_id, full_name, subscribe_date) VALUES (?, ?, ?)",
                       (tg_id, full_name, subscribe_date))
        conn.commit()
        response_text = f"✅ {full_name}, obuna bo‘ldingiz!"
    else:
        response_text = f"ℹ️ {full_name}, siz allaqachon obuna bo‘lgansiz!"

    await message.reply(response_text)


@dp.chat_member()
async def welcome_new_member(event: ChatMemberUpdated):
    """👋 Yangi a’zoni bazaga qo‘shish va unga salom berish."""
    if event.new_chat_member.status == ChatMemberStatus.MEMBER:
        new_user = event.new_chat_member.user
        full_name = new_user.full_name
        tg_id = new_user.id
        subscribe_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("SELECT * FROM subscribers WHERE tg_id = ?", (tg_id,))
        user = cursor.fetchone()

        if not user:
            cursor.execute("INSERT INTO subscribers (tg_id, full_name, subscribe_date) VALUES (?, ?, ?)",
                           (tg_id, full_name, subscribe_date))
            conn.commit()

        welcome_messages = [
            f"👋 Salom {full_name}, guruhimizga xush kelibsiz!",
            f"✅ {full_name}, sizni guruhda ko‘rib turganimizdan xursandmiz!",
            f"🌟 Assalomu alaykum, {full_name}! Guruhga xush kelibsiz!",
        ]

        await bot.send_message(event.chat.id, text=random.choice(welcome_messages))


@dp.message()
async def check_for_ads(message: Message):
    """🚫 Reklama tekshiruvi va foydalanuvchini chiqarish"""
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    if message.text and is_advertisement(message.text):
        await message.delete()

        cursor.execute("SELECT warnings FROM warnings WHERE tg_id = ?", (user_id,))
        user_warnings = cursor.fetchone()

        if user_warnings is None:
            cursor.execute("INSERT INTO warnings (tg_id, warnings) VALUES (?, ?)", (user_id, 1))
            conn.commit()
            await message.answer(f"⚠️ {full_name}, reklama taqiqlangan! Agar yana tashlasangiz, guruhdan chiqarilasiz.")
        else:
            warnings_count = user_warnings[0] + 1
            cursor.execute("UPDATE warnings SET warnings = ? WHERE tg_id = ?", (warnings_count, user_id))
            conn.commit()

            if warnings_count >= 3:
                await bot.ban_chat_member(message.chat.id, user_id)
                await message.answer(f"🚫 {full_name}, siz 3 marta reklama tashlaganingiz sababli guruhdan chiqarildingiz!")
            else:
                await message.answer(f"⚠️ {full_name}, bu {warnings_count}-ogohlantirish! 3-ogohlantirishdan keyin guruhdan chiqarilasiz!")


async def main():
    """🔄 Botni ishga tushirish"""
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
