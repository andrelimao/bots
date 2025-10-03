import os
from bs4 import BeautifulSoup
import yfinance as yf
import datetime as dt
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tvDatafeed import TvDatafeed, Interval
from telegram.ext import Application, CommandHandler, CallbackContext, ContextTypes, Updater
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Firefox options for headless mode
firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.add_argument("--disable-gpu")
firefox_options.add_argument("--no-sandbox")
firefox_options.add_argument("--disable-dev-shm-usage")

tv = TvDatafeed()
altcoins = tv.get_hist(symbol='TOTAL', exchange='CRYPTOCAP', interval=Interval.in_daily, n_bars=1000)
print(altcoins.columns)
# Initialize variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')


preco_btc = yf.Ticker("BTC-USD")
rn = dt.datetime.now()
info = preco_btc.fast_info
preco_atual = info.last_price
historico = preco_btc.history(period="1y", interval="1d")


def setup_driver():
    return webdriver.Firefox(options=firefox_options)


def calculate_dominance(driver):
    try:
        url = "https://coinmarketcap.com/pt-br/charts/bitcoin-dominance/"
        driver.get(url)
        dominancia_element = WebDriverWait(driver, 50).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='sc-65e7f566-0 libxwS']//div[@class = 'sc-65e7f566-0 iRoUPH']//span[@class = 'sc-65e7f566-0 exabdI base-text']"))
        )

        if dominancia_element:
            dominancia = dominancia_element.text
            dominancia_numero = dominancia.replace("%", "")
            return float(dominancia_numero)
        return None
    except Exception as e:
        print(f"Error calculating dominance: {e}")
        return None


def calculate_moving_average(prices, window):
    return prices.rolling(window=window).mean()


def crossing_moving_average_btc(historico):
    historico["Long_MA"] = calculate_moving_average(historico['Close'], window=200)
    historico["Short_MA"] = calculate_moving_average(historico['Close'], window=50)
    historico_limpo = historico.dropna()
    return historico_limpo["Long_MA"].iloc[-1] > historico_limpo["Short_MA"].iloc[-1]


def calcula_mayer(preco_atual, historico):
    historico["Long_MA"] = calculate_moving_average(historico['Close'], window=200)
    historico_limpo = historico.dropna()
    media_movel_longa = historico_limpo["Long_MA"].iloc[-1]
    return preco_atual / media_movel_longa
def calcula_nvt():
    url = "https://newhedge.io/bitcoin/network-value-to-transaction-ratio"
    r = requests.get(url)

    bs = BeautifulSoup(r.text, "lxml")
    texto_nvt = bs.find("p", class_ = "nvt-selector").text
    if texto_nvt is not None:
        valor_nvt = float(texto_nvt)
    return valor_nvt

def calcula_ishimoku_btc(historico):
    high_9 = historico["High"].rolling(window=9).max()
    low_9 = historico["Low"].rolling(window=9).min()
    historico["Tenkan_sen"] = (high_9 + low_9) / 2

    high_26 = historico["High"].rolling(window=26).max()
    low_26 = historico["Low"].rolling(window=26).min()
    historico["Kijun_sen"] = (high_26 + low_26) / 2

    historico["Senkou_span_A"] = ((historico['Tenkan_sen'] + historico['Kijun_sen']) / 2).shift(26)

    high_52 = historico["High"].rolling(window=52).max()
    low_52 = historico["Low"].rolling(window=52).min()
    historico["Senkou_span_B"] = ((high_52 + low_52) / 2).shift(26)

    historico_limpo = historico.dropna()
    return historico_limpo["Senkou_span_A"].iloc[-1] > historico_limpo["Senkou_span_B"].iloc[-1]
def decisao_btc(driver):
    dominancia = calculate_dominance(driver)
    mayer = calcula_mayer(preco_atual, historico)
    compra_btc = crossing_moving_average_btc(historico)
    ishimoku_compra = calcula_ishimoku_btc(historico)
    valor_nvt = calcula_nvt()

    if dominancia is None:
        return "⚠️ Erro ao obter dados de dominância do Bitcoin"

    mensagem = "🔄 Análise do Bitcoin:\n\n"
    mensagem += f"💰 Preço atual: ${preco_atual:,.2f}\n"
    mensagem += f"📊 Dominância BTC: {dominancia}%\n"
    mensagem += f"📈 Razão de Mayer: {mayer:.2f}\n\n"

    if dominancia > 50 and compra_btc and mayer < 2.4 and ishimoku_compra:
        mensagem += "🟢 BULLISH: Condições favoráveis para compra. Houve o cruzamento das médias móveis e o indicador ishimoku indica compra. O múltiplo Mayer está abaixo de 2.4"
    elif dominancia > 50 or mayer > 1:
        mensagem += "🟡 NEUTRO: Condições moderadamente favoráveis"
    elif dominancia < 50 and mayer > 2.4 and not compra_btc and not ishimoku_compra:
        mensagem += "🔴 BEARISH: Condições desfavoráveis"
    else:
        mensagem += "🟡 NEUTRO: Sinais mistos no mercado"
    if valor_nvt >= 150:
        mensagem = "Sobrecompra. Risco de queda considerável."
    elif valor_nvt <=45:
        mensagem = "Sobrevenda. Risco de alta considerável."

    return mensagem
