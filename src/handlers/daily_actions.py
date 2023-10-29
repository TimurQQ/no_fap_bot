from dispatcher import dp, bot
from aiogram import types
from aiogram.dispatcher.filters import Text
from datetime import datetime
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, RetryAfter, TelegramAPIError
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


async def sendMemeToUser(user, new_day):
    day_memes = database.cached_memes[new_day]
    new_meme = random.choice(day_memes)
    user.collectedMemes.append(new_meme)
    noFapLogger.info(f"User {user.username}({user.uid}) gets meme {new_meme}")

    await send_message_safety(user, f"Congratulations!!! You have collected {new_day}-day meme.", reply_markup=menu_kb)
    await send_photo_safety(user.uid, new_meme)


async def sendDailyQuestion(user, actual_nick):
    if user.uid in database.getBlackList():
        noFapLogger.info(f'User: "{actual_nick}" has been banned by bot!')
        return
    message = "Did you fap today?"
    noFapLogger.info(f'Try to send check message: "{message}" to user {actual_nick}({user.uid})')

    await send_message_safety(user, message, reply_markup=reply_kb,
        on_success=lambda: database.user_contexts[user.uid].daily_check()
    )


async def checkRating():
    for user in database.data.values():
        days = (datetime.now() - user.lastTimeFap).days

        if (days < 0 or user.isBlocked): continue

        uid = user.uid
        chat = await bot.get_chat(uid)
        actual_nick = chat.username
        database.update(uid, newNickName=actual_nick)

        new_day = 0
        if len(user.collectedMemes) != 0:
            last_day = int(user.collectedMemes[-1].split()[1].split("_")[0])
            new_day = min(last_day + 1, days)
            if (last_day == new_day):
                continue

        if (new_day not in database.cached_memes):
            if (not user.isWinner):
                database.update(user.uid, winnerFlag=True)
                await send_message_safety(user.uid, f"Not enough memes for you :(", reply_markup=menu_kb)
            continue

        database.update(uid, winnerFlag=False)

        await sendMemeToUser(user, new_day)

        await sendDailyQuestion(user, actual_nick)
    database.update()


async def send_message_safety(user, message, reply_markup, on_success = lambda: {}):
    chat_id = user.uid
    try:
        await bot.send_message(chat_id, message, reply_markup=reply_markup)
        on_success()
    except (BotBlocked, ChatNotFound) as err:
        noFapLogger.error(f'"{err}" While sending to user {user.username}({user.uid})')
        database.update(chat_id, bannedFlag=True)
    except RetryAfter as err:
        noFapLogger.error(f'"{err}" While sending to user {user.username}({user.uid})')
        await asyncio.sleep(err.timeout)
        return await send_message_safety(user, message, reply_markup, on_success)
    except TelegramAPIError as err:
        noFapLogger.error(f'"{err}" While sending to user {user.username}({user.uid})')


async def send_photo_safety(chat_id, file_name):
    with open(os.path.join("storage", "memes", file_name), "rb") as meme_pic:
        try:
            await bot.send_photo(chat_id, meme_pic)
        except Exception as exc:
            noFapLogger.error(f'"{exc}" while sending meme to user {chat_id}')
