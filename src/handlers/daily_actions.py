from dispatcher import dp, bot
from aiogram import types
from aiogram.dispatcher.filters import Text
from datetime import datetime
from aiogram.utils import exceptions
from database import database
from src.keyboard import reply_kb, menu_kb
import random
import os
import json
from logger import noFapLogger
from src.utils.json_encoder import LogJSONEncoder
import shutil
from src.constants import LOG_FILENAME
from src.constants import BACKUP_FOLDER
from datetime import date
import logging

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

async def checkRating():
    for userStat in database.data.values():
        days = (datetime.now() - userStat.lastTimeFap).days
        chat = await bot.get_chat(userStat.uid)
        actual_nick = chat.username
        database.update(userStat.uid, newNickName=actual_nick)
        try:
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
                    database.update(userStat.uid, winnerFlag=True)
                    await bot.send_message(userStat.uid, f"Not enough memes for you :(", reply_markup=menu_kb)
                    continue
                else:
                    database.update(userStat.uid, winnerFlag=False)
                day_memes = database.cached_memes[new_day]
                new_meme = random.choice(day_memes)
                userStat.collectedMemes.append(new_meme)
                noFapLogger.info(f"User {userStat.username}({userStat.uid}) gets meme {new_meme}")
                await bot.send_message(userStat.uid, f"Congratulations!!! You have collected {new_day}-day meme.", reply_markup=menu_kb)
                with open(os.path.join("storage", "memes", new_meme), "rb") as meme_pic:
                    await bot.send_photo(userStat.uid, meme_pic)
        except exceptions.BotBlocked:
            print(f'Bot blocked by user @{chat.username}')
            database.update(userStat.uid, bannedFlag=True)
    database.update()

async def sendCheckMessageBroadcast():
    noFapLogger.info("Send broadcast")
    noFapLogger.info(f"{json.dump(database.data, cls=LogJSONEncoder, indent=4)}")
    for uid in database.data:
        if uid in database.getBlackList():
            message = "You are no longer participating in the challenge. \nBut no one forbids collecting memes :)"
            username = database.data[uid].username
            noFapLogger.info(f"Send check message: {message} to user {username}({uid})")
            await bot.send_message(uid,
                message,
                reply_markup=types.ReplyKeyboardRemove()
            )
            continue
        message = "Did you fap today?"
        noFapLogger.info(f"Send check message: {message} to user {username}({uid})")

        await bot.send_message(uid, message, reply_markup=reply_kb)
        database.user_contexts[uid].daily_check()

def makeBackup():
    # hack for copying logs file. We turn off logger
    noFapLogger.turnOffLogging()

    # copy logs file
    new_filename = "".join(LOG_FILENAME.split(".")[:-1]) + "_" + str(date.today()) + ".log"
    shutil.move(LOG_FILENAME, os.path.join(BACKUP_FOLDER, new_filename))

    # and turn on logger again
    noFapLogger.turnOnLogging()

    # create new empty log file because sometimes we can try access to unexisted file
    open(LOG_FILENAME, 'a').close()
