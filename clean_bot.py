import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8295622572:AAG9h6E6c2BSzHRQ-LGV_MWLh6-eFzHlfSc"
MANAGER_USERNAME = "@cleanwithlove"

logging.basicConfig(level=logging.INFO)

# Состояния
SELECTING_TARIFF, SELECTING_AREA, ADDING_SERVICE, AWAITING_QUANTITY = range(4)

# Таблица тарифов (интервалы: 0-30, 31-60, 61-90, 91-120, 121-150, 151-180, 181-210)
TARIFF_PRICES = {
    "Стандарт": [5200, 7260, 9110, 10770, 12340, 14040, 14190],
    "Эксперт-регуляр": [7140, 10160, 12800, 14760, 17420, 19480, 21420],
    "Эксперт-макс": [9680, 13550, 15730, 21380, 23230, 25890, 28560],
    "Премиум": [21180, 26740, 31220, 41450, 45010, 53850, 62190],
    "Уборка после ремонта (полностью пустая)": [8830, 11980, 14040, 18740, 20450, 23720, 26860],
    "Уборка после ремонта (новая мебель)": [11860, 15610, 18150, 24290, 26620, 30860, 35090],
    "Уборка после ремонта (жилая)": [14400, 19120, 21900, 29170, 32070, 37030, 42110]
}

# Дополнительные услуги (название, цена за ед, единица измерения, тип)
EXTRA_SERVICES = {
    "Химчистка стула со спинкой": {"price": 450, "unit": "шт", "need_qty": True},
    "Стул в виде кресла": {"price": 550, "unit": "шт", "need_qty": True},
    "Химчистка диванных подушек": {"price": 300, "unit": "шт", "need_qty": True},
    "Пылесос (пол, ковролин)": {"price": 50, "unit": "м²", "need_qty": True},
    "Мытьё зеркал": {"price": 250, "unit": "м²", "need_qty": True},
    "Мытьё пола": {"price": 80, "unit": "м²", "need_qty": True},
    "Мытьё стен": {"price": 120, "unit": "м²", "need_qty": True},
    "Мытьё потолка": {"price": 100, "unit": "м²", "need_qty": True},
    "Мытьё двери": {"price": 250, "unit": "шт", "need_qty": True},
    "Вынос мусора (5 кг)": {"price": 250, "unit": "5 кг", "need_qty": True},
    "Стирка": {"price": 300, "unit": "загрузка", "need_qty": True},
    "Глажка": {"price": 1000, "unit": "час", "need_qty": True},
    "Развесить шторы": {"price": 600, "unit": "комплект", "need_qty": True},
    "Снять шторы": {"price": 450, "unit": "комплект", "need_qty": True},
    "Мытьё жалюзи": {"price": 300, "unit": "м²", "need_qty": True},
    "Мытьё радиатора": {"price": 600, "unit": "шт", "need_qty": True},
    "Мытьё люстры": {"price": 300, "unit": "шт", "need_qty": True},
    "Обработка штор паром": {"price": 500, "unit": "комплект", "need_qty": True},
    "Забрать ключи": {"price": 300, "unit": "", "need_qty": False},
    "Вернуть ключи": {"price": 300, "unit": "", "need_qty": False},
    "Особые поручения": {"price": 300, "unit": "", "need_qty": False},
    "Мытьё обуви": {"price": 150, "unit": "пара", "need_qty": True},
    "Обработка игрушек паром": {"price": 300, "unit": "шт", "need_qty": True},
    "Обработка Антидождь": {"price": 100, "unit": "м²", "need_qty": True},
    "Мытьё душевой кабины": {"price": 1500, "unit": "", "need_qty": False},
    "Мытьё санузла": {"price": 2500, "unit": "м²", "need_qty": True},
    "Уборка кухни (Эксперт до 30м²)": {"price": 150, "unit": "м²", "need_qty": True},
    "Обработка мебели паром": {"price": 150, "unit": "место", "need_qty": True},
    "Мытье посуды": {"price": 500, "unit": "раковина", "need_qty": True},
    "Мытье окон": {"price": 380, "unit": "м²", "need_qty": True},
    "Мытье окон в холод": {"price": 450, "unit": "м²", "need_qty": True},
    "Раскладка вещей": {"price": 500, "unit": "", "need_qty": False},
    "Протирка мелких предметов": {"price": 500, "unit": "", "need_qty": False},
    "Мытье микроволновки": {"price": 600, "unit": "шт", "need_qty": True},
    "Мытье духовки": {"price": 1000, "unit": "шт", "need_qty": True},
    "Мытье кухонного гарнитура": {"price": 1300, "unit": "пог.м", "need_qty": True},
    "Мытье плиты без духовки": {"price": 1000, "unit": "шт", "need_qty": True},
    "Мытье плиты с духовкой": {"price": 1500, "unit": "шт", "need_qty": True},
    "Мытье посудомойки": {"price": 450, "unit": "шт", "need_qty": True},
    "Мытье вытяжки": {"price": 800, "unit": "шт", "need_qty": True},
    "Мытьё холодильника": {"price": 1000, "unit": "шт", "need_qty": True},
    "Мытьё стиральной машины": {"price": 400, "unit": "шт", "need_qty": True},
    "Мытьё смесителя": {"price": 500, "unit": "шт", "need_qty": True},
    "Химчистка ковров": {"price": 250, "unit": "м²", "need_qty": True},
    "Химчистка матрасов": {"price": 400, "unit": "м²", "need_qty": True},
    "Химчистка диванов": {"price": 800, "unit": "место", "need_qty": True},
    "Химчистка стула без спинки": {"price": 300, "unit": "шт", "need_qty": True},
}

