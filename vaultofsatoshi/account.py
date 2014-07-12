# -*- coding: utf-8 -*-

import time
import hmac
import hashlib
import base64
import urllib2
import requests
import json
import datetime
from concurrent import futures
from BeautifulSoup import BeautifulSoup
from .config import config as config
from .util import to_iso_datetime
from .currency import Currency,build_currencies_from_list
from .orders import *
base_url = config['url']
api_key = config['api_key']
api_secret = config['api_secret']


class Account(object):
    
    def __init__(self,api_key,api_secret,base_url='https://api.vaultofsatoshi.com'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url 


    def microsecond_to_timestamp(self,microseconds):
        milliseconds = microseconds / 1000 / 1000
        dt = datetime.datetime.fromtimestamp(milliseconds)
        return dt.isoformat() + 'Z'

    def _get_http_data(self,data):
        if not data:
            data = {}

        # seconds + 6 microsecond accuracy
        nonce = str(int(time.time() * 1000)) + '000'
        data["nonce"] = nonce
        data = "&".join(["%s=%s" % (str(k), str(v)) for k, v in data.items()])
        return data

    def _request(self,data, resource_url):
        http_data = self._get_http_data(data)
        hash_this = resource_url + '\00' + http_data
        sig_base64 = base64.b64encode(hmac.new(self.api_secret, hash_this, digestmod=hashlib.sha512).hexdigest())
        full_url = self.base_url + resource_url

        try:
            response = requests.post(full_url, data=http_data, headers={'Api-Key': self.api_key, 'Api-Sign': sig_base64})
            return json.loads(response.text)['data']
        except requests.exceptions.ConnectionError:
            print "Caught ConnectionError for url: " + full_url
            return None

    def get_currency(self,code=None):
        """
        code: one of 'btc','ltc','ppc'
        """
        params = None
        if code:
            params = {'code': code}
        result = self._request(params, '/info/currency')
        return build_currencies_from_list(result)

    def get_account(self,):
        return self._request(None, '/info/account')

    def get_balance(self,):
        return self._request(None, '/info/balance')

    def get_wallet_address(self,):
        return self._request(None, '/info/wallet_address')

    def get_wallet_history(self,currency, count=None, after=None):
        data = {"currency": currency}
        if count:
            data["count"] = count
        if after:
            data["after"] = after
        return self._request(None, '/info/wallet_history')

    def get_ticker(self,order_currency='BTC', payment_currency='USD'):
        return self._request({"order_currency": order_currency, "payment_currency": payment_currency}, '/info/ticker')



    def get_quote(self,quote_type, order_units, order_currency, payment_units, payment_currency='USD'):
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
        return self._request(data, "/info/quote")

    def get_orderbook(self,order_currency, payment_currency, group_orders, count):
        return build_orderbook_from_dict(self._request({"order_currency": order_currency, "payment_currency": payment_currency,\
         "group_orders": group_orders, "count": count}, "/info/orderbook"))

    def get_orderbooks(self,currency_pairs,group_orders=True,count=20,thread_pool_max_workers=10):
        fut_orderbooks = {}
        for pair in currency_pairs:
            if pair[0].code not in orderbooks:
                orderbooks[pair[0].code] = {} 
        orderbooks = CurrenciesOrderbooks(fut_orderbooks.keys())
        with futures.ThreadPoolExecutor(thread_pool_max_workers) as ex: 
            for pair in currency_pairs:
                fut_orderbooks[pair[0].code][pair[0].code] = ex.submit(self.get_orderbook,pair[0],pair[1],True,20) 

            for order_code,fd in fut_orderbooks.iteritems():
                for purchase_code,fut in fd.iteritems():
                    if fut.exception():
                        raise fut.exception()
                    else:
                        orderbooks[order_code][purchase_code] = fut.result()
        return orderbooks

    def get_orders(self,count, after=None, open_only=False):
        data = {"count": count}
        if after:
            data["after"] = after
        if open_only:
            data["open_only"] = True
        return self._request(data, "/info/orders")

    def get_order_detail(self,order_id):
        return self._request({"order_id": order_id}, "/info/order_detail")

    def place_trade(self,trade_type, order_currency, units, payment_currency, price):
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
        return self._request(data, '/trade/place')

    def cancel_trade(self,order_id):
        return self._request({"order_id": order_id}, "/trade/cancel")

    def get_recent_orders(self,):
        page = urllib2.urlopen("https://www.vaultofsatoshi.com/orderbook")
        soup = BeautifulSoup(page)
        closed_btc = soup.find("div", {"id": "closedBitcoinOrders"})
        closed_ltc = soup.findAll("div", {"id": "closedLitecoinOrders"})[0]
        # bug in vault html, peercoin has div 'closedLitecoinOrders'
        closed_ppc = soup.findAll("div", {"id": "closedLitecoinOrders"})[1]

        btc_recent_orders = self._get_recent_orders(closed_btc)
        ltc_recent_orders = self._get_recent_orders(closed_ltc)
        ppc_recent_orders = self._get_recent_orders(closed_ppc)

        return btc_recent_orders, ltc_recent_orders, ppc_recent_orders

    def _get_recent_orders(self,soup):
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

 