# -*- coding: utf-8 -*-

from .vault import Account 
from .currency import * 
from concurrent import futures
from datetime import datetime

import threading

class VOS_data(object):
    def __init__(self,**kwargs):
        self.balance = kwargs.get('balance',None)
        self.currencies = kwargs.get('currencies',None)
        self.account = kwargs.get('account',None)
        self.orders = kwargs.get('orders',None)
        self.orderbook = kwargs.get('orderbook',None)

class AsyncDataUpdater(Account):

    def __init__(self,queue,api_key,api_secret,base_url='https://api.vaultofsatoshi.com',
                    call_time=0.5,thread_pool_max_workers=5):
        self.q = queue
        self.thread_pool_max_workers = thread_pool_max_workers
        self.orderbook = None
        self.orderbook_time = datetime.now()
        super(AsyncDataUpdater, self).__init__(api_key,api_secret,base_url)


    def start(self):
        self.currencies = build_currencies_from_list(self.get_currency()['data'])
        self.update()


    def update(self):
        start_time = datetime.now()
        with futures.ThreadPoolExecutor(self.thread_pool_max_workers)\
            as ex: 

            submitted = {}

            submitted['balance'] = ex.submit(self.get_balance)
            submitted['account'] = ex.submit(self.get_account)
            submitted['orders'] = ex.submit(self.get_orders,100)
            now = datetime.now()                
            got_orderbook = False
            if self.orderbook is None or \
            (now-self.orderbook_time).total_seconds >= 4.5:                    
                submitted['orderbook'] = self.get_orderbook()
                got_orderbook = True
                self.orderbook_time = datetime.now()

            results = {}
            for k,v in submitted.iteritems():
                if v.exception():
                    raise v.exception()
                else:
                    results[k] = v.result()

            if got_orderbook:
                self.orderbook = results['orderbook']
            else:
                results['orderbook'] = self.orderbook
            results['currencies'] = self.currencies
            data = VOS_data(results)
            self.q.put(data)
            
            end_time = datetime.now()
            elapsed = (end_time-start_time).total_seconds()
            if elapsed> self.call_time:
                threading.Thread(target=self.update).start()
            else:
                threading.Time(self.call_time-elapsed,self.update).start()

                




