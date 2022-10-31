import logging
import re
from typing import List

from database import OrdersTable, ProductsTable, FileTable, CustomersTable
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


async def send_photo(message, filename, caption=None, reply_markup=None, parse_mode="html"):
    file_id = FileTable.get_file_id_by_file_name(filename)
    if file_id is None:
        # upload_file
        with open(filename, 'rb') as photo:
            result = await message.answer_photo(
                photo,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            file_id = result.photo[0].file_id
            FileTable.create(telegram_file_id=file_id, file_name=filename)
    else:
        await bot.send_photo(
            message.from_user.id,
            file_id,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )


class StateMachine(StatesGroup):
    main_state = State()
    repair_state = State()
    search_by_name_state = State()
    view_catalog_state = State()
    can_it_be_repaired_state = State()
    get_number_state = State()


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


async def view_product_table(message, select, message_show):
    # комплектующие выводятся с ценой за замену
    if select == "products_by_name":
        table = ProductsTable.select_products_by_name(message.text)
    elif select == "products_by_name_and_category":
        table = ProductsTable.select_products_by_n_and_cat(message.text, "accessories")
    elif select == "products_by_category" and message_show == "accessories_show":
        table = ProductsTable.select_products_by_category("accessories")
    elif select == "products_by_category" and message_show == "product_show":
        table = ProductsTable.select_products_by_category("office")

    for products in table:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Заказать", callback_data=f"order_product_{products.products_id}"))

        if message_show == "accessories_show":
            markup.add(InlineKeyboardButton("Заказать с заменой", callback_data=f"order_repair_{products.products_id}"))
            repair_price = ProductsTable.select_products_by_n_and_cat(products.name, "services")

        if products.category_id != "services":
            if message_show == "accessories_show":
                await send_photo(
                    message,
                    f'data/{products.products_id}.png',
                    caption=get_message_text(message_show, name=products.name, desc=products.description,
                                             price=products.price, rep=repair_price[0].price),
                    reply_markup=markup
                )
            elif message_show == "product_show":
                await send_photo(
                    message,
                    f'data/{products.products_id}_{products.color}.jpg',
                    caption=get_message_text(message_show,
                                             name=products.name,
                                             desc=products.description,
                                             price=products.price),
                    reply_markup=markup
                )


# START
@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
        .add("Отправить запрос оператору", "Вывести каталог кресел")
    await message.reply(get_message_text("hello"), reply_markup=markup, parse_mode="html")
    await StateMachine.main_state.set()
    logging.info(f"{message.from_user.username}: {message.text}")
# end START


@dp.message_handler(commands=['repair'], state="*")
async def repair_command(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
        .add("Каталог комплектующих",
             "Найти деталь по названию",
             "Оставить заявку на ремонт"
             )
    markup.add("Главная страница")
    await StateMachine.repair_state.set()
    await message.reply(get_message_text("repair_order"), reply_markup=markup)


@dp.message_handler(state=StateMachine.repair_state)
async def repair_menu(message: types.Message, state: FSMContext):
    if message.text == "Каталог комплектующих":
        await view_product_table(message, "products_by_category", "accessories_show")

        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Отправить запрос оператору")
        markup.add("Главная страница")
        # message.reply(text="БАЗА ЗНАНИЙ ПО ВЫСТАВЛЕНИЮ СЧЕТОВ")
        await message.answer(get_message_text("need_op"), reply_markup=markup)

    elif message.text == "Найти деталь по названию":
        await StateMachine.search_by_name_state.set()
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Отправить запрос оператору")
        markup.add("Главная страница")
        await message.answer(get_message_text("need_op"), reply_markup=markup)
    elif message.text == "Оставить заявку на ремонт":
        pass
    elif message.text == "Главная страница":
        await StateMachine.main_state.set()
        await send_welcome(message)


# Поиск детали по названию
@dp.message_handler(state=StateMachine.search_by_name_state)
async def search_by_name_state_handler(message: types.Message, state: FSMContext):
    if message.text != "":
        # await view_product_table(message, "products_by_name_and_category", "accessories_show")
        for products in ProductsTable.select_products_by_n_and_cat(message.text, "accessories"):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Заказать",
                                            callback_data=f"order_product_{products.products_id}"))
            markup.add(InlineKeyboardButton("Заказать с услугой замены",
                                            callback_data=f"order_repair_{products.products_id}"))
            repair_price = ProductsTable.select_products_by_n_and_cat(products.name, "services")

            if products.category_id != "services":
                await send_photo(
                    message,
                    f'data/{products.products_id}.png',
                    caption=get_message_text("accessories_show", name=products.name, desc=products.description,
                                             price=products.price, rep=repair_price[0].price),
                    reply_markup=markup
                )

    # await message.reply(get_message_text("search_bad"))

