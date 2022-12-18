from bs4 import BeautifulSoup
import requests
from datetime import datetime
import pandas as pd
import json
from decouple import config

AUTH = config('AUTH_BEARER')
API = config('API_SHEETY')

dict = {'BTC':'bitcoin', 'ETH':'ethereum', 'MATIC':'polygon', 'ADA':'cardano', 'BNB':'bnb', 'DOT':'polkadot-new', 'ALPHA':'alpha-finance-lab', 'MLT':'milc-platform', 'FLOKI':'floki-inu', 'CHZ':'chiliz', 'WOO':'wootrade', 'KDA':'kadena', 'QRDO':'qredo', 'PBX':'paribus', 'UFO':'ufo-gaming', 'USDT':'tether', 'SAND':'the-sandbox', 'CRO':'cronos', 'MTRG':'meter-governance', 'APE':'apecoin-ape', 'METIS':'metisdao', 'OCEAN':'ocean-protocol', 'AZERO':'aleph-zero', 'AURORA':'aurora-near', 'NEAR':'near-protocol', 'PYR':'vulcan-forged-pyr', 'FET':'fetch', 'SFUND':'seedify-fund', 'PRIMAL':'primal-token'}

### Get dollar and today's date
response = requests.get('https://www.google.com/finance/quote/USD-BRL')
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')
object = soup.find(class_='YMlKec fxKbKc')

dollar = float(object.getText())
today = datetime.now().date().strftime('%Y/%m/%d')

pd.set_option('display.float_format', lambda x: '%.2f' %x)

# Get br, us, and crypto prices
with open('assets.json') as f:
    assets = json.load(f)

df = pd.DataFrame.from_dict(assets, orient='index')

df_br = df[df['local'] == 'br'].reset_index()

def status_invest_br(row):
    try:
        res = requests.get(f"https://statusinvest.com.br/acoes/{row['index']}", headers={
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
            "Accept-Language":"en-GB,en-US;q=0.9,en;q=0.8"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        price = float(soup.find(class_="value").getText().replace(",","."))
        return round(price, 2)
    except:
        res = requests.get(f"https://statusinvest.com.br/fundos-imobiliarios/{row['index']}", headers={
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
            "Accept-Language":"en-GB,en-US;q=0.9,en;q=0.8"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        price = float(soup.find(class_="value").getText().replace(",","."))
        return round(price, 2)

def status_invest_dividendos(row):
    try:
        response = requests.get(f"https://statusinvest.com.br/acoes/{row['index']}", headers={
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
            "Accept-Language":"en-GB,en-US;q=0.9,en;q=0.8"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        object = soup.select("#main-2 > div:nth-child(4) > div > div.pb-3.pb-md-5 > div > div:nth-child(4) > div > div.d-flex.justify-between > div > span.sub-value")

        for result in object:
            dividends = round(float(result.text.split(" ")[1].replace(",",".")),2)
            return dividends
    except:
        response = requests.get(f"https://statusinvest.com.br/fundos-imobiliarios/{row['index']}", headers={
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
            "Accept-Language":"en-GB,en-US;q=0.9,en;q=0.8"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        object = soup.select("#main-2 > div:nth-child(4) > div.top-info.d-flex.flex-wrap.justify-between.mb-3.mb-md-5 > div:nth-child(4) > div > div.d-flex.justify-between > div > span.sub-value")

        for result in object:
            dividends = round(float(result.text.split(" ")[1].replace(",",".")),2)
            return dividends

df_br['price'] = df_br.apply(status_invest_br, axis=1)
df_br['value'] = df_br['quantity'] * df_br['price']

df_br['dividends'] = df_br.apply(status_invest_dividendos, axis=1)
df_br['div_mes'] = (df_br['quantity'] * df_br['dividends'])/12

df_br.iloc[-1] = ['TOTAL', 'br', 'total', 'n', 'total', round(df_br['value'].sum(),0), df_br['dividends'].sum(), round(df_br['div_mes'].sum(),0)]

total_br = df_br['value'].iloc[-1]
total_div_br = df_br['div_mes'].iloc[-1]
div_caixa = (CAIXA_NUBANK * TAXA_SELIC/100)/12

# CRYPTO
df_crypto = df[df['local'] == 'crypto'].reset_index()
df_crypto['name'] = df_crypto['index'].apply(lambda x: dict[x])

def get_crypto_price(row):
    response = requests.get(f"https://coinmarketcap.com/currencies/{row['name']}")
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    object = soup.find(class_='priceValue')
    result = float(object.getText().strip('$').replace(',',""))
    return result

df_crypto['price'] = df_crypto.apply(get_crypto_price, axis=1)
df_crypto['value'] = df_crypto['quantity'] * df_crypto['price']

df_crypto.iloc[-1] = ['TOTAL', 'crypto', 'total', 'y', 'name', 'price', df_crypto['value'].sum()]

total_crypto = round(df_crypto['value'].iloc[-1] * dollar,2)

# US
df_us = df[df['local'] == 'us'].reset_index()

def get_us_price(row):
    response = requests.get(f"https://finance.yahoo.com/quote/{row['index']}?ltr=1", headers={
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
    "Accept-Language":"en-GB,en-US;q=0.9,en;q=0.8"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    object = soup.find(class_="Fw(b) Fz(36px) Mb(-4px) D(ib)")
    data = float(object.getText())
    return data

df_us['price'] = df_us.apply(get_us_price, axis=1)
df_us['value'] = df_us['quantity'] * df_us['price']

df_us.iloc[-1] = ['TOTAL', 'us', 'total', 'y', 'total', df_us['value'].sum()] 

total_us = round(df_us['value'].iloc[-1] * dollar,2)

upload_dict = {
    'datum': {
        'date':today, 'dollar':dollar, 'br':total_br, 'divbr':total_div_br, 'caixa':CAIXA_NUBANK, 'divcaixa':div_caixa,
        'crypto':total_crypto, 'us':total_us, 'invest':DIVIDENDOS_INVEST_MENSAL, 'selic': TAXA_SELIC,
        'xp': FATURA_XP
    }
}

print(upload_dict)

sheet_endpoint = API

headers = {
    'Authorization': AUTH
}

sheet_response = requests.post(url=sheet_endpoint, json=upload_dict, headers=headers)
print(sheet_response.status_code)
print(sheet_response.text)
