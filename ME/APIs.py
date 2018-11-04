# -*- coding: utf-8 -*-
"""
Created on Sat Nov  3 17:34:03 2018

@author: theki
"""
from neo_futures import KeepRefs
from time import sleep
import requests
import json

class APIs(KeepRefs):
    def __init__(self,name,url,nOracles):
        super(APIs, self).__init__()
        self.name=name
        self.url=url
        self.nOracles=0
        
    def get_latest_price(self):
        r = requests.get(self.url)
        r_json = r.json()
        last_updated = r_json[0]['last_updated']
        price_usd = r_json[0]['price_usd']
        return last_updated, price_usd


    def update_buffer(self,buffer, max_len=10):

        t, p = self.get_latest_price()
        changed = False

        if buffer is None:
            buffer = [(t,p)]
            changed = True
        else:
            (t_1, p_1) = buffer[-1]
            if t_1 < t:
                buffer.append((t,p))
                changed = True
    
        if len(buffer) > max_len:
            buffer = buffer[-max_len:]
    
        return buffer, changed
    
def list_APIs():
    inst=APIs.get_instances()
    nOracle=[]
    for r in inst:
        nOracle[r]=inst[r].nOracles
    nOraclesperAPI=dict(zip(inst, nOracle))
    return nOraclesperAPI
            
        
def allocate_oracle(client):
    OracleperAPI=list_APIs()
    minAPI=min(OracleperAPI, key=OracleperAPI.get)
    return minAPI.get_latest_price
    
if __name__ == '__main__':
   buffer = None
   while True:
    buffer = update_buffer(buffer)
    print(buffer)
    sleep(60)
            
