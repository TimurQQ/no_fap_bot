from dispatcher import dp, bot
from aiogram import types
from database import database
from commands import commands
from src.logger import noFapLogger

@dp.message_handler(is_admin=True, commands=['ban'])
async def ban_user(message: types.Message):
    args = message.get_args()
    noFapLogger.info(f"User {message.chat.username}({message.from_user.id}) has tried to ban with comand {args}")
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
    noFapLogger.info(f"User {message.chat.username}({message.from_user.id}) has tried to unban with comand {args}")
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
    noFapLogger.info(f"User {message.chat.username}({message.from_user.id}) has tried to ban but he don't have rights")
    await message.answer(f"You don't have admin rights to do /{message.get_command()}")

@dp.message_handler(commands=[commands.BlacklistCommand])
async def get_black_list(message: types.Message):
    noFapLogger.info(f"User {message.chat.username}({message.from_user.id}) has asked blacklist")
    await message.answer("BlackList: \n" +
        "\n".join([
            f"@{(await bot.get_chat(userId)).username} is blocked" for userId in database.getBlackList()
        ])
    )