def calcula_ishimoku_altcoins():
    # Linha de Conversão (Tenkan-sen)
    compra_altcoins = True
    high_9 = altcoins["high"].rolling(window=9).max()
    low_9 = altcoins["low"].rolling(window=9).min()
    altcoins["Tenkan_sen"] = (high_9 + low_9) / 2

    # Linha Base (Kijun-sen)
    high_26 = altcoins["high"].rolling(window=26).max()
    low_26 = altcoins["low"].rolling(window=26).min()
    altcoins["Kijun_sen"] = (high_26 + low_26) / 2

    # Senkou Span A
    altcoins["Senkou_span_A"] = ((altcoins['Tenkan_sen'] + altcoins['Kijun_sen']) / 2).shift(26)

    # Senkou Span B
    high_52 = altcoins["high"].rolling(window=52).max()
    low_52 = altcoins["low"].rolling(window=52).min()
    altcoins["Senkou_span_B"] = ((high_52 + low_52) / 2).shift(26)

    # Chikou Span
    altcoins["Chikou_span"] = altcoins["close"].shift(-26)
    historico_limpo = altcoins.dropna()
    if historico_limpo["Senkou_span_A"].iloc[-1] > historico_limpo["Senkou_span_B"].iloc[-1] and historico_limpo["close"].iloc[-1] < historico_limpo["Shinkou_span"].iloc[-1]:
        compra_altcoins = True
    else:
        compra_altcoins = False
    return compra_altcoins
def crossing_moving_average_altcoins():
    altcoins["Long_MA"] = calculate_moving_average(altcoins['close'], window=200)
    altcoins["Short_MA"] = calculate_moving_average(altcoins['close'], window=50)
    altcoins_limpo = altcoins.dropna()
    return altcoins_limpo["Long_MA"].iloc[-1] > altcoins_limpo["Short_MA"].iloc[-1]

def decisao_altcoins(driver):
    dominancia = calculate_dominance(driver)
    compra_altcoins = crossing_moving_average_altcoins()
    ishimoku_compra = calcula_ishimoku_altcoins()

    if dominancia is None:
        return "⚠️ Erro ao obter dados de dominância das Altcoins"

    mensagem = "🔄 Análise de Altcoins:\n\n"
    mensagem += f"📊 Dominância BTC: {dominancia}%\n\n"

    if dominancia < 50 and compra_altcoins and ishimoku_compra:
        mensagem += "🟢 BULLISH: Condições favoráveis para compra de altcoins"
    elif dominancia < 50:
        mensagem += "🟡 NEUTRO: Condições moderadamente favoráveis para compra de altcoins"
    elif dominancia < 50 and not compra_altcoins and not ishimoku_compra:
        mensagem += "🔴 BEARISH: Condições desfavoráveis. Bearish."
    else:
        mensagem += "🟡 NEUTRO: Sinais mistos no mercado"

    return mensagem

async def send_analysis_btc(context: CallbackContext):
    driver = setup_driver()
    try:
        mensagem = decisao_btc(driver)
        await context.bot.send_message(chat_id=CHAT_ID, text=mensagem)
    except Exception as e:
        error_msg = f"❌ Erro ao gerar análise BTC: {str(e)}"
        await context.bot.send_message(chat_id=CHAT_ID, text=error_msg)
    finally:
        driver.quit()

async def send_analysis_altcoins(context: CallbackContext):
    driver = setup_driver()
    try:
        mensagem = decisao_altcoins(driver)
        await context.bot.send_message(chat_id=CHAT_ID, text=mensagem)
    except Exception as e:
        error_msg = f"❌ Erro ao gerar análise Altcoins: {str(e)}"
        await context.bot.send_message(chat_id=CHAT_ID, text=error_msg)
    finally:
        driver.quit()

async def start(update: Updater, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 Bem-vindo ao Bot de Análise Bitcoin e altcoins!\n\n"
        "🤖 Eu enviarei análises diárias do Bitcoin e altcoins às 20:00.\n"
        "📊 A análise inclui:\n"
        "- Cruzamento de médias móveis\n"
        "- Nuvem de Ishimoku\n"
        "- Dominância do Bitcoin\n"
        "- Razão de Mayer (BTC)\n"
        "- NVT Ratio para apontar topos e fundos.\n"
        "- Através dele se analisa qual a tendência atual de btc e altcoins\n"
        "Use /analysis_btc para receber uma análise imediata do BTC.\n"
        "Use /analysis_altcoins para receber uma análise imediata das altcoins."
    )
    await update.message.reply_text(welcome_msg)

async def analysis_btc(update, context):
    await update.message.reply_text("🔄 Gerando análise BTC...")
    driver = setup_driver()
    try:
        mensagem = decisao_btc(driver)
        await update.message.reply_text(mensagem)
    except Exception as e:
        error_msg = f"❌ Erro ao gerar análise BTC: {str(e)}"
        await update.message.reply_text(error_msg)
    finally:
        driver.quit()

async def analysis_altcoins(update, context):
    await update.message.reply_text("🔄 Gerando análise Altcoins...")
    driver = setup_driver()
    try:
        mensagem = decisao_altcoins(driver)
        await update.message.reply_text(mensagem)
    except Exception as e:
        error_msg = f"❌ Erro ao gerar análise Altcoins: {str(e)}"
        await update.message.reply_text(error_msg)
    finally:
        driver.quit()

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Error: TELEGRAM_TOKEN and CHAT_ID must be set in .env file")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos
    #app.add_handler(CommandHandler("start", start))
    #app.add_handler(CommandHandler("analysis_btc", analysis_btc))
    #app.add_handler(CommandHandler("analysis_altcoins", analysis_altcoins))

    # Agendamento da análise diária
    job_queue = app.job_queue
    time = dt.time(20, 0, 0)
    job_queue.run_daily(send_analysis_btc, time=time, days=(0, 1, 2, 3, 4, 5, 6))
    job_queue.run_daily(send_analysis_altcoins, time=time, days=(0, 1, 2, 3, 4, 5, 6))

    print("🤖 Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
