from fplan.extract.parse_tma import parse_all_tma,parse_r_areas
from fplan.extract.parse_obstacles import parse_obstacles
from fplan.extract.extract_airfields import extract_airfields
from fplan.extract.parse_sig_points import parse_sig_points
from fplan.extract.fetchdata import get_filedate
from datetime import datetime,timedelta
import pickle
import os

version=2

from threading import Lock
aipdata=[]
loaded_aipdata_cachefiledate=None
last_timestamp_check=datetime.utcnow()
lock=Lock()
def get_aipdata(cachefile="aipdata.cache"):
    global aipdata
    global loaded_aipdata_cachefiledate
    global last_timestamp_check
    lock.acquire()
    try:
            
        if aipdata and os.path.exists(cachefile) and aipdata.get('version',None)==version:
            if datetime.utcnow()-last_timestamp_check>timedelta(0,15) and os.path.exists(cachefile):
                last_timestamp_check=datetime.utcnow()
                filestamp=get_filedate(cachefile)
                print "Timestamp of loaded aipdata: %s, Timestamp of aipdata on disk: %s"%(loaded_aipdata_cachefiledate,filestamp)
                if filestamp!=loaded_aipdata_cachefiledate:
                    try:
                        print "Loading new aipdata"
                        newaipdata=pickle.load(open(cachefile))
                        if newaipdata.get('version',None)!=version:
                            raise Exception("Bad aipdata version")
                        loaded_aipdata_cachefiledate=get_filedate(cachefile);
                        aipdata=newaipdata
                        return aipdata
                    except Exception,cause:
                        print "Tried to load new aipdata from disk, but failed"
            return aipdata
        try:
            aipdata=pickle.load(open(cachefile))
            if aipdata.get('version',None)!=version:
                raise Exception("Bad aipdata version")
            loaded_aipdata_cachefiledate=get_filedate(cachefile);
            return aipdata
        except:
            airspaces=parse_all_tma()
            airspaces.extend(parse_r_areas())
            
            airfields=extract_airfields()
            for ad in airfields:
                if 'spaces' in ad:
                    for space in ad['spaces']:
                        pa=dict()
                        pa['name']=space['name']
                        pa['floor']=space['floor']
                        pa['ceiling']=space['ceil']
                        pa['points']=space['points']
                        pa['type']='CTR'
                        pa['freqs']=space.get('freqs',"")
                        airspaces.append(pa)
            
            aipdata=dict(
                airspaces=airspaces,
                obstacles=parse_obstacles(),
                airfields=airfields,
                sig_points=parse_sig_points(),
                version=version
                )
            pickle.dump(aipdata,open(cachefile,"w"),-1)        
            loaded_aipdata_cachefiledate=get_filedate(cachefile);
            return aipdata
    finally:
        lock.release()
def get_airspaces():
    aipdata=get_aipdata()
    return aipdata['airspaces']
def get_obstacles():
    aipdata=get_aipdata()
    return aipdata['obstacles']
def get_airfields():
    aipdata=get_aipdata()
    return aipdata['airfields']
def get_sig_points():
    aipdata=get_aipdata()
    return aipdata['sig_points']
if __name__=='__main__':
    get_aipdata("aipdata.cache.new")
    print "wrote aipdata.cache.new"
    
