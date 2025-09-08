from datetime import datetime

from aiogram import types
from aiogram.dispatcher.filters import Text

from commands import commands
from database import database
from dispatcher import bot, dp
from src.keyboard import choosepage_cb, getInlineSlider


def make_statistics_message(topListPart, callerStat, page):
    return (
        f"Statistics ({page*10 + 1}-{(page + 1)*10}):\n"
        + "\n".join(
            [
                f"{page*10 + i + 1}. @{topListPart[i].username} Stat: {datetime.now() - topListPart[i].lastTimeFap}"
                for i in range(len(topListPart))
            ]
        )
        + f"\n...\n{callerStat[0]}. @{callerStat[1].username} Stat: {datetime.now() - callerStat[1].lastTimeFap}"
    )


@dp.message_handler(Text("Statistics"))
@dp.message_handler(commands=[commands.StatisticsCommand])
async def show_stats(message: types.Message):
    top10List, callerStat = database.getTop(caller=message.chat.id)

    await bot.send_message(
        message.chat.id,
        make_statistics_message(top10List, callerStat, 0),
        reply_markup=getInlineSlider(0, message.chat.id),
    )


@dp.callback_query_handler(choosepage_cb.filter(direction="next"))
async def handle_next_page(query: types.CallbackQuery, callback_data: dict):
    next_page = int(callback_data["page"]) + 1
    topListPart, callerStat = database.getTop(
        page=next_page, caller=callback_data["caller"]
    )
    await bot.edit_message_text(
        make_statistics_message(topListPart, callerStat, next_page),
        query.message.chat.id,
        query.message.message_id,
        reply_markup=getInlineSlider(next_page, callback_data["caller"]),
    )


@dp.callback_query_handler(choosepage_cb.filter(direction="back"))
async def handle_prev_page(query: types.CallbackQuery, callback_data: dict):
    prev_page = int(callback_data["page"]) - 1
    if prev_page < 0:
        return
    topListPart, callerStat = database.getTop(
        page=prev_page, caller=callback_data["caller"]
    )
    await bot.edit_message_text(
        make_statistics_message(topListPart, callerStat, prev_page),
        query.message.chat.id,
        query.message.message_id,
        reply_markup=getInlineSlider(prev_page, callback_data["caller"]),
    )
