# markup = InlineKeyboardMarkup()
# markup.add(InlineKeyboardButton("💺 Подобрать кресла", callback_data="catalog"))
# markup.add(InlineKeyboardButton("🛠 Ремонт кресел и стульев", callback_data=f"order_pizza_"))
# markup.add(InlineKeyboardButton("🧾 Выставить счёт", callback_data=f"order_pizza_"))
# markup.add(InlineKeyboardButton("🏷 Узнать о своём заказе", callback_data=f"order_pizza_"))
# # markup.add(InlineKeyboardButton("🛠 Оформить заявку на ремонт", callback_data=f"order_pizza_"))
# markup.add(InlineKeyboardButton("📦 Рассчитать стоимость доставки", callback_data=f"order_pizza_"))
# # markup.add(InlineKeyboardButton("🏪 Почему выбирают наш магазин", callback_data=f"order_pizza_"))


# await bot.send_message(message.from_user.id, text=get_message_text("start_question"))

# await message.reply(get_message_text("hello"), reply_markup=markup, parse_mode="html")