# Хранилище данных пользователей
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"tariff": None, "area": None, "base_price": 0, "services": [], "area_value": 0}
    
    keyboard = [[InlineKeyboardButton(name, callback_data=f"tariff_{i}")] for i, name in enumerate(TARIFF_PRICES.keys())]
    await update.message.reply_text("🧹 Добро пожаловать в клининговую компанию CleanWithLove!\n\nВыберите тип уборки:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_TARIFF

async def tariff_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    tariff_index = int(query.data.split("_")[1])
    tariff_name = list(TARIFF_PRICES.keys())[tariff_index]
    user_data[user_id]["tariff"] = tariff_name
    
    keyboard = [
        [InlineKeyboardButton("0-30 м²", callback_data="area_0_30")],
        [InlineKeyboardButton("31-60 м²", callback_data="area_31_60")],
        [InlineKeyboardButton("61-90 м²", callback_data="area_61_90")],
        [InlineKeyboardButton("91-120 м²", callback_data="area_91_120")],
        [InlineKeyboardButton("121-150 м²", callback_data="area_121_150")],
        [InlineKeyboardButton("151-180 м²", callback_data="area_151_180")],
        [InlineKeyboardButton("181-210 м²", callback_data="area_181_210")],
        [InlineKeyboardButton("Более 210 м²", callback_data="area_more")]
    ]
    await query.edit_message_text(f"✅ Тариф: {tariff_name}\n\nТеперь выберите площадь помещения:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_AREA

async def area_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    area_key = query.data.split("_")[1]
    
    if area_key == "more":
        await query.edit_message_text("Введите точную площадь в м² (число больше 210):")
        return SELECTING_AREA
    
    ranges = ["0_30", "31_60", "61_90", "91_120", "121_150", "151_180", "181_210"]
    idx = ranges.index(area_key)
    
    tariff = user_data[user_id]["tariff"]
    base_price = TARIFF_PRICES[tariff][idx]
    user_data[user_id]["base_price"] = base_price
    user_data[user_id]["area"] = area_key.replace("_", "-")
    user_data[user_id]["area_value"] = int(area_key.split("_")[1])
    
    await show_main_menu(query, user_id)
    return ADDING_SERVICE

async def area_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        area = float(update.message.text)
        if area <= 210:
            await update.message.reply_text("Пожалуйста, введите число больше 210, или используйте кнопки.")
            return SELECTING_AREA
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (площадь в м²):")
        return SELECTING_AREA
    
    tariff = user_data[user_id]["tariff"]
    base_price_210 = TARIFF_PRICES[tariff][6]
    extra = area - 210
    base_price = base_price_210 + (extra * 80)
    
    user_data[user_id]["base_price"] = base_price
    user_data[user_id]["area"] = f">{210}"
    user_data[user_id]["area_value"] = area
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить услугу", callback_data="add_service")],
        [InlineKeyboardButton("💰 Показать итог", callback_data="show_total")],
        [InlineKeyboardButton("❌ Начать заново", callback_data="restart")]
    ]
    await update.message.reply_text(f"✅ Площадь: {area} м²\n💰 Стоимость уборки: {base_price} ₽\n\nЧто дальше?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADDING_SERVICE

async def show_main_menu(query, user_id):
    data = user_data[user_id]
    keyboard = [
        [InlineKeyboardButton("➕ Добавить услугу", callback_data="add_service")],
        [InlineKeyboardButton("💰 Показать итог", callback_data="show_total")],
        [InlineKeyboardButton("❌ Начать заново", callback_data="restart")]
    ]
    await query.edit_message_text(
        f"✅ Тариф: {data['tariff']}\n✅ Площадь: {data['area']} м²\n💰 Базовая стоимость: {data['base_price']} ₽\n\n📋 Добавлено услуг: {len(data['services'])}\n\nЧто делаем дальше?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Показываем услуги по частям (первые 30)
    services = list(EXTRA_SERVICES.keys())
    keyboard = []
    for i in range(min(30, len(services))):
        keyboard.append([InlineKeyboardButton(services[i], callback_data=f"serv_{i}")])
    
    keyboard.append([InlineKeyboardButton("📋 Следующие услуги →", callback_data="more_services")])
    keyboard.append([InlineKeyboardButton("◀️ Назад в главное меню", callback_data="back_main")])
    
    await query.edit_message_text("Выберите дополнительную услугу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def more_services_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    services = list(EXTRA_SERVICES.keys())
    keyboard = []
    for i in range(30, min(60, len(services))):
        keyboard.append([InlineKeyboardButton(services[i], callback_data=f"serv_{i}")])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад к услугам", callback_data="add_service")])
    
    await query.edit_message_text("Дополнительные услуги (продолжение):", reply_markup=InlineKeyboardMarkup(keyboard))

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    service_idx = int(query.data.split("_")[1])
    service_name = list(EXTRA_SERVICES.keys())[service_idx]
    service = EXTRA_SERVICES[service_name]
    
    context.user_data["pending_service"] = service_name
    
    if service["need_qty"]:
        await query.edit_message_text(f"Введите количество (в {service['unit']}) для услуги:\n\n{service_name}\n💰 Цена за единицу: {service['price']} ₽")
        return AWAITING_QUANTITY
    else:
        user_data[user_id]["services"].append({"name": service_name, "price": service["price"], "qty": 1, "unit": service["unit"]})
        await query.edit_message_text(f"✅ {service_name} добавлена! +{service['price']} ₽")
        await show_main_menu(query, user_id)
        return ADDING_SERVICE

async def quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        qty = float(update.message.text)
        if qty <= 0:
            await update.message.reply_text("Введите положительное число:")
            return AWAITING_QUANTITY
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число:")
        return AWAITING_QUANTITY
    
    service_name = context.user_data.get("pending_service")
    service = EXTRA_SERVICES[service_name]
    total_price = service["price"] * qty
    
    user_data[user_id]["services"].append({"name": service_name, "price": total_price, "qty": qty, "unit": service["unit"], "unit_price": service["price"]})
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить ещё услугу", callback_data="add_service")],
        [InlineKeyboardButton("💰 Показать итог", callback_data="show_total")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
    ]
    await update.message.reply_text(f"✅ {service_name}: {qty} {service['unit']} × {service['price']} ₽ = {total_price} ₽\n\nЧто дальше?", reply_markup=InlineKeyboardMarkup(keyboard))
    
    context.user_data["pending_service"] = None
    return ADDING_SERVICE

async def show_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = user_data.get(user_id)
    if not data or not data.get("tariff"):
        await query.edit_message_text("❌ Ошибка: начните заново командой /start")
        return ConversationHandler.END
    
    total = data["base_price"]
    text = f"🧹 *Калькуляция уборки* 🧹\n\n"
    text += f"📌 *Тариф:* {data['tariff']}\n"
    text += f"📐 *Площадь:* {data['area']} м²\n"
    text += f"💰 *Базовая стоимость:* {data['base_price']} ₽\n\n"
    
    if data["services"]:
        text += "➕ *Дополнительные услуги:*\n"
        for s in data["services"]:
            if s["qty"] > 1:
                text += f"  • {s['name']}: {s['qty']} {s['unit']} × {s['unit_price']} ₽ = {s['price']} ₽\n"
            else:
                text += f"  • {s['name']}: {s['price']} ₽\n"
            total += s["price"]
    else:
        text += "➕ *Дополнительные услуги:* нет\n"
    
    text += f"\n💵 *ИТОГО:* {total} ₽\n\n"
    text += f"📞 Для оформления заказа свяжитесь с менеджером: {MANAGER_USERNAME}"
    
    keyboard = [[InlineKeyboardButton("📞 Связаться с менеджером", url=f"https://t.me/{MANAGER_USERNAME[1:]}")]]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await query.edit_message_text("🔄 Начинаем заново! Напишите /start")
    return ConversationHandler.END

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await show_main_menu(query, user_id)
    return ADDING_SERVICE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена. Используйте /start для начала.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_TARIFF: [CallbackQueryHandler(tariff_selected, pattern="^tariff_")],
            SELECTING_AREA: [
                CallbackQueryHandler(area_selected, pattern="^area_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, area_input)
            ],
            ADDING_SERVICE: [
                CallbackQueryHandler(add_service_menu, pattern="^add_service$"),
                CallbackQueryHandler(more_services_menu, pattern="^more_services$"),
                CallbackQueryHandler(service_selected, pattern="^serv_"),
                CallbackQueryHandler(show_total, pattern="^show_total$"),
                CallbackQueryHandler(restart, pattern="^restart$"),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
            AWAITING_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_input),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    
    print("✅ Бот @CWL_cost1_bot успешно запущен!")
    print("📞 Менеджер: @cleanwithlove")
    print("Напишите /start в Telegram")
    
    app.run_polling()

if __name__ == "__main__":
    main()