@dp.message_handler(state=StateMachine.main_state)
async def request_for_bot(message: types.Message, state: FSMContext):
    # записываем всё, что человек спросил у бота
    async with state.proxy() as data:
        if "request_for_bot" not in data:
            data["request_for_bot"] = []
        data["request_for_bot"].append(message.text)
    logging.info(f"{message.from_user.username}: {message.text}")

    if re.fullmatch(".*Вывести каталог кресел", message.text):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Для офиса", "Для дома")
        markup.add("Главная страница")
        await message.reply(get_message_text("catalog_main"), reply_markup=markup, parse_mode="html")
        await StateMachine.view_catalog_state.set()
    elif message.text == "Отправить запрос оператору":
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add("Прикрепить фото", "Отменить")
        await message.reply(get_message_text("repair_order"), reply_markup=markup)
        await StateMachine.can_it_be_repaired_state.set()
    elif (re.fullmatch(".*став.*сч.*", message.text) or re.fullmatch(".*сч.*", message.text)) and not re.fullmatch(
            ".*доставк.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ ПО ВЫСТАВЛЕНИЮ СЧЕТОВ")
    elif re.fullmatch(".*реж.*раб.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ ПО режиму работы")
    elif re.fullmatch(".*доставк.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ ПО доставке")
    elif re.fullmatch(".*для.*офис.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ по офисным стульям и креслам")
    elif re.fullmatch(".*для.*дома.*", message.text):
        await message.reply(text="БАЗА ЗНАНИЙ по стульям для дома")


@dp.message_handler(state=StateMachine.view_catalog_state)
async def view_catalog(message: types.Message, state: FSMContext):
    if message.text == "Для офиса":
        await view_product_table(message, "products_by_category", "product_show")
    elif message.text == "Для дома":
        await message.reply(text="База знаний стульев для дома")
    elif message.text == "Главная страница":
        await StateMachine.main_state.set()
        await send_welcome(message)

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


@dp.callback_query_handler(text_startswith="order_", state="*")
async def order_handler(call: types.CallbackQuery, state: FSMContext):
    if call.data.split('_')[1] == "product":
        pass
    elif call.data.split('_')[1] == "repair":
        pass
    await call.message.answer(get_message_text("order_create"))
    await call.answer()


@dp.message_handler(state=StateMachine.can_it_be_repaired_state)
async def handle(message: types.Message, state: FSMContext):
    if message.text == "Прикрепить фото":
        # вкл состояние ожидания номера телефона для связи
        await StateMachine.get_number_state.set()
        await message.answer(get_message_text("get_photo"))
    elif message.text == "Отменить":
        pass
    elif message.text == "Главная страница":
        await StateMachine.main_state.set()
        await send_welcome(message)
    else:
        await message.answer(
            "БАЗА ЗНАНИЙ по вопросу о ремонта. Если находится подходящая деталь, "
            "то выходит карточка товара с надписью Заказать. Заказать с услугой замены")

@dp.message_handler(state=StateMachine.get_number_state)
async def create_order(message: types.Message, state: FSMContext):
    if re.fullmatch("[0-9]{10,}", message.text):
        async with state.proxy() as data:
            data["phone"] = message.text
        await message.reply(get_message_text("repair_order_ok"))
        await bot.send_message(REPAIR_CHAT_ID, message.text)
        await StateMachine.main_state.set()
        await send_welcome(message)
    elif message.text == "Главная страница":
        await StateMachine.main_state.set()
        await send_welcome(message)
    else:
        await message.reply(get_message_text("phone_bad"))


    # if message.text == "Отправить заявку":
    #     pass
        # await bot.send_message(REPAIR_CHAT_ID, message.text)
        # await StateMachine.main_state.set()
        # await message.answer(get_message_text("repair_order_ok"))
        # await send_welcome(message)


@dp.message_handler(content_types=['photo'], state=StateMachine.get_number_state)
async def handle_docs_photo(message: types.Message, state: FSMContext):
    await bot.send_photo(REPAIR_CHAT_ID, photo=message.photo[-1].file_id, caption=message.caption)
    # markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
    #     .add("Отправить заявку", "Отменить")
    # markup.add("Главная страница")
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
        .add("Главная страница")
    # await message.answer(get_message_text("get_number"), reply_markup=markup, parse_mode="html")
    await message.reply(get_message_text("get_number"), reply_markup=markup, parse_mode="html")

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


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
