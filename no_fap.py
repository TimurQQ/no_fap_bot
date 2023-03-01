from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram.utils import executor
from src.keyboard import reply_kb, start_kb, menu_kb, getInlineSlider
from src.keyboard import choosepage_cb
from src.database import NoFapDB
from datetime import datetime
from src.commands import Commands
from config.config import BOT_TOKEN
import os
import sys
from aiogram.dispatcher.filters import Text
from aiogram_calendar import simple_cal_callback, SimpleCalendar
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random

random.seed(datetime.now().timestamp())

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
database = NoFapDB()
blacklist = database.getBlackList()
commands = Commands()
scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

class BlackListMiddleware(BaseMiddleware):
    def __init__(self):
        super(BlackListMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if message.chat.id in blacklist:
            userStat = database.getStatById(message.chat.id)
            await bot.send_message(message.chat.id,
                "Your statistics: \n" +
                f"@{userStat.username} Stat: {datetime.now() - userStat.lastTimeFap}"
                , reply_markup=types.ReplyKeyboardRemove()
            )
            raise CancelHandler()

srcPath = os.path.join(os.path.dirname(__file__), 'src')
configPath = os.path.join(os.path.dirname(__file__), 'config')
sys.path.extend([srcPath, configPath])

@dp.message_handler(commands=[commands.HelpCommand])
async def show_help(message: types.Message):
    await message.reply(
        f"Hi!\nI am No Fap Bot [created by @timtim2379]!\nOptions:{commands.getAllCommands()}"
    )

@dp.message_handler(commands=[commands.StartCommand])
async def send_welcome(message: types.Message):
    chatId = message.chat.id
    if chatId not in database:
        chat = await bot.get_chat(chatId)
        username = chat.username
        database.addNewUser(chatId, username, datetime.now())

    await message.reply(
        f"Hi!\nI am No Fap Bot [created by @timtim2379]!\nOptions:{commands.getAllCommands()}"
    )

    await message.reply("Choose your last fap day:", reply_markup=start_kb)

@dp.message_handler(Text("Statistics"))
@dp.message_handler(commands=[commands.StatisticsCommand])
async def show_stats(message: types.Message):
    top10List = database.getTop()
    await bot.send_message(message.chat.id,
        "Statistics (1-10):\n" +
        "\n".join([
            f"{i+1}. @{top10List[i].username} Stat: {datetime.now() - top10List[i].lastTimeFap}"\
            for i in range(len(top10List))
         ]), reply_markup = getInlineSlider(0)
    )

@dp.callback_query_handler(choosepage_cb.filter(direction='next'))
async def handle_next_page(query: types.CallbackQuery, callback_data: dict):
    next_page = int(callback_data["page"]) + 1
    topListPart = database.getTop(page = next_page)
    await bot.edit_message_text(
        f"Statistics ({next_page*10 + 1}-{(next_page + 1)*10}):\n" +
        "\n".join([
                f"{next_page*10 + i + 1}. @{topListPart[i].username} Stat: {datetime.now() - topListPart[i].lastTimeFap}"\
                for i in range(len(topListPart))
            ]
        ),
        query.from_user.id,
        query.message.message_id,
        reply_markup=getInlineSlider(next_page)
    )

@dp.callback_query_handler(choosepage_cb.filter(direction='back'))
async def handle_prev_page(query: types.CallbackQuery, callback_data: dict):
    prev_page = int(callback_data["page"]) - 1
    if (prev_page < 0):
        return
    topListPart = database.getTop(page = prev_page)
    await bot.edit_message_text(
        f"Statistics ({prev_page*10 + 1}-{(prev_page + 1)*10}):\n" +
        "\n".join([
                f"{prev_page*10 + i + 1}. @{topListPart[i].username} Stat: {datetime.now() - topListPart[i].lastTimeFap}"\
                for i in range(len(topListPart))
            ]
        ),
        query.from_user.id,
        query.message.message_id,
        reply_markup=getInlineSlider(prev_page)
    )

@dp.message_handler(Text("Not now"))
async def start_challenge_now(message: types.Message):
    await message.reply("Ok, you nofap challenge begin now.", reply_markup=menu_kb)

@dp.message_handler(Text(equals=["Yes!", "I'm guilty"], ignore_case=True))
async def fapping_reply(message: types.Message):
    uid = message.chat.id
    database.update(uid, datetime.now())
    await message.reply("Oh no, I'll have to reset your work.", reply_markup=menu_kb)

@dp.message_handler(Text("No!"))
async def fapping_reply(message: types.Message):
    await message.reply("Good job, keep up the good work.", reply_markup=menu_kb)

@dp.message_handler(Text(equals=["Open Calendar", "Restart"],ignore_case=True))
async def nav_cal_handler(message: types.Message):
    await message.answer("Please select a date: ", reply_markup=await SimpleCalendar().start_calendar())

@dp.message_handler(commands=[commands.BlacklistCommand])
async def get_black_list(message: types.Message):
    await message.answer("BlackList: \n" +
        "\n".join([
            f"@{(await bot.get_chat(userId)).username} is blocked" for userId in blacklist
        ])
    )

@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        uid = callback_query.message.chat.id
        new_datetime = datetime.combine(date, datetime.min.time())
        await callback_query.message.answer(
            f'You selected {date.strftime("%d/%m/%Y")}',
            reply_markup=menu_kb
        )
        if (new_datetime > datetime.now()):
            await callback_query.message.answer(
                f'You selected future date. There is two variants :\n\
            1) You are silly \n\
            2) You are pentester\n\n\
            Your time starts now: ' + datetime.now().isoformat(),
                reply_markup=menu_kb
            )
            new_datetime = datetime.now()
        database.update(uid, new_datetime)

async def checkRating():
    for userStat in database.data.values():
        days = (datetime.now() - userStat.lastTimeFap).days
        chat = await bot.get_chat(userStat.uid)
        actual_nick = chat.username
        database.update(userStat.uid, None, actual_nick)
        if days >= 0:
            if len(userStat.collectedMemes) == 0:
                new_day = 0
            else:
                last_day = int(userStat.collectedMemes[-1].split()[1].split("_")[0])
                new_day = min(last_day + 1, days)
                if (last_day == new_day):
                    continue
            if (new_day not in database.cached_memes):
                if (userStat.isWinner):
                    continue
                database.update(userStat.uid, None, None, True)
                await bot.send_message(userStat.uid, f"Not enough memes for you :(", reply_markup=menu_kb)
                continue
            else:
                database.update(userStat.uid, None, None, False)
            day_memes = database.cached_memes[new_day]
            new_meme = random.choice(day_memes)
            userStat.collectedMemes.append(new_meme)
            await bot.send_message(userStat.uid, f"Congratulations!!! You have collected {new_day}-day meme.", reply_markup=menu_kb)
            with open(os.path.join("storage", "memes", new_meme), "rb") as meme_pic:
                await bot.send_photo(userStat.uid, meme_pic)
    database.update()

async def sendCheckMessageBroadcast():
    for uid in database.data:
        if uid in blacklist:
            await bot.send_message(uid,
                "You are no longer participating in the challenge. \nBut no one forbids collecting memes :)",
                reply_markup=types.ReplyKeyboardRemove()
            )
            continue
        await bot.send_message(uid, "Did you fap today?", reply_markup=reply_kb)

if __name__ == '__main__':
    dp.middleware.setup(BlackListMiddleware())
    scheduler.add_job(sendCheckMessageBroadcast, "cron", day_of_week='mon-sun', hour=21, minute = 00)
    scheduler.add_job(checkRating, "interval", seconds = 60)
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
