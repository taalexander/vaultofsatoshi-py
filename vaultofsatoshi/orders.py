from .currency import Currency,build_currency_from_dict
from datetime import datetime
class Order(object):
    def __init__(self,order_currency,payment_currency,total,is_ask=True,time=None):        
        assert isinstance(order_currency,Currency) and isinstance(payment_currency,Currency)\
        and isinstance(total,Currency)        
        self.order_currency = order_currency
        self.payment_currency = payment_currency
        self.total = total
        self._is_ask = is_ask
        self.time = time if time else datetime.now()

    @property
    def is_ask(self):
        return self._is_ask
    @property
    def is_bid(self):
        return not self._is_ask
     
    
class Orderbook(object):
    
    def __init__(self,asks,bids):
        """
        Accepts list asks,bids which must be lists of Order classes
        """
        self.asks = asks
        self.bids = bids


class CurrenciesOrderbooks(dict):
    def __init__(self, *args, **kw):
        super(CurrenciesOrderbooks,self).__init__(*args, **kw)        
    
    def __setitem__(self, key, value):
         # TODO: what should happen to the order if
        #       the key is already in the dict  
        if not isinstance(value,Orderbook)and isinstance(value,dict):          
       
           value = build_orderbook_from_dict(value)
        else:
           raise Exception('is not currency object or dict')
        
        super(CurrenciesOrderbooks,self).__setitem__(key, value)     


def build_order_from_dict(order_dict,is_ask,timestamp,order_code,payment_code):
    price_dict = order_dict['price']
    quantity_dict = order_dict['quantity']
    total_dict = order_dict['total']
    price_dict['code'] = order_code
    quantity_dict['code'] = payment_code
    total_dict['code'] = payment_code


    price_curr = build_currency_from_dict(price_dict)
    quantity_curr = build_currency_from_dict(quantity_dict)
    total_curr = build_currency_from_dict(total_dict)
    #timestamp in microseconds
    time = datetime.fromtimestamp(timestamp / 1e6)

    return Order(price_curr,quantity_curr,total_curr,is_ask,time)
    
    


def build_orderbook_from_dict(orderbook_dict):
    asks_dict = orderbook_dict['asks']
    bids_dict = orderbook_dict['bids']
    asks = []
    bids = []    
    timestamp = orderbook_dict['timestamp']
    order_code = orderbook_dict['order_currency']
    payment_code = orderbook_dict['payment_currency']
    for ask in asks_dict:
        asks.append(build_order_from_dict(ask,True,timestamp,order_code,payment_code))
    for bid in bids_dict:
        bids.append(build_order_from_dict(bid,False,timestamp,order_code,payment_code))

    return Orderbook(asks,bids)