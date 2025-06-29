import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

# Включаем логирование, чтобы видеть происходящее в консоли
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
# Токен вашего ОСНОВНОГО бота
BOT_TOKEN = "" 

# !!! ВАШИ РЕАЛЬНЫЕ ID ГРУППЫ И ТЕМ, ПОЛУЧЕННЫЕ С ПОМОЩЬЮ @userinfobot !!!
ADMIN_CHAT_ID = "" # ID вашей группы (отрицательное число, как строка)
ORDERS_TOPIC_ID = ""          # ID темы "Заказы" (положительное число)
HISTORY_TOPIC_ID = ""         # ID темы "История заказов" (положительное число, пока не используется для новых заявок)

# Замените на ваши реальные контактные данные:
MANAGER_TELEGRAM_LOGIN = "" # Например: "my_telegram_manager"
MANAGER_EMAIL = ""   # Например: "support@mypractices.ru"
MANAGER_PHONE = "+7 (XXX) XXX-XX-XX"      # Например: "+7 (999) 123-45-67"
# --- КОНФИГУРАЦИЯ ---

# --- СОСТОЯНИЯ ДЛЯ ConversationHandler (не меняются) ---
CHOOSING_PRACTICE_TYPE, GETTING_FIO, GETTING_UNIVERSITY, GETTING_TOPIC, GETTING_DATES, GETTING_CONTACT, CONFIRMING_DATA = range(7)

# --- КЛАВИАТУРЫ (не меняются) ---
# Главное меню (Reply Keyboard)
main_menu_keyboard = [
    ["📄 Оформить заявку"],
    ["ℹ️ О практиках", "📞 Контакты"],
]
MAIN_MENU_MARKUP = ReplyKeyboardMarkup(main_menu_keyboard, one_time_keyboard=False, resize_keyboard=True)

# Выбор типа практики (Inline Keyboard)
practice_type_keyboard = [
    [InlineKeyboardButton("📘 Учебная практика", callback_data="учебная")],
    [InlineKeyboardButton("🏭 Производственная практика", callback_data="производственная")],
]
PRACTICE_TYPE_MARKUP = InlineKeyboardMarkup(practice_type_keyboard)

# Подтверждение заявки (Inline Keyboard)
confirm_application_keyboard = [
    [InlineKeyboardButton("✅ Подтвердить заявку", callback_data="confirm")],
    [InlineKeyboardButton("✏️ Изменить данные", callback_data="edit")], # Для простоты, edit начинает диалог заново
]
CONFIRM_APPLICATION_MARKUP = InlineKeyboardMarkup(confirm_application_keyboard)

# --- ОБРАБОТЧИКИ КОМАНД И СООБЩЕНИЙ ---

async def start(update: Update, context):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Привет, {user.first_name}! Добро пожаловать в твой помощник по оформлению учебных и производственных практик!\n\n"
        "Я здесь, чтобы сделать процесс заказа практики максимально быстрым, удобным и понятнымдля тебя.\n\n"
        "Здесь ты можешь:\n"
        "📄 Оформить заявку на нужный тип практики\n"
        "ℹ️ Узнать подробнее о наших услугах и процессе работы\n"
        "📞 Получить контактную информацию для связи\n\n"
        "Готов начать? Выбери действие в меню ниже: 👇",
        reply_markup=MAIN_MENU_MARKUP
    )

async def show_about(update: Update, context):
    """Обработчик кнопки 'О практиках'"""
    await update.message.reply_html(
        "ℹ️ Информация о наших услугах по практикам\n\n"
        "Мы помогаем студентам с оформлением Учебных и Производственных практик, предоставляя всю необходимую документацию и поддержку.\n\n"
        "Как это работает:\n"
        "1️⃣ Ты оформляешь заявку через этот бот.\n"
        "2️⃣ Мы связываемся с тобой для уточнения деталей и требований (тема, сроки, вуз и т.д.).\n"
        "3️⃣ После согласования всех нюансов, мы приступаем к подготовке документов.\n"
        "4️⃣ Ты получаешь готовый пакет для своей практики!\n\n"
        "Почему выбирают нас:\n"
        "✨ Профессиональный подход и опыт\n"
        "⏱️ Экономия твоего времени и сил\n"
        "🔒 Гарантия качества и конфиденциальности\n"
        "👍 Индивидуальный подход к каждой заявке\n\n"
        "Готов оформить заявку или есть вопросы?"
    )

