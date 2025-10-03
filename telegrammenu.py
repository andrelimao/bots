import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import talib as ta
import datetime as dt
from telegram import LabeledPrice, Update, InlineKeyboardButton, InlineKeyboardMarkup, PreCheckoutQuery
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import logging

TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"
# CHAT_ID = "SEU_CHAT_ID_AQUI"  # Unused, commented out

# Set up logging (optional, but since imported, configure it)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = 'Choose your bot'
    
    keyboard = [
        [InlineKeyboardButton("DCA Turbo", callback_data="bot_1")],  # Removed duplicates, pay, and url
        [InlineKeyboardButton("DCA Reminder", callback_data="bot_2")],
        [InlineKeyboardButton("Analyse Season", callback_data="bot_3")],
        [InlineKeyboardButton("DCA Turbo 2.0", callback_data="bot_4")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Please choose your bot:", reply_markup=reply_markup  # Corrected "choice" to "choose"
    )
    
    await update.message.reply_text(welcome_msg)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "bot_1":
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="Awesome Product",
            description="A truly awesome product you need!",
            payload="custom-invoice-payload",  # A unique string to identify the invoice
            provider_token="YOUR_PROVIDER_TOKEN",  # Get this from BotFather
            currency="USD",
            prices=[LabeledPrice("Product Price", 1000)],  # Price in smallest units (e.g., cents)
            start_parameter="start_param",  # Optional: for deep linking
            need_name=True,  # Request user's name
            need_email=True,  # Request user's email
            is_flexible=False  # Set to True if shipping options are needed
        )
    elif query.data == "bot_2":
        # Placeholder for DCA Reminder logic (e.g., redirect or other action)
        await query.edit_message_text("You selected DCA Reminder. Add functionality here.")
    elif query.data == "bot_3":
        # Placeholder for Analyse Season logic (e.g., redirect or other action)
        await query.edit_message_text("You selected Analyse Season. Add functionality here.")

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles pre-checkout queries for payments."""
    query = update.pre_checkout_query
    # Check the payload (optional security check)
    if query.invoice_payload != "custom-invoice-payload":
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles successful payment messages."""
    await update.message.reply_text("Thank you for your purchase! You now have access to DCA Turbo.")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()