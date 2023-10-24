from dispatcher import dp, bot
from aiogram import types
from aiogram.dispatcher.filters import Text
from datetime import datetime
from aiogram.utils import exceptions
from database import database
from src.keyboard import reply_kb, menu_kb
import random
import os
from logger import noFapLogger
import asyncio

random.seed(datetime.now().timestamp())

async def send_message_safety(chat_id, message, reply_markup, on_success = lambda: {}, on_failure = lambda _: {}):
    try:
        await bot.send_message(chat_id, message, reply_markup=reply_markup)
        on_success()
    except exceptions.BotBlocked as e:
        print(f"Target [ID:{chat_id}]: blocked by user")
        database.update(chat_id, bannedFlag=True)
        on_failure(e)
    except exceptions.ChatNotFound as e:
        print(f"Target [ID:{chat_id}]: invalid user ID")
        database.update(chat_id, bannedFlag=True)
        on_failure(e)
    except exceptions.RetryAfter as e:
        print(f"Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message_safety(chat_id, message, reply_markup, on_success)
    except exceptions.TelegramAPIError as e:
        print(f"Target [ID:{chat_id}]: failed")
        on_failure(e)

@dp.message_handler(Text(equals=["Yes!", "I'm guilty"], ignore_case=True))
async def fapping_reply(message: types.Message):
    message_text = "Oh no, I'll have to reset your work."
    username = message.chat.username
    if not username:
        message_text += "\n\nYou should set nickname for using our bot"
    uid = message.chat.id
    database.update(uid, datetime.now())
    database.user_contexts[uid].getting_response()
    await message.reply(message_text, reply_markup=menu_kb)

@dp.message_handler(Text("No!"))
async def fapping_reply(message: types.Message):
    message_text = "Good job, keep up the good work."
    username = message.chat.username
    if not username:
        message_text += "\n\nYou should set nickname for using our bot"
    uid = message.chat.id
    database.user_contexts[uid].getting_response()
    await message.reply(message_text, reply_markup=menu_kb)

async def checkRating():
    for userStat in database.data.values():
        days = (datetime.now() - userStat.lastTimeFap).days

        if (days < 0 or userStat.isBlocked): continue

        chat = await bot.get_chat(userStat.uid)
        actual_nick = chat.username
        database.update(userStat.uid, newNickName=actual_nick)

        new_day = 0

        if len(userStat.collectedMemes) != 0:
            last_day = int(userStat.collectedMemes[-1].split()[1].split("_")[0])
            new_day = min(last_day + 1, days)
            if (last_day == new_day):
                continue

        if (new_day not in database.cached_memes):
            if (not userStat.isWinner):
                database.update(userStat.uid, winnerFlag=True)
                await send_message_safety(userStat.uid, f"Not enough memes for you :(", reply_markup=menu_kb)
            continue

        database.update(userStat.uid, winnerFlag=False)
        day_memes = database.cached_memes[new_day]
        new_meme = random.choice(day_memes)
        userStat.collectedMemes.append(new_meme)
        noFapLogger.info(f"User {userStat.username}({userStat.uid}) gets meme {new_meme}")
        await send_message_safety(userStat.uid, f"Congratulations!!! You have collected {new_day}-day meme.", reply_markup=menu_kb,
            on_failure=lambda exc: noFapLogger.info(f'ERROR: "{exc}" While sending to user {userStat.username}({userStat.uid})'))
        await send_photo_safety(userStat.uid, new_meme)
    database.update()

async def send_photo_safety(chat_id, file_name):
    with open(os.path.join("storage", "memes", file_name), "rb") as meme_pic:
        try:
            await bot.send_photo(chat_id, meme_pic)
        except Exception as e:
            noFapLogger.info(f"ERROR: {e} while sending meme to user {chat_id} ")

async def sendCheckMessageBroadcast():
    noFapLogger.info("Send broadcast")
    noFapLogger.info_database(database.data)
    for uid in database.data:
        username = database.data[uid].username
        if uid in database.getBlackList():
            noFapLogger.info(f'User: "{username}" has been banned by bot!')
            continue
        message = "Did you fap today?"
        noFapLogger.info(f'Try to send check message: "{message}" to user {username}({uid})')

        await send_message_safety(uid, message, reply_markup=reply_kb,
            on_success=lambda: database.user_contexts[uid].daily_check(),
            on_failure=lambda exc: noFapLogger.info(f'ERROR: "{exc}" While sending to user {username}({uid})')
        )