async def show_contacts(update: Update, context):
    """Обработчик кнопки 'Контакты'"""
    await update.message.reply_html(
        "📞📧 Свяжитесь с нами!\n\n"
        "Если у вас возникли вопросы до или после оформления заявки, вы можете связаться с нами любым удобным способом:\n\n"
        f"👤 Менеджер в Telegram: <a href='tg://resolve?domain={MANAGER_TELEGRAM_LOGIN}'>@{MANAGER_TELEGRAM_LOGIN}</a>\n" 
        f"✉️ Email: <a href='mailto:{MANAGER_EMAIL}'>{MANAGER_EMAIL}</a>\n"
        f"📱 Телефон: {MANAGER_PHONE}\n\n"
        "Будем рады помочь!"
    )

# --- ConversationHandler: Оформление заявки ---

async def start_application(update: Update, context):
    """Начало диалога оформления заявки"""
    await update.message.reply_html(
        "✅ Оформление заявки на практику\n\n"
        "Отлично! Давайте приступим к оформлению вашей заявки. Пожалуйста, отвечайте на вопросы по порядку.\n\n"
        "Первый вопрос:\n"
        "Какой тип практики вам нужен?",
        reply_markup=PRACTICE_TYPE_MARKUP 
    )
    return CHOOSING_PRACTICE_TYPE 

async def choose_practice_type(update: Update, context):
    """Обработчик выбора типа практики"""
    query = update.callback_query
    await query.answer() # Важно ответить на callback_query
    
    context.user_data['practice_type'] = query.data # Сохраняем выбор пользователя

    await query.edit_message_text( # Редактируем предыдущее сообщение
        text=f"Хорошо, тип практики - {query.data.capitalize()}.\n\n"
             f"Теперь, пожалуйста, введите ваше полное ФИО:",
        parse_mode='HTML'
    )
    return GETTING_FIO # Переходим в состояние получения ФИО

async def get_fio(update: Update, context):
    """Обработчик получения ФИО"""
    context.user_data['fio'] = update.message.text # Сохраняем ФИО

    await update.message.reply_html(
        "Принято.\n\n"
        "Пожалуйста, укажите название вашего ВУЗа, факультет и номер группы:\n"
        "(Например: МГУ, Экономический факультет, группа ИС1-227-ОТ)"
    )
    return GETTING_UNIVERSITY 

async def get_university(update: Update, context):
    """Обработчик получения ВУЗа"""
    context.user_data['university'] = update.message.text # Сохраняем данные ВУЗа

    await update.message.reply_html(
        "Спасибо.\n\n"
        "Теперь опишите тему вашей практики и основные требования от ВУЗа (если есть методичка или особые указания, кратко упомяните их):"
    )
    return GETTING_TOPIC 

async def get_topic(update: Update, context):
    """Обработчик получения темы практики"""
    context.user_data['topic'] = update.message.text # Сохраняем тему

    await update.message.reply_html(
        "Понятно.\n\n"
        "Укажите, пожалуйста, желаемые сроки прохождения практики (начало и конец):\n"
        "(Например: с 15.06.2024 по 15.07.2024)"
    )
    return GETTING_DATES 

async def get_dates(update: Update, context):
    """Обработчик получения сроков практики"""
    context.user_data['dates'] = update.message.text # Сохраняем сроки

    await update.message.reply_html(
        "И последний шаг!\n\n"
        "Чтобы мы могли оперативно связаться с вами для уточнения деталей заявки, пожалуйста, укажите удобный способ связи (номер телефона, telegram или email):"
    )
    return GETTING_CONTACT 

