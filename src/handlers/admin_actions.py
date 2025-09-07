from dispatcher import dp, bot
from aiogram import types
from database import database
from commands import commands
import os
from src.constants import LOGS_FOLDER
from no_fap import send_logs

@dp.message_handler(is_admin=True, commands=['ban'])
async def ban_user(message: types.Message):
    args = message.get_args()
    if (len(args) == 0):
        await message.answer(f"Command args passes incorrectly")
        return
    whom = args.split()[0].split("@")[-1]
    uid = database.getUserIDFromNick(whom)
    if (uid is None):
        await message.answer(f"User with provided nickname doesn't exist")
        return
    database.update(uid, bannedFlag=True)
    await message.answer(f"User with nick @{whom} was banned by you :)")

@dp.message_handler(is_admin=True, commands=['unban'])
async def unban_user(message: types.Message):
    args = message.get_args()
    if (len(args) == 0):
        await message.answer(f"Command args passes incorrectly")
        return
    whom = args.split()[0].split("@")[-1]
    uid = database.getUserIDFromNick(whom)
    if (uid is None):
        await message.answer(f"User with provided nickname doesn't exist")
        return
    database.update(uid, bannedFlag=False)
    await message.answer(f"User with nick @{whom} was unbanned by you :)")

@dp.message_handler(is_admin=False, commands=['ban', 'unban'])
async def no_admin_rights_handler(message: types.Message):
    await message.answer(f"You don't have admin rights to do /{message.get_command()}")

@dp.message_handler(commands=[commands.BlacklistCommand])
async def get_black_list(message: types.Message):
    blacklisted_users = database.getBlackList()
    
    if not blacklisted_users:
        await message.answer("BlackList is empty ✅")
        return

    # Формируем список без API вызовов - используем сохраненные usernames
    blacklist_lines = []
    for user in blacklisted_users:
        username = user['username']
        uid = user['uid']
        blacklist_lines.append(f"@{username} (ID: {uid}) is blocked")
    
    # Простое разбиение на части по 4000 символов
    full_text = f"BlackList ({len(blacklisted_users)} users):\n\n" + "\n".join(blacklist_lines)
    
    # Разбиваем текст на куски по 4000 символов
    chunk_size = 4000
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i:i + chunk_size]
        if i == 0:
            await message.answer(chunk)
        else:
            await message.answer(f"BlackList (continued):\n{chunk}")

@dp.message_handler(is_admin=True, commands=['get_logs'])
async def send_logs_manually(message: types.Message):
    """Ручная отправка логов админам"""
    try:
        # Найдем последний файл логов
        log_files = [f for f in os.listdir(LOGS_FOLDER) 
                    if f.startswith('log.') and os.path.isfile(os.path.join(LOGS_FOLDER, f))]
        
        if not log_files:
            await message.answer("❌ Нет файлов логов для отправки")
            return
        
        # Берем последний файл
        latest_log = sorted(log_files)[-1]
        log_path = os.path.join(LOGS_FOLDER, latest_log)
        
        await message.answer(f"📤 Отправляю лог файл: {latest_log}")
        
        # Отправляем лог
        await send_logs(log_path)
        
        await message.answer(f"✅ Лог файл {latest_log} успешно отправлен всем админам!")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке логов: {e}")

@dp.message_handler(is_admin=False, commands=['get_logs'])
async def send_logs_no_admin(message: types.Message):
    await message.answer("❌ У вас нет прав администратора для выполнения /get_logs")
