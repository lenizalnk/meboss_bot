import logging
import re
import pandas as pd

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from settings import API_TOKEN, REPAIR_CHAT_ID
from messages import get_message_text


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)

storage = JSONStorage("states.json")

dp = Dispatcher(bot, storage=storage)

# REPAIR_CHAT_ID = -1001514327950

# db = pd.read_csv("products.csv")
# print(db.text())

class StateMachine(StatesGroup):
    main_state = State()
    view_catalog_state = State()
    can_it_be_repaired_state = State()



# START
@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
         .add("💺 Вывести каталог", "🧾 Выставить счёт", "📦 Рассчитать стоимость доставки","🛠 Ремонт кресел и стульев")

    await message.reply(get_message_text("hello"), reply_markup=markup, parse_mode="html")
    await StateMachine.main_state.set()
    logging.info(f"{message.from_user.username}: {message.text}")
# end START


@dp.message_handler(state=StateMachine.main_state)
async def request_for_bot(message: types.Message, state: FSMContext):
    # записываем всё, что человек спросил у бота
    async with state.proxy() as data:
        if "request_for_bot" not in data:
            data["request_for_bot"] = []
        data["request_for_bot"].append(message.text)

    if re.fullmatch(".*Вывести каталог", message.text):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Для офиса", "Для дома")
        await message.reply(get_message_text("catalog_main"), reply_markup=markup, parse_mode="html")
        await StateMachine.view_catalog_state.set()

    elif (re.fullmatch(".*став.*сч.*", message.text) or re.fullmatch(".*сч.*", message.text)) and not re.fullmatch(".*доставк.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ ПО ВЫСТАВЛЕНИЮ СЧЕТОВ")
    elif re.fullmatch(".*реж.*раб.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ ПО режиму работы")
    elif re.fullmatch(".*доставк.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ ПО доставке")
    elif re.fullmatch(".*для.*офис.*", message.text):
        await message.reply(text="Огонь, вам нужен стул для офиса")
    elif re.fullmatch(".*для.*дома.*", message.text):
        await message.reply(text="Вам нужен стул для дома")


@dp.message_handler(state=StateMachine.view_catalog_state)
async def view_catalog(message: types.Message, state: FSMContext):
    if message.text == "Для офиса":
        await message.reply(text="Огонь, вам нужен стул для офиса")
    #     если есть кресла по акции, вывести их, если нет, то вывести категории кресел
    #     with open('products.csv') as f:

    elif message.text == "Для дома":
        await message.reply(text="Вам нужен стул для дома")

@dp.callback_query_handler(text_startswith="catalog", state=StateMachine.main_state)
async def main_state_handler(call: types.CallbackQuery, state: FSMContext):

    catalog_keyboard = InlineKeyboardMarkup()
    catalog_keyboard.add(InlineKeyboardButton("Кресла по акции", callback_data="order_pizza_"))
    catalog_keyboard.add(InlineKeyboardButton("Кресла офисные", callback_data="order_pizza_"))
    catalog_keyboard.add(InlineKeyboardButton("Стулья офисные", callback_data="order_pizza_"))
    catalog_keyboard.add(InlineKeyboardButton("Барные стулья", callback_data="order_pizza_"))
    catalog_keyboard.add(InlineKeyboardButton("Геймерские кресла", callback_data="order_pizza_"))
    catalog_keyboard.add(InlineKeyboardButton("Кресла детские", callback_data="order_pizza_"))

    await call.message.answer(get_message_text("catalog_main"), reply_markup=catalog_keyboard)
    await call.answer()


@dp.message_handler(state=StateMachine.can_it_be_repaired_state)
async def handle(message: types.Message, state: FSMContext):
    await message.answer(message.text)
    await StateMachine.main_state.set()





    # for row in reader:
    #     if row['category'] == "office":
    #
    #
    #     print(row)
    #     print(row['first_name'], row['last_name'])




# ------------
# обработчик группы файлов
from typing import List, Union
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

class AlbumMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            return

        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()  # Tell aiogram to cancel handler for this group element
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict):
        """Clean up after handling our album."""
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]
# ------------
# end обработчик группы файлов


@dp.message_handler(content_types=['photo'], state="*")
async def handle_docs_photo(message: types.Message, state: FSMContext):
    await bot.send_photo(REPAIR_CHAT_ID, photo=message.photo[-1].file_id, caption=message.caption)

@dp.message_handler(is_media_group=True, content_types=types.ContentType.ANY)
async def handle_albums(message: types.Message, album: List[types.Message]):
    # """This handler will receive a complete album of any type."""
    media_group = types.MediaGroup()
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id
        try:
            # We can also add a caption to each file by specifying `"caption": "text"`
            media_group.attach({"media": file_id, "type": obj.content_type})
        except ValueError:
            return await message.answer("This type of album is not supported by aiogram.")

    # await message.answer_media_group(media_group)
    await bot.send_media_group(REPAIR_CHAT_ID, media_group)

# @dp.message_handler(state="*")
# async def handle_question_to_bot(message: types.Message, state: FSMContext):


    #     markup = ReplyKeyboardMarkup(resize_keyboard=True).add("Пропустить")
    #     await message.reply(get_message_text("email_ok"), reply_markup=markup)
    #     await StateMachine.register_waiting_address_state.set()
    # else:
    #     await message.reply(get_message_text("email_bad"))


# @dp.message_handler(state=StateMachine.can_it_be_repaired_state)
# async def handle_registered(message: types.Message, state: FSMContext):
#     # if message.text == "Удалить аккаунт":


# @dp.message_handler(commands = ['start'])
# async def main(message: types.Message):
#     # строка, чтобы отправить что-нибудь в группу
#     await bot.send_message('-1001514327950', 'Hello World')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)