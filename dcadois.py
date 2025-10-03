import datetime as dt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import logging

# Configuração do logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados da conversa
MENU, SET_REMINDER = range(2)

# Token e ID do chat
TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia a conversa e exibe o menu de dias da semana."""
    welcome_msg = (
        "Welcome to DCA Bitcoin. This bot will work as a reminder for you.\n"
        "You will set the day of the week and every week it will remind you to buy BTC."
    )
    
    keyboard = [
        [InlineKeyboardButton("Monday", callback_data="day_1")],
        [InlineKeyboardButton("Tuesday", callback_data="day_2")],
        [InlineKeyboardButton("Wednesday", callback_data="day_3")],
        [InlineKeyboardButton("Thursday", callback_data="day_4")],
        [InlineKeyboardButton("Friday", callback_data="day_5")],
        [InlineKeyboardButton("Saturday", callback_data="day_6")],
        [InlineKeyboardButton("Sunday", callback_data="day_0")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_msg)
    await update.message.reply_text(
        "Please choose a day to set your weekly reminder:", reply_markup=reply_markup
    )
    
    return MENU

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processa a seleção do dia e agenda o lembrete."""
    query = update.callback_query
    await query.answer()

    # Mapeamento de callback_data para nome do dia e número do dia
    day_map = {
        "day_0": ("Sunday", 0),
        "day_1": ("Monday", 1),
        "day_2": ("Tuesday", 2),
        "day_3": ("Wednesday", 3),
        "day_4": ("Thursday", 4),
        "day_5": ("Friday", 5),
        "day_6": ("Saturday", 6),
    }

    selected_day_name, selected_day_number = day_map.get(query.data)

    if not selected_day_name:
        await query.edit_message_text(text="Unknown option selected.")
        return ConversationHandler.END

    # Salva a preferência do usuário e agenda o lembrete
    chat_id = query.message.chat_id
    
    # Remove job anterior para evitar duplicação
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    # Agenda o novo job semanalmente
    reminder_time = dt.time(20, 0, 0) # Exemplo: 20:00:00
    context.job_queue.run_daily(
        send_reminder, 
        time=reminder_time, 
        days=(selected_day_number),
        chat_id=chat_id,
        name=str(chat_id)
    )

    await query.edit_message_text(f"✅ Your reminder for **{selected_day_name}** at 20:00 has been set!")
    return ConversationHandler.END

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Função de lembrete que envia a mensagem."""
    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text="⏰ It's time to buy some Bitcoin! 🚀"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela a operação."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main() -> None:
    """Função principal para iniciar o bot."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Error: TELEGRAM_TOKEN and CHAT_ID must be set.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(set_reminder, pattern="^day_")],
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.COMMAND, cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()