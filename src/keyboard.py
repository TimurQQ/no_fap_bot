from aiogram.types import (
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
)

from aiogram.utils.callback_data import CallbackData

button_yes = KeyboardButton("Yes!")
button_no = KeyboardButton("No!")

reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reply_kb.add(button_no)
reply_kb.add(button_yes)

button_open_cal = KeyboardButton("Open Calendar")
not_now_button = KeyboardButton("Not now")

start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
start_kb.add(button_open_cal)
start_kb.add(not_now_button)

button1 = KeyboardButton("Statistics")
button2 = KeyboardButton("I'm guilty")
button3 = KeyboardButton("Restart")

buttonSuggest = KeyboardButton("Suggest a meme")

menu_kb = (
    ReplyKeyboardMarkup(resize_keyboard=True)
    .row(button1, button2, button3)
    .insert(buttonSuggest)
)

choosepage_cb = CallbackData(
    "choosepage", "direction", "caller", "page"
)  # post:<action>:<amount>


def getInlineSlider(num_page=0, caller=-1):
    inline_page_kb = InlineKeyboardMarkup().row(
        InlineKeyboardButton(
            "◀",
            callback_data=choosepage_cb.new(
                direction="back", page=num_page, caller=caller
            ),
        ),
        InlineKeyboardButton(
            "▶",
            callback_data=choosepage_cb.new(
                direction="next", page=num_page, caller=caller
            ),
        ),
    )
    return inline_page_kb
