from xml.etree.ElementTree import fromstring
import re
from md5 import md5
from datetime import datetime
import mapper

class Track():pass
def parse_gpx(gpxcontents,startstr,endstr):
    start=None
    end=None
    try:
        start=datetime.strptime(startstr,"%Y-%m-%d %H:%M:%S")
        end=datetime.strptime(endstr,"%Y-%m-%d %H:%M:%S")
    except Exception,cause:
        print "Problem parsing gpx daterange: ",cause
        end=None
        start=None
        
    print "GPX Range: ",start,end
    xml=fromstring(gpxcontents)
    dynamic_id=md5(gpxcontents).hexdigest()
    out=[]
    lastlat=None
    lastlon=None
    threshold=0.25*1.0/60.0
    minlat=1e30
    minlon=1e30
    maxlat=-1e30
    maxlon=-1e30
    out=Track()
    out.points=[]
    lastpos=None
    lasttime=None
    for track in xml.findall("*//{http://www.topografix.com/GPX/1/1}trkpt"):
        lat=float(track.attrib['lat'].strip())
        lon=float(track.attrib['lon'].strip())
        pos=(lat,lon)
        tim=track.find("{http://www.topografix.com/GPX/1/1}time").text.strip()
        ele=float(track.find("{http://www.topografix.com/GPX/1/1}ele").text.strip())
        Y,M,D,h,m,s=re.match("(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):([\.\d]+)Z",tim.strip()).groups()
        micros=int((1e6)*(float(s)%1.0))
        s=int(float(s))
        dtim=datetime(int(Y),int(M),int(D),int(h),int(m),int(s),int(micros))
        #print "Parsed %s as %s"%(tim,dtim)
        
        if start and end and (dtim<start or dtim>end): continue

        if lastlat!=None and lastlon!=None:            
            d=(lastlat-lat)**2+(lastlon-lon)**2
        else:
            d=2*(threshold**2)
        if d>threshold**2:            
            out.points.append(((lat,lon),ele,dtim))
            lastlon=lon
            lastlat=lat
            if lat<minlat: minlat=lat
            if lon<minlon: minlon=lon
            if lat>maxlat: maxlat=lat
            if lon>maxlon: maxlon=lon
        lastpos=pos
        lasttime=dtim

    out.bb1=(maxlat,minlon)
    out.bb2=(minlat,maxlon)
    out.dynamic_id=dynamic_id
    print "Bbs:",out.bb1,out.bb2
    return out
def get_stats(a,b):
    latlon1,ele1,dtim1=a
    latlon2,ele2,dtim2=b    
    
    elapsed=dtim2-dtim1
    bearing,distance=mapper.bearing_and_distance(latlon1,latlon2)
    distance/=1.852
    elapsed_sec=elapsed.days*86400.0+elapsed.seconds+elapsed.microseconds*1e-6
    if elapsed_sec>0:
        speed=distance/(elapsed_sec/3600.0) #kt
    else:
        speed=0
    return dict(when=dtim1.strftime("%Y-%m-%d %H:%M:%S"),altitude=0.5*(ele1+ele2)/0.3048,speed=speed,heading=bearing)
    
