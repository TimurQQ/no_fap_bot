from dispatcher import dp, bot
from aiogram.dispatcher.filters import Text
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from commands import commands
import os


class SuggestMeme(StatesGroup):
    waitMeme = State()


@dp.message_handler(Text("Suggest a meme"))
@dp.message_handler(commands=[commands.SuggestMemeCommand])
async def process_suggestMemeUsecase(message: types.Message):
    await SuggestMeme.waitMeme.set()
    await message.reply(
        "Please send your meme to this chat. We will consider it:\n🔽🔽🔽🔽🔽🔽🔽🔽"
    )


@dp.message_handler(
    lambda message: message.content_type not in ["photo"], state=SuggestMeme.waitMeme
)
async def process_invalid_meme(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, "This not a meme, btw")
    await bot.send_message(
        message.chat.id,
        "You can continue to use our bot. \
                           \nTo suggest meme you can push button again",
    )
    await state.finish()


@dp.message_handler(content_types=["photo"], state=SuggestMeme.waitMeme)
async def processSuggestedMeme(message: types.Message, state: FSMContext):
    uid = message.chat.id
    userSuggestions = os.path.join("storage", "suggestions", str(uid))
    if not os.path.exists(userSuggestions):
        os.makedirs(userSuggestions)
    countSuggestions = len(os.listdir(userSuggestions))
    await message.photo[-1].download(
        destination_file=os.path.join(userSuggestions, f"{countSuggestions + 1}.jpg")
    )
    await message.reply(
        "Good meme! Thanks. You can continue to use our bot. \
                        Tell your friends about it!\nhttps://t.me/nofap_challenge_bot"
    )
    await state.finish()
