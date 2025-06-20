
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import requests
from datetime import datetime, timedelta
import json
from telegram import BotCommand
import logging
import os

TELEGRAM_TOKEN = "7735977476:AAHm8aP7zBdwaLmiEtOk6iGefE5gnLOpo00"
WEATHER_API_KEY = "85dedf97d07b5ba59da16b7033a9d1f0"
CHOOSING_TIME, CONFIRMING = range(2)
ADMIN_ID = 1227953014

holidays = [
    {
        "name": "Международный женский день",
        "date": datetime(2025, 5, 1),
        "event": "Празднование на городской площади",
        "tickets_available": True
    },
    {
        "name": "День труда",
        "date": datetime(2025, 5, 1),
        "event": "Фестиваль с музыкой и едой",
        "tickets_available": False
    },
    {
        "name": "Сурхарбан",
        "date": datetime(2025, 6, 5),
        "event": "Бурятский спортивный народный праздник",
        "tickets_available": False
    },
    # Добавь другие праздники по необходимости
]

appointments = {}
available_times = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]

from telegram import ReplyKeyboardMarkup

async def confirm_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text.lower()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Без имени"

    if user_response == 'да':
        chosen_time = context.user_data['chosen_time']
        appointments[chosen_time] = user_id
        await update.message.reply_text(f"Вы успешно записаны на {chosen_time}!")

        # Сообщение для администратора
        admin_message = (
            f"Новая запись на приём:\n"
            f"Пользователь: @{username} (ID: {user_id})\n"
            f"Время: {chosen_time}\n"
            f"Дата: Сегодня"  # Можно добавить конкретную дату, если вы расширите логику
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

        # Логирование (если logging импортирован)
        logging.info(f"Запись на приём: Пользователь {user_id} записан на {chosen_time}")
        
        # Возврат в главное меню
        await start(update, context)
    else:
        await update.message.reply_text("Запись отменена.")
        await start(update, context)  # Возврат в главное меню при отмене
    
    context.user_data.clear()  # Очистка данных
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  
    
    if user_id == ADMIN_ID:  # Меню для администратора
        keyboard = [
            ["📩 Отправить сообщение"],
            ["📋 Посмотреть записи"],
            ["ℹ️ Справка", "📞 Контакты"],
            ["📅 График работы", "🌦 Погода"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Добро пожаловать, администратор! Выберите действие:",
            reply_markup=reply_markup
        )
    else:  # Меню для обычных пользователей
        keyboard = [
            ["ℹ️ Справка", "📞 Контакты"],
            ["📅 График работы", "📌 Записаться на приём"],
            ["🌦 Погода", "📜 Мои записи"],
            ["🎉 Праздники"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Добро пожаловать в бот администрации! Выберите команду:",
            reply_markup=reply_markup
        )

async def view_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return

    if not appointments:
        await update.message.reply_text("На сегодня нет записей.")
    else:
        message = "Текущие записи на приём:\n"
        for time, uid in appointments.items():
            message += f"{time}: Пользователь с ID {uid}\n"
        await update.message.reply_text(message)
    
    # Возврат в меню администратора
    await start(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Справочная информация:\n"
        "/contact - Контактная информация\n"
        "/schedule - График работы\n"
        "/appointment - Записаться на приём\n"
        "/weather - Погода в Аргаде\n"
        "/my_appointments - Мои записи\n"
        "/events - Посмотреть предстоящие праздники и события\n"
        "Также вы можете отправить свой вопрос текстом"
    )

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Контактная информация администрации:\n"
        "Адрес: ул. Хышиктуева, 14, улус Аргада\n"
        "Телефон: +7(30149)-4-11-88\n"
        "Email: admargada@yandex.ru"
    )

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "График работы администрации:\n"
        "Пн-Пт: 9:00 - 17:00\n"
        "Обед: 13:00 - 14:00\n"
        "Сб-Вс: Выходной"
    )

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not WEATHER_API_KEY:
        await update.message.reply_text("Ошибка: API-ключ не задан.")
        return

    url = f"http://api.openweathermap.org/data/2.5/weather?q=Kurumkan&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        temp = round(data['main']['temp'])
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = round(data['wind']['speed'])

        weather_message = (
            f"🌍 Погода в Аргаде:\n"
            f"🌡 Температура: {temp}°C\n"
            f"🌤 {description.capitalize()}\n"
            f"💧 Влажность: {humidity}%\n"
            f"💨 Скорость ветра: {wind_speed} м/с"
        )
        await update.message.reply_text(weather_message)
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Ошибка при получении данных о погоде: {str(e)}")

async def start_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    # Фильтруем только свободные временные слоты
    available = [time for time in available_times if time not in appointments]
    
    if not available:
        await update.message.reply_text("Извините, на сегодня нет свободных мест для записи.")
        await start(update, context)  # Возвращаем в главное меню
        return ConversationHandler.END
    
    reply_keyboard = [[time] for time in available]
    await update.message.reply_text(
        "Выберите удобное время для записи:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSING_TIME

async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_time = update.message.text
    if chosen_time not in available_times or chosen_time in appointments:
        await update.message.reply_text("Извините, это время уже занято или недоступно. Пожалуйста, выберите другое время.")
        # Повторно показываем только свободные слоты
        available = [time for time in available_times if time not in appointments]
        if not available:
            await update.message.reply_text("Все слоты заняты. Попробуйте позже.")
            await start(update, context)
            return ConversationHandler.END
        reply_keyboard = [[time] for time in available]
        await update.message.reply_text(
            "Выберите удобное время для записи:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return CHOOSING_TIME
    
    context.user_data['chosen_time'] = chosen_time
    await update.message.reply_text(
        f"Вы хотите записаться на {chosen_time}?\n"
        "Отправьте 'да' для подтверждения или 'нет' для отмены.",
        reply_markup=ReplyKeyboardRemove()
    )
    return CONFIRMING


async def my_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_appointments = [time for time, uid in appointments.items() if uid == user_id]
    
    if user_appointments:
        message = "Ваши записи на сегодня:\n"
        for i, time in enumerate(user_appointments, 1):
            message += f"{i}. {time}\n"
        message += "\nВведите номер записи, которую хотите отменить, или '0' для возврата в меню."
        await update.message.reply_text(message)
        return CANCEL_APPOINTMENT  # Запускаем состояние отмены
    else:
        await update.message.reply_text("У вас нет активных записей.")
        await start(update, context)  # Возврат в главное меню
        return ConversationHandler.END

async def cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_appointments = [time for time, uid in appointments.items() if uid == user_id]
    
    try:
        choice = int(update.message.text)
        if choice == 0:  # Возврат в меню
            await update.message.reply_text("Отмена не выполнена.")
            await start(update, context)
            return ConversationHandler.END
        elif 1 <= choice <= len(user_appointments):
            time_to_cancel = user_appointments[choice - 1]
            del appointments[time_to_cancel]  # Удаляем запись
            await update.message.reply_text(f"Запись на {time_to_cancel} успешно отменена.")
            
            # Уведомление администратору об отмене
            username = update.message.from_user.username or "Без имени"
            admin_message = (
                f"Отмена записи:\n"
                f"Пользователь: @{username} (ID: {user_id})\n"
                f"Время: {time_to_cancel}"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
            
            # Логирование (если logging импортирован)
            logging.info(f"Пользователь {user_id} отменил запись на {time_to_cancel}")
            
            await start(update, context)  # Возврат в главное меню
            return ConversationHandler.END
        else:
            await update.message.reply_text("Неверный номер. Введите правильный номер записи или '0' для отмены.")
            return CANCEL_APPOINTMENT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (номер записи или '0').")
        return CANCEL_APPOINTMENT

CHOOSING_TIME, CONFIRMING = range(2)

# Состояния для работы с праздниками
CHOOSE_EVENT, CONFIRM_PURCHASE, ENTER_TICKETS = range(3, 6)

# Состояние для отмены записи
CANCEL_APPOINTMENT = 6

# Константа для максимального количества билетов
MAX_TICKETS = 10

async def start_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"start_events: Текущее состояние {context.user_data.get('state', 'неизвестно')}")
    today = datetime.now()
    upcoming = [h for h in holidays if today < h["date"] < today + timedelta(days=30)]
    if not upcoming:
        await update.message.reply_text("В ближайшие 30 дней нет предстоящих событий.")
        await start(update, context)  # Возврат в главное меню
        return ConversationHandler.END
    else:
        context.user_data["upcoming_events"] = upcoming
        message = "Предстоящие события:\n"
        for i, event in enumerate(upcoming, 1):
            tickets = "Билеты доступны." if event["tickets_available"] else "Билеты не требуются."
            message += f"{i}. {event['name']} ({event['date'].strftime('%Y-%m-%d')}): {event['event']}. {tickets}\n"
        message += "\nПожалуйста, выберите номер события, которое вас интересует."
        await update.message.reply_text(message)
        return CHOOSE_EVENT

async def choose_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"choose_event: Текущее состояние {context.user_data.get('state', 'неизвестно')}")
    try:
        choice = int(update.message.text) - 1
        upcoming = context.user_data["upcoming_events"]
        if 0 <= choice < len(upcoming):
            event = upcoming[choice]
            context.user_data["chosen_event"] = event
            if event["tickets_available"]:
                await update.message.reply_text(
                    f"Вы выбрали {event['name']}.\n"
                    f"Хотите купить билеты? (да/нет)"
                )
                return CONFIRM_PURCHASE
            else:
                await update.message.reply_text(
                    f"Подробности о {event['name']}: {event['event']}.\n"
                    "Билеты для этого события не требуются."
                )
                await start(update, context)  # Возврат в главное меню
                return ConversationHandler.END
        else:
            await update.message.reply_text("Неверный выбор. Пожалуйста, выберите правильный номер.")
            return CHOOSE_EVENT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите номер события.")
        return CHOOSE_EVENT

async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"confirm_purchase: Текущее состояние {context.user_data.get('state', 'неизвестно')}")
    response = update.message.text.lower()
    if response == "да":
        event = context.user_data["chosen_event"]
        await update.message.reply_text(
            f"Сколько билетов вы хотите купить на {event['name']}? (Максимум {MAX_TICKETS})"
        )
        return ENTER_TICKETS
    elif response == "нет":
        event = context.user_data["chosen_event"]
        await update.message.reply_text(
            f"Подробности о {event['name']}: {event['event']}.\n"
            "Если передумаете, начните заново с /events."
        )
        await start(update, context)  # Возврат в главное меню
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, ответьте 'да' или 'нет'.")
        return CONFIRM_PURCHASE

async def enter_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"enter_tickets: Получен текст '{update.message.text}' от {update.effective_user.id}")
    try:
        num_tickets = int(update.message.text)
        if num_tickets <= 0:
            await update.message.reply_text("Пожалуйста, введите положительное число.")
            return ENTER_TICKETS
        elif num_tickets > MAX_TICKETS:
            await update.message.reply_text(
                f"Максимальное количество билетов: {MAX_TICKETS}. Пожалуйста, выберите меньшее число."
            )
            return ENTER_TICKETS
        else:
            event = context.user_data["chosen_event"]
            user_id = update.effective_user.id
            username = update.effective_user.username or "Без имени"

            # Сообщение для пользователя
            await update.message.reply_text(
                f"Спасибо! Ваш запрос на {num_tickets} билетов на {event['name']} ({event['date'].strftime('%Y-%m-%d')}) получен.\n"
                "Администрация свяжется с вами для подтверждения и оплаты."
            )

            # Сообщение для администратора
            admin_message = (
                f"Новый запрос на билеты:\n"
                f"Пользователь: @{username} (ID: {user_id})\n"
                f"Событие: {event['name']}\n"
                f"Дата: {event['date'].strftime('%Y-%m-%d')}\n"
                f"Количество билетов: {num_tickets}"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

            # Логирование
            logging.info(f"Запрос на билеты: Пользователь {user_id} хочет {num_tickets} билетов на {event['name']}")

            # Очистка данных и возврат в главное меню
            context.user_data.clear()
            await start(update, context)
            print(f"Диалог завершается с ConversationHandler.END ({ConversationHandler.END})")
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число билетов.")
        return ENTER_TICKETS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено. Вы вернулись в главное меню.")
    return ConversationHandler.END

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Используйте формат: /send <user_id> <сообщение>\n"
            "Пример: /send 123456789 Привет, ваш запрос обработан!"
        )
        return

    try:
        target_user_id = int(context.args[0])
        message_text = " ".join(context.args[1:])

        # Отправка сообщения пользователю
        await context.bot.send_message(chat_id=target_user_id, text=message_text)
        await update.message.reply_text(f"Сообщение отправлено пользователю с ID {target_user_id}.")
    except ValueError:
        await update.message.reply_text("Пожалуйста, укажите корректный user_id (число).")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"handle_message: Получен текст '{update.message.text}' от {update.effective_user.id}")
    await update.message.reply_text(
        "Спасибо за ваше сообщение. Мы обработаем его в ближайшее время.\n"
        "Для получения справочной информации используйте команду /help"
    )

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # 🎉 ConversationHandler для праздников
    conv_handler_events = ConversationHandler(
        entry_points=[CommandHandler("events", start_events),
                      MessageHandler(filters.Regex(r"🎉 Праздники"), start_events)],
        states={
            CHOOSE_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_event)],
            CONFIRM_PURCHASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_purchase)],
            ENTER_TICKETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_tickets)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    application.add_handler(conv_handler_events)

    # 🎯 ConversationHandler для записи на приём
    conv_handler_appointment = ConversationHandler(
        entry_points=[CommandHandler("appointment", start_appointment),
                      MessageHandler(filters.Regex(r"📌 Записаться на приём"), start_appointment)],
        states={
            CHOOSING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_time)],
            CONFIRMING: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_appointment)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    application.add_handler(conv_handler_appointment)

    # 🎯 ConversationHandler для отмены записи
    conv_handler_cancel = ConversationHandler(
        entry_points=[CommandHandler("my_appointments", my_appointments),
                      MessageHandler(filters.Regex(r"📜 Мои записи"), my_appointments)],
        states={
            CANCEL_APPOINTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_appointment)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )
    application.add_handler(conv_handler_cancel)

    # Обработчики кнопок
    application.add_handler(MessageHandler(filters.Regex(r"ℹ️ Справка"), help_command))
    application.add_handler(MessageHandler(filters.Regex(r"📞 Контакты"), contact))
    application.add_handler(MessageHandler(filters.Regex(r"📅 График работы"), schedule))
    application.add_handler(MessageHandler(filters.Regex(r"📌 Записаться на приём"), start_appointment))
    application.add_handler(MessageHandler(filters.Regex(r"🌦 Погода"), weather))
    application.add_handler(MessageHandler(filters.Regex(r"🎉 Праздники"), start_events))
    # Кнопки администратора
    application.add_handler(MessageHandler(filters.Regex(r"📩 Отправить сообщение"), send_message))
    application.add_handler(MessageHandler(filters.Regex(r"📋 Посмотреть записи"), view_appointments))

    # Стандартные команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contact", contact))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("weather", weather))
    application.add_handler(CommandHandler("events", start_events))
    application.add_handler(CommandHandler("send", send_message))
    application.add_handler(CommandHandler("view_appointments", view_appointments))

    # Общий обработчик сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен ✅")
    application.run_polling()
if __name__ == "__main__":
    main()
