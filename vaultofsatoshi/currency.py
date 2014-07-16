# -*- coding: utf-8 -*-


class Currency(object):
    def __init__(self,code,name, precision, value=0,virtual= True,tradeable=True):
        self.precision = int(precision)
        self.value = value        
        self.virtual = virtual
        self.tradeable = tradeable
        self.code = code
        self.name = name
    def to_data(self, name):
        return {"%s[precision]" % name: self.precision,
                "%s[value]" % name: self.value,
                "%s[value_int]" % name: self.value_int}
    @property
    def value_int(self):
        return self.value*10**self.precision
    
    

def build_currency_from_dict(d):
    code = d.get('code','')
    name = d.get('name','')
    precision = d['precision']
    tradeable = bool(d.get('tradeable',True))
    virtual = bool(d.get('virtual',True))
    value = d.get('value',0)
    return Currency(code,name,precision,value,virtual,tradeable)



class Currencies(dict):
    def __init__(self,*args, **kw):
        super(Currencies,self).__init__(*args, **kw)        
    
    def __setitem__(self, key, value):
         # TODO: what should happen to the order if
        #       the key is already in the dict  
        if not isinstance(value,Currency)and isinstance(value,dict):          
       
           value = build_currency_from_dict(value)
        else:
           raise Exception('is not currency object or dict')
        
        super(Currencies,self).__setitem__(key, value)     
    
    
    def generate_orderbook_combinations(self):
        combos = []
        for k in self.itervalues():
                   
            for v in self.itervalues():
                if k is not v and not v.virtual:
                    combos.append((k,v))          
        
        return combos


def build_currencies_from_list(currency_list):
    currencies = Currencies()
    for curr in currency_list:
        currencies[curr['code']] = curr
    return currencies

