import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import talib as ta
import datetime as dt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    CallbackContext,
    MessageHandler,
    filters,
)
import logging
TELEGRAM_TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        
    )
    await update.message.reply_text(welcome_msg)

def calcula_indicador():
    symbol = "BTC-USD"
    mensagem = ""
    try:
        historico = yf.download(symbol, period="2y", interval="1d", auto_adjust=True)
        print(historico.columns)

    except Exception as e:
        print(f"Erro ao baixar dados: {e}")
        exit()

    if historico.empty:
        print("Nenhum dado foi retornado. Verifique o símbolo ou a conexão.")
        exit()

    historico_2d = historico.resample('2D').agg({
        ("Open", "BTC-USD"): "first",
        ("High", "BTC-USD"): "max",
        ("Low", "BTC-USD"): "min",
        ("Close", "BTC-USD"): "last",
        ("Volume", "BTC-USD"): "sum",
    }).dropna()


    historico_2d['SMA_200'] = ta.SMA(historico_2d['Close', 'BTC-USD'], timeperiod=200)  # Corrigido para SMA


    historico_2d['RSI'] = ta.RSI(historico_2d['Close', 'BTC-USD'], timeperiod=14)
    fastk, fastd = ta.STOCHRSI(historico_2d['Close', 'BTC-USD'], timeperiod=14, fastk_period=3, fastd_period=3, fastd_matype=0)
    historico_2d['StochRSI_K'] = fastk
    historico_2d['StochRSI_D'] = fastd


    preco_atual = historico_2d['Close'].iloc[-1]


    preco_atual = historico_2d['Close'].iloc[-1].item()
    rsi_atual = historico_2d['RSI'].iloc[-1].item()
    sma_200_atual = historico_2d['SMA_200'].iloc[-1].item()
    stoch_k_atual = historico_2d['StochRSI_K'].iloc[-1].item()
    stoch_d_atual = historico_2d['StochRSI_D'].iloc[-1].item()


    if pd.isna([rsi_atual, sma_200_atual, stoch_k_atual, stoch_d_atual]).any():
        print("Alguns indicadores contêm valores NaN. Aguarde mais dados.")
    else:

        if (rsi_atual < 40.21 and preco_atual < sma_200_atual and stoch_k_atual < 26.21 and stoch_d_atual < 26.21):
            mensagem += f"Compra! RSI: {rsi_atual:.2f}, Preço: {preco_atual:.2f}, SMA_200: {sma_200_atual:.2f}, "f"StochRSI_K: {stoch_k_atual:.2f}, StochRSI_D: {stoch_d_atual:.2f}"
        else:
            mensagem += f"Espere mais um pouco. RSI: {rsi_atual:.2f}, Preço: {preco_atual:.2f}, SMA_200: {sma_200_atual:.2f}, "f"StochRSI_K: {stoch_k_atual:.2f}, StochRSI_D: {stoch_d_atual:.2f}"
    return mensagem
async def send_analysis_btc(context: CallbackContext):
    
    try:
        mensagem = calcula_indicador()
        await context.bot.send_message(chat_id=CHAT_ID, text=mensagem)
    except Exception as e:
        error_msg = f"❌ Error generating BTC analysis: {str(e)}"
        await context.bot.send_message(chat_id=CHAT_ID, text=error_msg)
    
def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Error: TELEGRAM_TOKEN and CHAT_ID must be set in .env file")
        return None

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    job_queue = app.job_queue
    if job_queue is not None:
        time = dt.time(20, 0, 0)
        job_queue.run_monthly(send_analysis_btc, time=time, day=1) 
    else:
        print("⚠️ JobQueue not available. Install: pip install 'python-telegram-bot[job-queue]'")
