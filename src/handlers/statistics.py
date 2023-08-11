from dispatcher import dp, bot
from aiogram.dispatcher.filters import Text
from commands import commands
from aiogram import types
from database import database
from datetime import datetime
from src.keyboard import getInlineSlider
from src.keyboard import choosepage_cb

@dp.message_handler(Text("Statistics"))
@dp.message_handler(commands=[commands.StatisticsCommand])
async def show_stats(message: types.Message):
    top10List, callerStat = database.getTop(caller=message.chat.id)

    await bot.send_message(message.chat.id,
        "Statistics (1-10):\n" +
        "\n".join([
            f"{i+1}. @{top10List[i].username} Stat: {datetime.now() - top10List[i].lastTimeFap}"\
            for i in range(len(top10List)) if top10List[i].username
         ]) +
         f"\n...\n{callerStat[0]}. @{callerStat[1].username} Stat: {datetime.now() - callerStat[1].lastTimeFap}",
            reply_markup = getInlineSlider(0, message.chat.id))

@dp.callback_query_handler(choosepage_cb.filter(direction='next'))
async def handle_next_page(query: types.CallbackQuery, callback_data: dict):
    next_page = int(callback_data["page"]) + 1
    topListPart, callerStat = database.getTop(page = next_page, caller=callback_data["caller"])
    await bot.edit_message_text(
        f"Statistics ({next_page*10 + 1}-{(next_page + 1)*10}):\n" +
        "\n".join([
                f"{next_page*10 + i + 1}. @{topListPart[i].username} Stat: {datetime.now() - topListPart[i].lastTimeFap}"\
                for i in range(len(topListPart))
            ]
        ) +
         f"\n...\n{callerStat[0]}. @{callerStat[1].username} Stat: {datetime.now() - callerStat[1].lastTimeFap}",
        query.from_user.id,
        query.message.message_id,
        reply_markup=getInlineSlider(next_page, callback_data["caller"])
    )

@dp.callback_query_handler(choosepage_cb.filter(direction='back'))
async def handle_prev_page(query: types.CallbackQuery, callback_data: dict):
    prev_page = int(callback_data["page"]) - 1
    if (prev_page < 0):
        return
    topListPart, callerStat = database.getTop(page = prev_page, caller=callback_data["caller"])
    await bot.edit_message_text(
        f"Statistics ({prev_page*10 + 1}-{(prev_page + 1)*10}):\n" +
        "\n".join([
                f"{prev_page*10 + i + 1}. @{topListPart[i].username} Stat: {datetime.now() - topListPart[i].lastTimeFap}"\
                for i in range(len(topListPart))
            ]
        ) +
         f"\n...\n{callerStat[0]}. @{callerStat[1].username} Stat: {datetime.now() - callerStat[1].lastTimeFap}",
        query.from_user.id,
        query.message.message_id,
        reply_markup=getInlineSlider(prev_page, callback_data["caller"])
    )