async def get_contact(update: Update, context):
    """Обработчик получения контакта"""
    context.user_data['contact'] = update.message.text # Сохраняем контакт

    # Формируем сообщение для подтверждения
    user_data = context.user_data
    summary = (
        "📝 Проверьте введенные данные:\n\n"
        f"Тип практики: {user_data.get('practice_type', 'Не указан').capitalize()}\n"
        f"ФИО: {user_data.get('fio', 'Не указан')}\n"
        f"ВУЗ/Факультет/Группа: {user_data.get('university', 'Не указан')}\n"
        f"Тема/Требования: {user_data.get('topic', 'Не указан')}\n"
        f"Сроки: {user_data.get('dates', 'Не указан')}\n"
        f"Контакт для связи: {user_data.get('contact', 'Не указан')}\n\n"
        "Все верно? 👇"
    )

    await update.message.reply_html(summary, reply_markup=CONFIRM_APPLICATION_MARKUP)
    return CONFIRMING_DATA 

async def confirm_application(update: Update, context):
    """Обработчик подтверждения или изменения заявки"""
    query = update.callback_query
    await query.answer()

    if query.data == 'confirm':
        # Формируем сообщение для администратора
        user_data = context.user_data
        user_info = update.effective_user 
        
        admin_notification = (
            "🔔 НОВАЯ ЗАЯВКА НА ПРАКТИКУ!\n\n"
            f"От кого: <a href='tg://user?id={user_info.id}'>{user_info.full_name}</a> (@{user_info.username})\n"
            f"ID пользователя: {user_info.id}\n\n" # Полезно для идентификации, если у пользователя нет username или он его скрыл
            "Детали заявки:\n"
            f"Тип практики: {user_data.get('practice_type', 'Не указан').capitalize()}\n"
            f"ФИО: {user_data.get('fio', 'Не указан')}\n"
            f"ВУЗ/Факультет/Группа: {user_data.get('university', 'Не указан')}\n"
            f"Тема/Требования: {user_data.get('topic', 'Не указан')}\n"
            f"Сроки: {user_data.get('dates', 'Не указан')}\n"
            f"Контакт для связи: {user_data.get('contact', 'Не указан')}\n\n"
            "---\n"
            "Срочно свяжитесь со студентом для уточнения деталей!"
        )

        # --- ОТПРАВКА УВЕДОМЛЕНИЯ В ТЕМУ "Заказы" ГРУППЫ ---
        try:
            # Отправляем сообщение в конкретную тему (ORDERS_TOPIC_ID) внутри группы (ADMIN_CHAT_ID)
            # Добавляем reply_markup=None, чтобы убрать инлайн-кнопки под сообщением в админ чате
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID, 
                message_thread_id=ORDERS_TOPIC_ID, 
                text=admin_notification, 
                parse_mode='HTML',
                reply_markup=None # Убираем инлайн кнопки под сообщением в админ-чате
            )
            logger.info(f"Заявка от пользователя {user_info.id} успешно отправлена в тему Заказы.")
        except Exception as e:
            logger.error(f"Ошибка при отправке заявки в тему {ORDERS_TOPIC_ID} группы {ADMIN_CHAT_ID}: {e}")
            # Отправляем пользователю сообщение об ошибке отправки
            await query.edit_message_text("К сожалению, произошла ошибка при отправке вашей заявки. Пожалуйста, свяжитесь с нами напрямую, используя раздел \"Контакты\".", parse_mode='HTML')
            context.user_data.clear() # Очищаем данные
            return ConversationHandler.END # Завершаем диалог


        # Отправляем подтверждение пользователю
        await query.edit_message_text(
            "🎉 Ваша заявка успешно отправлена!\n\n"
            "Спасибо! Мы получили вашу заявку на оформление практики. Наш менеджер свяжется с вами в ближайшее время по указанным контактным данным "
            f"({user_data.get('contact', 'Не указан')}) для обсуждения всех деталей и запуска процесса.\n\n"
            "Ожидайте нашего сообщения или звонка.\n\n"
            "Если у вас появятся срочные вопросы, вы можете воспользоваться разделом \"Контакты\".",
            parse_mode='HTML'
        )

        context.user_data.clear() # Очищаем данные пользователя после успешной отправки
        return ConversationHandler.END # Завершаем диалог

    elif query.data == 'edit':
        # Если пользователь хочет изменить данные, начинаем процесс заново
        await query.edit_message_text(
            "Хорошо, давайте попробуем снова. \n\n"
            "✅ Оформление заявки на практику\n\n"
            "Отлично! Давайте приступим к оформлению вашей заявки. Пожалуйста, отвечайте на вопросы по порядку.\n\n"
            "Первый вопрос:\n"
            "Какой тип практики вам нужен?",
            reply_markup=PRACTICE_TYPE_MARKUP,
            parse_mode='HTML'
        )
        context.user_data.clear() # Очищаем старые данные
        return CHOOSING_PRACTICE_TYPE # Возвращаемся в состояние выбора типа

