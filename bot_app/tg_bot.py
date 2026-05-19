import os
import html
import asyncio
import threading
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from .views import ai_god

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the environment variables.")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    msg = (
        "👋 Welcome! I am your AI Assistant.\n\n"
        "<b>View:</b>\n"
        "/profile — Personal information\n"
        "/tasks — Task list\n"
        "/schedule — Academic schedule\n\n"
        "<b>Add / Update:</b>\n"
        "/add_task &lt;name&gt; — Add a task\n"
        "/done &lt;name&gt; — Mark task as done\n"
        "/set &lt;key&gt; &lt;value&gt; — Update profile info\n"
        "/add_schedule &lt;day&gt; &lt;discipline&gt; — Add schedule entry\n\n"
        "<b>Manage:</b>\n"
        "/clear &lt;tasks|profile|schedule|history&gt; — Clear data\n\n"
        "Send any message to chat with AI."
    )
    await message.answer(msg, parse_mode="HTML")


@dp.message(Command("profile"))
async def show_profile(message: types.Message):
    data = ai_god.get_profile_data()
    if not data:
        await message.answer("Profile is empty.")
        return
    res = "\n".join([f"🔹 <b>{html.escape(r[0])}</b>: {html.escape(r[1])}" for r in data])
    await message.answer(f"👤 <b>Your Profile:</b>\n\n{res}", parse_mode="HTML")


@dp.message(Command("tasks"))
async def show_tasks(message: types.Message):
    data = ai_god.get_tasks_data()
    if not data:
        await message.answer("No tasks found.")
        return
    res = "\n".join([f"{'✅' if r[1] else '⏳'} {html.escape(r[0])}" for r in data])
    await message.answer(f"✅ <b>Task List:</b>\n\n{res}", parse_mode="HTML")


@dp.message(Command("schedule"))
async def show_schedule(message: types.Message):
    data = ai_god.get_schedule_data()
    if not data:
        await message.answer("Schedule is empty.")
        return
    res = "\n".join([f"📅 <b>{html.escape(r[0])}</b>: {html.escape(r[1])}" for r in data])
    await message.answer(f"🕒 <b>Your Schedule:</b>\n\n{res}", parse_mode="HTML")


@dp.message(Command("add_task"))
async def cmd_add_task(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("Usage: /add_task <task name>")
        return
    task_name = args[1].strip()
    ai_god.add_task(task_name)
    await message.answer(
        f"⏳ Task added: <b>{html.escape(task_name)}</b>",
        parse_mode="HTML"
    )


@dp.message(Command("done"))
async def cmd_done_task(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("Usage: /done <task name or part of it>\nExample: /done lab report")
        return
    success = ai_god.complete_task(args[1].strip())
    if success:
        await message.answer("✅ Task marked as done!")
    else:
        await message.answer("❌ Task not found. Check /tasks for exact names.")


@dp.message(Command("set"))
async def cmd_set_profile(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3 or not args[2].strip():
        await message.answer(
            "Usage: /set <key> <value>\n"
            "Example: /set name Alex\n"
            "Example: /set age 20\n"
            "Example: /set city Almaty"
        )
        return
    ai_god.set_profile(args[1].strip().lower(), args[2].strip())
    await message.answer(f"✅ Saved: <b>{args[1]}</b> = {args[2]}", parse_mode="HTML")


@dp.message(Command("add_schedule"))
async def cmd_add_schedule(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3 or not args[2].strip():
        await message.answer(
            "Usage: /add_schedule <day> <discipline>\n"
            "Example: /add_schedule Monday Python Programming"
        )
        return
    ai_god.add_schedule(args[1].strip(), args[2].strip())
    await message.answer(f"📅 Added to schedule: <b>{args[1]}</b> — {args[2]}", parse_mode="HTML")


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Usage: /clear <target>\n"
            "Targets: <b>tasks</b> | <b>profile</b> | <b>schedule</b> | <b>history</b>",
            parse_mode="HTML"
        )
        return
    table_map = {
        'tasks':    'tasks',
        'profile':  'user_profile',
        'schedule': 'schedule',
        'history':  'chat_logs',
    }
    target = args[1].strip().lower()
    table = table_map.get(target)
    if not table:
        await message.answer("❌ Unknown target. Use: tasks, profile, schedule, or history")
        return
    ai_god.clear_table(table)
    await message.answer(f"🗑 <b>{target}</b> cleared successfully.", parse_mode="HTML")
    

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


@dp.message(F.text.startswith('/'))
async def unknown_command(message: types.Message):
    await message.answer("Unknown command. Please use /start to see available commands.")


def start_bot_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("Bot is running in a background thread...")
    loop.run_until_complete(dp.start_polling(bot))


def run_bot_in_thread():
    bot_thread = threading.Thread(target=start_bot_loop, daemon=True)
    bot_thread.start()

