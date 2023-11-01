from dispatcher import dp
from aiogram import types
from aiogram_calendar import simple_cal_callback, SimpleCalendar
from aiogram.dispatcher.filters import Text
from datetime import datetime
from database import database
from src.keyboard import menu_kb


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(
    callback_query: types.CallbackQuery, callback_data: dict
):
    selected, date = await SimpleCalendar().process_selection(
        callback_query, callback_data
    )
    if selected:
        uid = callback_query.message.chat.id
        new_datetime = datetime.combine(date, datetime.min.time())
        await callback_query.message.answer(
            f'You selected {date.strftime("%d/%m/%Y")}', reply_markup=menu_kb
        )
        if new_datetime > datetime.now():
            await callback_query.message.answer(
                f"You selected future date. There is two variants :\n\
            1) You are silly \n\
            2) You are pentester\n\n\
            Your time starts now: "
                + datetime.now().isoformat(),
                reply_markup=menu_kb,
            )
            new_datetime = datetime.now()
        database.update(uid, new_datetime)


@dp.message_handler(Text(equals=["Open Calendar", "Restart"], ignore_case=True))
async def nav_cal_handler(message: types.Message):
    await message.answer(
        "Please select a date: ", reply_markup=await SimpleCalendar().start_calendar()
    )


@dp.message_handler(Text("Not now"))
async def start_challenge_now(message: types.Message):
    await message.reply("Ok, you nofap challenge begin now.", reply_markup=menu_kb)