async def cancel(update: Update, context):
    """Отменяет и завершает диалог"""
    user = update.effective_user
    logger.info(f"Пользователь {user.first_name} отменил диалог оформления заявки.")
    await update.message.reply_text(
        "Оформление заявки отменено.",
        reply_markup=MAIN_MENU_MARKUP # Возвращаем главное меню
    )
    context.user_data.clear() # Очищаем данные
    return ConversationHandler.END # Завершаем диалог

async def fallback(update: Update, context):
    """Обработчик для любых других сообщений во время диалога"""
    await update.message.reply_text(
        "Кажется, вы сейчас находитесь в процессе оформления заявки. Пожалуйста, ответьте на текущий вопрос или используйте /cancel для отмены."
    )
    # Остаемся в текущем состоянии, чтобы пользователь мог ввести корректные данные


# --- Главная функция запуска бота ---
def main():
    # Создаем Application с токеном основного бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Создаем ConversationHandler для оформления заявки
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📄 Оформить заявку$") & ~filters.COMMAND, start_application)], # Входная точка - кнопка "Оформить заявку"
        states={
            CHOOSING_PRACTICE_TYPE: [CallbackQueryHandler(choose_practice_type)], 
            GETTING_FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_fio)], 
            GETTING_UNIVERSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_university)], 
            GETTING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_topic)], 
            GETTING_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dates)], 
            GETTING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)], 
            CONFIRMING_DATA: [CallbackQueryHandler(confirm_application)], 
        },
        fallbacks=[
            CommandHandler("cancel", cancel), 
            # Добавляем обработку любых сообщений или команд во время диалога, чтобы не ломать его
            MessageHandler(filters.ALL & ~filters.COMMAND, fallback), # Любое сообщение (кроме команд), не соответствующее состоянию
            CommandHandler("start", fallback) # Не перезапускаем диалог командой start во время оформления
        ]
    )

    application.add_handler(conv_handler)

    # Обработчики для кнопок главного меню, которые не входят в диалог
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ О практиках$") & ~filters.COMMAND, show_about))
    application.add_handler(MessageHandler(filters.Regex("^📞 Контакты$") & ~filters.COMMAND, show_contacts))

    # Обработчик для неизвестных команд или сообщений вне диалога
    application.add_handler(MessageHandler(filters.COMMAND, lambda update, context: update.message.reply_text("Неизвестная команда. Используйте /start для начала.")))
    # Этот обработчик будет ловить все остальное, что не поймали другие (текст вне диалога, фото, стикеры и т.д.)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, lambda update, context: update.message.reply_text("Извините, я не понимаю это. Выберите действие из меню или используйте /start.")))


    # Запускаем бота
    logger.info("Бот запущен!")
    application.run_polling(poll_interval=3, stop_signals=None) # poll_interval - как часто проверять обновления. stop_signals=None позволяет останавливать ctrl+C

# Запускаем главную функцию
if __name__ == '__main__':
    main()