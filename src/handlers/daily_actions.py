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
from src.utils.async_utils import UserProcessingStatus, run_with_semaphore

random.seed(datetime.now().timestamp())

# Кэш для проблемных пользователей, чтобы не проверять их слишком часто
_problematic_users_cache = set()

def clear_problematic_users_cache():
    """Очищает кэш проблемных пользователей. Вызывается периодически."""
    global _problematic_users_cache
    cache_size = len(_problematic_users_cache)
    _problematic_users_cache.clear()
    noFapLogger.info(f"Cleared problematic users cache, removed {cache_size} entries")


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
    if user.uid in database.getBlackListUIDs():
        noFapLogger.info(f'User: "{actual_nick}" has been banned by bot!')
        return
    message = "Did you fap today?"
    noFapLogger.info(f'Try to send check message: "{message}" to user {actual_nick}({user.uid})')

    await send_message_safety(user, message, reply_markup=reply_kb,
        on_success=lambda: database.user_contexts[user.uid].daily_check()
    )


async def process_single_user(user):
    """Обработка одного пользователя. Возвращает статус обработки."""
    days = (datetime.now() - user.lastTimeFap).days

    if (days < 0 or user.isBlocked): 
        return UserProcessingStatus.SKIPPED
    
    # Пропускаем пользователей, которые недавно вызывали ошибки
    if user.uid in _problematic_users_cache:
        return UserProcessingStatus.SKIPPED

    # Безопасное получение информации о чате с обработкой ошибок
    try:
        chat = await bot.get_chat(user.uid)
        actual_nick = chat.username
        database.update(user.uid, newNickName=actual_nick)
    except (ChatNotFound, BotBlocked) as err:
        noFapLogger.warning(f'User {user.username}({user.uid}) is not accessible: {err}. Marking as blocked.')
        database.update(user.uid, bannedFlag=True)
        _problematic_users_cache.add(user.uid)
        return UserProcessingStatus.BLOCKED
    except TelegramAPIError as err:
        noFapLogger.error(f'Telegram API error for user {user.username}({user.uid}): {err}. Skipping this user.')
        _problematic_users_cache.add(user.uid)
        return UserProcessingStatus.ERROR

    new_day = 0
    last_day = 0
    if len(user.collectedMemes) != 0:
        last_day = int(user.collectedMemes[-1].split()[1].split("_")[0])
        new_day = min(last_day + 1, days)
        if last_day == new_day:
            return UserProcessingStatus.SKIPPED

    if (new_day in database.cached_memes):
        database.update(user.uid, winnerFlag=False)
        await sendMemeToUser(user, new_day)
    elif (not user.isWinner):
        database.update(user.uid, winnerFlag=True)
        await send_message_safety(user, f"Not enough memes for you :(", reply_markup=menu_kb)
    else:
        return UserProcessingStatus.SKIPPED

    if days - last_day == 1:
        await sendDailyQuestion(user, actual_nick)
    
    return UserProcessingStatus.PROCESSED


async def checkRating():
    users_count = len(database.data)
    noFapLogger.info(f"Starting async checkRating for {users_count} users")
    
    if users_count == 0:
        noFapLogger.info("No users in database, skipping checkRating")
        return
    
    # Создаем задачи для параллельной обработки пользователей
    tasks = [process_single_user(user) for user in database.data.values()]
    
    # Выполняем все задачи параллельно с ограничением (max 10 одновременно)
    results = await run_with_semaphore(tasks, max_concurrent=10)
    
    # Подсчитываем статистику
    processed_users = results.count(UserProcessingStatus.PROCESSED)
    blocked_users = results.count(UserProcessingStatus.BLOCKED) 
    error_users = results.count(UserProcessingStatus.ERROR)
    skipped_users = results.count(UserProcessingStatus.SKIPPED)
    
    database.update()
    noFapLogger.info(f"Async checkRating completed: {processed_users} processed, {blocked_users} blocked, {error_users} errors, {skipped_users} skipped")


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


async def sendCheckMessageToWinners():
    noFapLogger.info("Send broadcast message for winners")
    for uid in database.data:
        user = database.data[uid]
        if (not user.isWinner):
            continue
        await sendDailyQuestion(user, user.username)