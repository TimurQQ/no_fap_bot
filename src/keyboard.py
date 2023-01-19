from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

button_yes = KeyboardButton('Yes!')
button_no  = KeyboardButton('No!')

reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reply_kb.add(button_no)
reply_kb.add(button_yes)

button_open_cal = KeyboardButton('Open Calendar')

start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
start_kb.add(button_open_cal)

button1 = KeyboardButton('Statistics')
button2 = KeyboardButton("I'm guilty")
button3 = KeyboardButton('Restart')

menu_kb = ReplyKeyboardMarkup().row(
    button1, button2, button3
)