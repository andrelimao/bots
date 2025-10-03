from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from httpcore import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import NoSuchElementException
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import os
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from bs4 import BeautifulSoup
import yfinance as yf
import datetime as dt
import pandas as pd
from selenium import webdriver
#from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tvDatafeed import TvDatafeed, Interval
from telegram.ext import Application, CommandHandler, CallbackContext, ContextTypes, Updater
import requests
from dotenv import load_dotenv
import pytz

CHAT_ID = ''
TELEGRAM_TOKEN = ''

url = "https://en.macromicro.me/charts/30335/bitcoin-mvrv-zscore"
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_argument('--disable-blink-features=AutomationControlled')
driver = uc.Chrome()
def calcula_indice(driver):
    message += ""
    driver.get(url)
    mvrv_z = WebDriverWait(driver, 60).until(EC.visibility_of_element_located((By.XPATH, "//div[@class = 'stat-val']//span[@class = 'val']")))
    print(type(mvrv_z))
    mvrv_z_numero = float(mvrv_z.text)
    if mvrv_z_numero <  1:
        message += f"Excellent time to buy even leveraged. Mvrv-z now is {mvrv_z_numero} Mvrv-z is 1 or under 1"
        return message
    else:
        message += f"Wait a little bit more. Mvrv-z is {mvrv_z_numero} Mvrv-z is above 1"
        return message
async def start(update: Updater, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg += "welcome to the bot dca turbo 2.0. this bot will use the mvrv-z indicator to show you if it's a good time to buy some btc. It will help you to take the best decision. every day you will receive a message by this bot, you don't have to do nothing"
    return welcome_msg
async def send_analysis(update, context):
    try:
        mensagem = calcula_indice(driver)
        await context.bot.send_message(chat_id=CHAT_ID, text=mensagem)
    except Exception as e:
        error_msg = f"❌ Error generating BTC analysis: {str(e)}"
        await context.bot.send_message(chat_id=CHAT_ID, text=error_msg)

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Error: TELEGRAM_TOKEN and CHAT_ID must be set in .env file")
        return None

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos
    #app.add_handler(CommandHandler("start", start))
    #app.add_handler(CommandHandler("analysis_btc", analysis_btc)W  )
    #app.add_handler(CommandHandler("analysis_altcoins", analysis_altcoins))

    # Agendamento da análise diária
    job_queue = app.job_queue
    if job_queue is not None:
        # Configurar timezone do Brasil
        #brazil_tz = pytz.timezone('America/Sao_Paulo')
        time = dt.time(20, 0, 0)
        job_queue.run_daily(send_analysis, time)
        
        print("📅 Daily analysis scheduled for 8:00 PM Brazil time (America/Sao_Paulo)")
    else:
        print("⚠️ JobQueue not available. Install: pip install 'python-telegram-bot[job-queue]'")

    print("🤖 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()