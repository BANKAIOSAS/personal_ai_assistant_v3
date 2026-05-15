import asyncio
import threading
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from .views import ai_god


BOT_TOKEN = "8660895856:AAHo5ktMthM8GsZ5XVwOTgKrbcSfj0c6cuc"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    msg = (
        "👋 Welcome! I am your AI Assistant.\n\n"
        "<b>Commands:</b>\n"
        "/profile - Personal information\n"
        "/tasks - Task manager\n"
        "/schedule - Academic schedule\n"
        "Send any message to chat with AI."
    )
    await message.answer(msg, parse_mode="HTML")


@dp.message(Command("profile"))
async def show_profile(message: types.Message):
    data = ai_god.get_profile_data()
    if not data:
        await message.answer("Profile is empty.")
        return
    res = "\n".join([f"🔹 <b>{r[0]}</b>: {r[1]}" for r in data])
    await message.answer(f"👤 <b>Your Profile:</b>\n\n{res}", parse_mode="HTML")


@dp.message(Command("tasks"))
async def show_tasks(message: types.Message):
    data = ai_god.get_tasks_data()
    if not data:
        await message.answer("No tasks found.")
        return
    res = "\n".join([f"{'✅' if r[1] else '⏳'} {r[0]}" for r in data])
    await message.answer(f"✅ <b>Task List:</b>\n\n{res}", parse_mode="HTML")


@dp.message(Command("schedule"))
async def show_schedule(message: types.Message):
    data = ai_god.get_schedule_data()
    if not data:
        await message.answer("Schedule is empty.")
        return
    res = "\n".join([f"📅 <b>{r[0]}</b>: {r[1]}" for r in data])
    await message.answer(f"🕒 <b>Your Schedule:</b>\n\n{res}", parse_mode="HTML")


@dp.message(F.text & ~F.text.startswith('/'))
async def ai_handler(message: types.Message):
    if not message.text.strip():
        await message.reply("Please Send A Non-Empty Message")
        return
    await bot.send_chat_action(message.chat.id, "typing")
    answer = ai_god.ask_ai(message.text)
    if not answer or not answer.strip():
        answer = "Sorry, I couldn't generate a response."
    ai_god.save_log(message.text, answer)
    await message.reply(answer)


def start_bot_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("Bot is running in a background thread...")
    loop.run_until_complete(dp.start_polling(bot))


def run_bot_in_thread():
    bot_thread = threading.Thread(target=start_bot_loop, daemon=True)
    bot_thread.start()

