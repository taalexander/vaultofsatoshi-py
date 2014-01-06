import time
import hmac
import hashlib
import base64
import urllib2
from BeautifulSoup import BeautifulSoup
import requests
import json
import datetime

base_url = "https://api.vaultofsatoshi.com"
api_key = "TODO"
api_secret = "TODO"

def microsecond_to_timestamp(microseconds):
    milliseconds = microseconds / 1000 / 1000
    dt = datetime.datetime.fromtimestamp(milliseconds)
    return dt.isoformat() + 'Z'

def get_http_data(data):
    if not data:
        data = {}

    # seconds + 6 microsecond accuracy
    nonce = str(int(time.time() * 1000)) + '000'
    data["nonce"] = nonce
    data = "&".join(["%s=%s" % (str(k), str(v)) for k, v in data.items()])
    return data

def request(data, resource_url):
    http_data = get_http_data(data)
    hash_this = resource_url + '\00' + http_data
    sig_base64 = base64.b64encode(hmac.new(api_secret, hash_this, digestmod=hashlib.sha512).hexdigest())
    full_url = base_url + resource_url

    try:
        response = requests.post(full_url, data=http_data, headers={'Api-Key': api_key, 'Api-Sign': sig_base64})
        return json.loads(response.text)
    except requests.exceptions.ConnectionError:
        print "Caught ConnectionError for url: " + full_url
        return None

def get_currency(code=None):
    """
    code: one of 'btc','ltc','ppc'
    """
    params = None
    if code:
        params = {'code': code}
    result = request(params, '/info/currency')
    return result

def get_account():
    return request(None, '/info/account')

def get_balance():
    return request(None, '/info/balance')

def get_wallet_address():
    return request(None, '/info/wallet_address')

def get_wallet_history(currency, count=None, after=None):
    data = {"currency": currency}
    if count:
        data["count"] = count
    if after:
        data["after"] = after
    return request(None, '/info/wallet_history')

def get_ticker(order_currency='BTC', payment_currency='USD'):
    return request({"order_currency": order_currency, "payment_currency": payment_currency}, '/info/ticker')

class Currency(object):
    def __init__(self, precision, value, value_int):
        self.precision = precision
        self.value = value
        self.value_int = value_int

    def to_data(self, name):
        return {"%s[precision]" % name: self.precision,
                "%s[value]" % name: self.value,
                "%s[value_int]" % name: self.value_int}


def get_quote(quote_type, order_units, order_currency, payment_units, payment_currency='USD'):
    """
    quote_type: one of 'bid' or 'ask'
    order_units: object of type Currency
    order_currency: 'BTC', 'LTC'
    payment_units: object of type Currency
    payment_currency: 'USD'
    """
    data = {"type": quote_type,
            "order_currency": order_currency,
            "payment_currency": payment_currency,
            }
    data.update(order_units.to_data("units"))
    data.update(payment_units.to_data("price"))
    return request(data, "/info/quote")

def get_orderbook(order_currency, payment_currency, group_orders, count):
    return request({"order_currency": order_currency, "payment_currency": payment_currency, "group_orders": group_orders, "count": count}, "/info/orderbook")

def get_orders(count, after=None, open_only=False):
    data = {"count": count}
    if after:
        data["after"] = after
    if open_only:
        data["open_only"] = True
    return request(data, "/info/orders")

def get_order_detail(order_id):
    return request({"order_id": order_id}, "/info/order_detail")

def place_trade(trade_type, order_currency, units, payment_currency, price):
    """
    trade_type: one of 'bid' or 'ask'
    order_currency: 'BTC', 'LTC'
    units: Currency object
    payment_currency: 'USD'
    price: Currency object
    """
    data = {"trade_type": trade_type,
            "order_currency": order_currency,
            "payment_currency": payment_currency}
    data.update(units.to_data("units"))
    data.update(price.to_data("price"))
    return request(data, '/trade/place')

def cancel_trade(order_id):
    return request({"order_id": order_id}, "/trade/cancel")

def get_recent_orders():
    page = urllib2.urlopen("https://www.vaultofsatoshi.com/orderbook")
    soup = BeautifulSoup(page)
    closed_btc = soup.find("div", {"id": "closedBitcoinOrders"})
    closed_ltc = soup.findAll("div", {"id": "closedLitecoinOrders"})[0]
    # bug in vault html, peercoin has div 'closedLitecoinOrders'
    closed_ppc = soup.findAll("div", {"id": "closedLitecoinOrders"})[1]

    btc_recent_orders = _get_recent_orders(closed_btc)
    ltc_recent_orders = _get_recent_orders(closed_ltc)
    ppc_recent_orders = _get_recent_orders(closed_ppc)

    return btc_recent_orders, ltc_recent_orders, ppc_recent_orders

def _get_recent_orders(soup):
    results = []
    for r in soup.findAll("tr"):
        tds = r.findAll("td")
        if not len(tds):
            continue

        date = to_iso_datetime(tds[0].text)
        price = float(tds[1].text.partition(' ')[2])
        amount = float(tds[2].text)
        total = float(tds[3].text.partition(' ')[2])
        results.append((date, price, amount, total))
    return results

def to_iso_datetime(date_str):
    """
    converts date string '12/29/13 03:20:17' -> '2013-12-29T03:20:17Z'
    """
    return (datetime.datetime.strptime(date_str, "%m/%d/%y %H:%M:%S")).isoformat() + 'Z'
