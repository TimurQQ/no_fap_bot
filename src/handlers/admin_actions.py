from dispatcher import dp, bot
from aiogram import types
from database import database
from commands import commands

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
