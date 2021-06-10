from io import BytesIO
from aiogram import Bot, types
from aiogram.utils import executor
import torchvision.models as models
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ParseMode
# from users import create_user_checker, users
from net import run_style_transfer, unloader, download_cnn
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram import Bot, Dispatcher, executor, types

import config

print('Bot is starting..')
cnn = download_cnn()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)
print('Bot has been started')

counter = 0
styleSize = (0, 0)
contentSize = (0, 0)


@dp.message_handler(commands=['start', 'help'])
async def welcome(message):
    try:
        # create_user_checker(message.from_user.id)

        inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
        item1 = InlineKeyboardButton("Давай!", callback_data='yes')
        item2 = InlineKeyboardButton("Чуть позже", callback_data='no')

        inline_keyboard.add(item1, item2)
        me = await bot.get_me()

        await bot.send_message(message.chat.id, f'Приветствую тебя, *{message.from_user.first_name}*! '
                                                f'Я *{me.first_name}* — бот, созданный, чтобы '
                                                f'переносить стиль одних фотографий на другие. '
                                                f'Начнем?',
                               parse_mode=ParseMode.MARKDOWN,
                               reply_markup=inline_keyboard)
    except Exception as e:
        await message.reply(message, "Ошибка: " + repr(e))


@dp.message_handler(commands=['transfer_style'])
async def transfer(message):
    try:

        # create_user_checker(message.from_user.id)

        inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton("Давай!", callback_data='yes')
        item2 = types.InlineKeyboardButton("Чуть позже.", callback_data='no')

        inline_keyboard.add(item1, item2)

        await bot.send_message(message.chat.id, f'Итак, начнем?',
                               parse_mode='Markdown',
                               reply_markup=inline_keyboard)

    except Exception as e:
        await message.reply(message, "Ошибка: " + repr(e))


@dp.callback_query_handler(lambda call: True)
async def callback_inline(call):
    # create_user_checker(call.from_user.id)

    # try:
    if call.message:
        if call.data == 'yes':
            # users[call.from_user.id].is_getting_photos = True

            await bot.send_message(call.message.chat.id, 'Отлично, тогда отправь мне сначала фото стиля, '
                                                         'а затем фото контента. Жду!')
        elif call.data == 'no':
            await bot.send_message(call.message.chat.id, 'Хорошо, пиши, как понадоблюсь!')

        await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            reply_markup=None)


@dp.message_handler(content_types=['photo'])
async def get_photo(message):
    global counter, styleSize, contentSize
    photo = message.photo[-1]
    print(type(photo))
    photo_id = message.photo[-1].file_id
    photo_width = message.photo[-1].width
    photo_height = message.photo[-1].height
    file = await bot.get_file(photo_id)
    if counter == 0:
        styleSize = (photo_width, photo_height)
        await photo.download(f'images\{message.from_user.id}' + '_style_photo.pickle')
        await bot.send_message(message.chat.id, 'Отлично, теперь отправь фото контента')
        counter += 1
        return
    if counter == 1:
        contentSize = (photo_width, photo_height)
        await photo.download(f'images\{message.from_user.id}' + '_content_photo.pickle')
        await bot.send_message(message.chat.id, 'Фото получил, начинаю работу!')
        await transfer_style(message)
        counter = 0


async def transfer_style(message):
    output = run_style_transfer(cnn,
                                f'images\{message.from_user.id}',
                                styleSize,
                                contentSize,
                                )

    output = unloader(output)

    bio = BytesIO()
    bio.name = f'images\{message.from_user.id}+_result.png'
    output.save(bio, 'PNG')
    bio.seek(0)

    await bot.send_photo(message.chat.id, bio, 'Вот, что у меня получилось')

    inline_keyboard = types.InlineKeyboardMarkup(row_width=2)
    item1 = InlineKeyboardButton("Давай!", callback_data='yes')
    item2 = InlineKeyboardButton("Чуть позже", callback_data='no')
    inline_keyboard.add(item1, item2)

    await bot.send_message(message.chat.id, f'Хочешь перенести стиль еще на одну фотографию?',
                           reply_markup=inline_keyboard)


if __name__ == '__main__':
    executor.start_polling(dp)
