import logging
import re

from database import OrdersTable, ProductsTable,  FileTable, CustomersTable
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.files import JSONStorage
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from settings import API_TOKEN, REPAIR_CHAT_ID
from messages import get_message_text


logging.basicConfig(level=logging.INFO)

# bot = Bot(token=API_TOKEN)
import os

if "https_proxy" in os.environ:
    proxy_url = os.environ["https_proxy"]
    bot = Bot(token=API_TOKEN, proxy=proxy_url)
else:
    bot = Bot(token=API_TOKEN)


storage = JSONStorage("states.json")

dp = Dispatcher(bot, storage=storage)

async def send_photo(message, filename, caption=None, reply_markup=None):
    file_id = FileTable.get_file_id_by_file_name(filename)
    if file_id is None:
        # upload_file
        with open(filename, 'rb') as photo:
            result = await message.answer_photo(
                photo,
                caption=caption,
                reply_markup=reply_markup
            )
            file_id = result.photo[0].file_id
            FileTable.create(telegram_file_id=file_id, file_name=filename)
    else:
        await bot.send_photo(
            message.from_user.id,
            file_id,
            caption=caption,
            reply_markup=reply_markup
        )
class StateMachine(StatesGroup):
    main_state = State()
    view_catalog_state = State()
    can_it_be_repaired_state = State()


async def send_photo(message, filename, caption=None, reply_markup=None):
    file_id = FileTable.get_file_id_by_file_name(filename)
    if file_id is None:
        # upload_file
        with open(filename, 'rb') as photo:
            result = await message.answer_photo(
                photo,
                caption=caption,
                reply_markup=reply_markup
            )
            file_id = result.photo[0].file_id
            FileTable.create(telegram_file_id=file_id, file_name=filename)
    else:
        await bot.send_photo(
            message.from_user.id,
            file_id,
            caption=caption,
            reply_markup=reply_markup
        )

# START
@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
         .add("💺 Вывести каталог", "📦 Рассчитать стоимость доставки", "Оставить заявку на ремонт кресел и стульев")

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
    logging.info(f"{message.from_user.username}: {message.text}")


    if re.fullmatch(".*Вывести каталог", message.text):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Для офиса", "Для дома")
        await message.reply(get_message_text("catalog_main"), reply_markup=markup, parse_mode="html")
        await StateMachine.view_catalog_state.set()
    elif message.text == "Оставить заявку на ремонт кресел и стульев":
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Далее", "Отменить")
        await message.reply(get_message_text("repair_order"), reply_markup=markup)
        await StateMachine.can_it_be_repaired_state.set()
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
        for products in ProductsTable.select_products_by_category("office"):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Заказать", callback_data=f"order_product_{products.products_id}"))

            await send_photo(
                message,
                f'data/products/{products.products_id}_{products.color}.jpg',
                caption=get_message_text("product_show",
                                             name=products.name,
                                             desc=products.description,
                                             price=products.price),
                reply_markup=markup
            )
    elif message.text == "Для дома":
        await message.reply(text="Вам нужен стул для дома")

# не актуально
@dp.callback_query_handler(text_startswith="catalog", state=StateMachine.main_state)
async def main_state_handler(call: types.CallbackQuery, state: FSMContext):
    catalog_keyboard = InlineKeyboardMarkup()
    catalog_keyboard.add(InlineKeyboardButton("Кресла по акции", callback_data="order_product_"))
    catalog_keyboard.add(InlineKeyboardButton("Кресла офисные", callback_data="order_product_"))
    catalog_keyboard.add(InlineKeyboardButton("Стулья офисные", callback_data="order_product_"))
    catalog_keyboard.add(InlineKeyboardButton("Барные стулья", callback_data="order_product_"))
    catalog_keyboard.add(InlineKeyboardButton("Геймерские кресла", callback_data="order_product_"))
    catalog_keyboard.add(InlineKeyboardButton("Кресла детские", callback_data="order_product_"))

    await call.message.answer(get_message_text("catalog_main"), reply_markup=catalog_keyboard)
    await call.answer()


@dp.message_handler(state=StateMachine.can_it_be_repaired_state)
async def handle(message: types.Message, state: FSMContext):
    if message.text == "Далее":
        await message.answer(message.text)

    # await StateMachine.main_state.set()


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


# @dp.message_handler(commands = ['start'])
# async def main(message: types.Message):
#     # строка, чтобы отправить что-нибудь в группу
#     await bot.send_message('-1001514327950', 'Hello World')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)