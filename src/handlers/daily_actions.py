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


def memeExistsForUser(userStat, new_day) -> bool:
    if (new_day in database.cached_memes):
        return True
    if (not userStat.isWinner):
        database.update(userStat.uid, winnerFlag=True)
    return False


async def sendMemeToUser(userStat, new_day):
    day_memes = database.cached_memes[new_day]
    new_meme = random.choice(day_memes)
    userStat.collectedMemes.append(new_meme)
    noFapLogger.info(f"User {userStat.username}({userStat.uid}) gets meme {new_meme}")

    await send_message_safety(userStat.uid, f"Congratulations!!! You have collected {new_day}-day meme.", reply_markup=menu_kb)
    await send_photo_safety(userStat.uid, new_meme)


async def sendDailyQuestion(userStat, actual_nick):
    if userStat.uid in database.getBlackList():
        noFapLogger.info(f'User: "{actual_nick}" has been banned by bot!')
        return
    message = "Did you fap today?"
    noFapLogger.info(f'Try to send check message: "{message}" to user {actual_nick}({userStat.uid})')

    await send_message_safety(userStat.uid, message, reply_markup=reply_kb,
        on_success=lambda: database.user_contexts[userStat.uid].daily_check()
    )


async def checkRating():
    for userStat in database.data.values():
        days = (datetime.now() - userStat.lastTimeFap).days

        if (days < 0 or userStat.isBlocked): continue

        uid = userStat.uid
        chat = await bot.get_chat(uid)
        actual_nick = chat.username
        database.update(uid, newNickName=actual_nick)

        new_day = 0
        if len(userStat.collectedMemes) != 0:
            last_day = int(userStat.collectedMemes[-1].split()[1].split("_")[0])
            new_day = min(last_day + 1, days)
            if (last_day == new_day):
                continue

        if not memeExistsForUser(userStat, new_day):
            await send_message_safety(uid, f"Not enough memes for you :(", reply_markup=menu_kb)
            continue

        database.update(uid, winnerFlag=False)

        await sendMemeToUser(userStat, new_day)

        await sendDailyQuestion(userStat, actual_nick)
    database.update()


async def send_message_safety(chat_id, message, reply_markup, on_success = lambda: {}):
    try:
        await bot.send_message(chat_id, message, reply_markup=reply_markup)
        on_success()
    except exceptions.BotBlocked as e:
        noFapLogger.error(f"Target [ID:{chat_id}]: blocked by user")
        database.update(chat_id, bannedFlag=True)
    except exceptions.ChatNotFound as e:
        noFapLogger.error(f"Target [ID:{chat_id}]: invalid user ID")
        database.update(chat_id, bannedFlag=True)
    except exceptions.RetryAfter as e:
        noFapLogger.error(f"Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message_safety(chat_id, message, reply_markup, on_success)
    except exceptions.TelegramAPIError as e:
        noFapLogger.error(f"Target [ID:{chat_id}]: failed")


async def send_photo_safety(chat_id, file_name):
    with open(os.path.join("storage", "memes", file_name), "rb") as meme_pic:
        try:
            await bot.send_photo(chat_id, meme_pic)
        except Exception as exc:
            noFapLogger.error(f'"{exc}" while sending meme to user {chat_id}')
