import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from fplan.model import meta,User,Trip,Waypoint,Route,Aircraft
from fplan.lib.base import BaseController, render
import sqlalchemy as sa
log = logging.getLogger(__name__)
import fplan.lib.mapper as mapper
import routes.util as h
from fplan.extract.extracted_cache import get_airfields
import json
import re
import fplan.lib.weather as weather
from fplan.lib.calc_route_info import get_route



class FlightplanController(BaseController):
    def search(self):
        searchstr=request.params.get('search','')

        latlon_match=re.match(r"(\d+)\.(\d+)([NS])(\d+)\.(\d+)([EW])",searchstr)
        if latlon_match:
            latdeg,latdec,ns,londeg,londec,ew=latlon_match.groups()
            lat=float(latdeg)+float("0."+latdec)
            lon=float(londeg)+float("0."+londec)
            if ns in ['S','s']:
                lat=-lat
            if ew in ['W','w']:
                lon=-lon
            return json.dumps([['Unknown Waypoint',[lat,lon]]])                


        #print "Searching for ",searchstr
        searchstr=searchstr.lower()
        airports=[]
        for airp in get_airfields():
            if airp['name'].lower().count(searchstr) or \
                airp['icao'].lower().count(searchstr):
                airports.append(airp)  
        if len(airports)==0:
            return ""
        airports.sort()
        ret=json.dumps([[x['name'],mapper.from_str(x['pos'])] for x in airports[:15]])
        print "returning json:",ret
        return ret
    def save(self):
        print "Saving tripname:",request.params['tripname']
        trip=meta.Session.query(Trip).filter(sa.and_(Trip.user==session['user'],
            Trip.trip==request.params['tripname'])).one()
        waypoints=meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],
             Waypoint.trip==request.params['tripname'])).order_by(Waypoint.ordinal).all()
        for idx,way in enumerate(waypoints[:-1]):
            print "Found waypoint #%d"%(idx,)    
            route=meta.Session.query(Route).filter(sa.and_(
                Route.user==session['user'],
                Route.trip==request.params['tripname'],
                Route.waypoint1==way.ordinal,
                )).one()
            for col,att in [
                ('W','winddir'),
                ('V','windvel'),
                ('TAS','tas'),
                ('Alt','altitude'),
                ('Var','variation'),
                ('Dev','deviation')
                ]:
                                                
                key="%s_%d"%(col,idx)
                val=request.params[key]
                print "Value of key %s: %s"%(key,val)
                setattr(route,att,val)
        acname=request.params.get('aircraft','').strip()
        if acname!="":
            trip.aircraft=acname
        meta.Session.flush()
        meta.Session.commit()
        return "ok"
    def fetchac(self):
        trip=meta.Session.query(Trip).filter(sa.and_(Trip.user==session['user'],
            Trip.trip==session['current_trip'])).one()
        trip.aircraft=request.params['aircraft']
        
        alts=request.params.get('alts','')
        if alts==None:
            altvec=[]
        else:
            altvec=alts.split(",")
        for idx,alt in enumerate(altvec):
             route=meta.Session.query(Route).filter(sa.and_(
                  Route.user==session['user'],
                  Route.trip==request.params['tripname'],
                  Route.waypoint1==idx,
                  Route.waypoint2==idx+1,
                  )).one()
             route.altitude=alt

        rts=get_route(session['user'],request.params['tripname'])['routes']
        ret=[]
        for rt in rts:
            print "Processing rt:",rt 
            ret.append(rt.tas)
        jsonstr=json.dumps(ret)
        print "returning json:",jsonstr
        return jsonstr
        
    def weather(self):
        waypoints=meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],
             Waypoint.trip==request.params['tripname'])).order_by(Waypoint.ordinal).all()
             
        ret=[]
        alts=request.params.get('alts','')
        if alts==None:
            altvec=[]
        else:
            altvec=alts.split(",")
        for way,altitude in zip(waypoints[:-1],altvec):
             print("Looking for waypoint: %s"%(way.pos,))
             try:
                mapper.parse_elev(altitude)
             except mapper.NotAnAltitude,cause:
                 ret.append(['',''])                 
                 continue #skip this alt
             #N+1 selects....
             route=meta.Session.query(Route).filter(sa.and_(
                  Route.user==session['user'],
                  Route.trip==request.params['tripname'],
                  Route.waypoint1==way.ordinal,
                  )).one()
             way2=meta.Session.query(Waypoint).filter(sa.and_(
                  Waypoint.user==session['user'],
                  Waypoint.trip==request.params['tripname'],
                  Waypoint.ordinal==route.waypoint2,
                  )).one()
             merc1=mapper.latlon2merc(mapper.from_str(way.pos),14)
             merc2=mapper.latlon2merc(mapper.from_str(way2.pos),14)
             center=(0.5*(merc1[0]+merc2[0]),0.5*(merc1[1]+merc2[1]))
             lat,lon=mapper.merc2latlon(center,14)
             print "Fetching weather for %s,%s, %s"%(lat,lon,route.altitude)
             we=weather.get_weather(lat,lon)
             if we==None:
                 ret.append(['',''])                 
             else:
                 wi=we.get_wind(altitude)
                 print "Got winds:",wi
                 ret.append([wi['direction'],wi['knots']])
        jsonstr=json.dumps(ret)
        print "returning json:",jsonstr
        return jsonstr
    def gpx(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        waypoints=meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordinal).all()
        c.waypoints=[]
        c.trip=session['current_trip']
        for wp in waypoints:                    
            lat,lon=mapper.from_str(wp.pos)
            c.waypoints.append(dict(
                lat=lat,
                lon=lon,
                name=wp.waypoint
                ))
        #response.headers['Content-Type'] = 'application/xml'               
        response.content_type = 'application/octet-stream'               
        response.charset="utf8"
        return render('/gpx.mako')

    def ats(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        waypoints=meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordinal).all()
        c.waypoints=[]
        c.trip=session['current_trip']
        for wp in waypoints:
            lat,lon=mapper.from_str(wp.pos)            
            c.waypoints.append(dict(
                name=wp.waypoint,
                pos=mapper.format_lfv_ats(lat,lon)
                ))
        #response.headers['Content-Type'] = 'application/xml'               
        return render('/ats.mako')



    def index(self):
        # Return a rendered template
        #return render('/flightplan.mako')
        # or, return a response
        trip=meta.Session.query(Trip).filter(sa.and_(Trip.user==session['user'],
            Trip.trip==session['current_trip'])).one()
        c.waypoints=list(meta.Session.query(Waypoint).filter(sa.and_(
             Waypoint.user==session['user'],Waypoint.trip==session['current_trip'])).order_by(Waypoint.ordinal).all())
        
        c.totdist=0.0
        for a,b in zip(c.waypoints[:-1],c.waypoints[1:]):     
            bear,dist=mapper.bearing_and_distance(a.pos,b.pos)
            c.totdist+=dist/1.852
            
        def get(what,a,b):
            #print "A:<%s>"%(what,),a.pos,b.pos
            if what in ['TT','D']:
                bear,dist=mapper.bearing_and_distance(a.pos,b.pos)
                #print "Bear,dist:",bear,dist
                if what=='TT':
                    return "%03.0f"%(bear,)
                elif what=='D':
                    return "%.1f"%(dist/1.852,)
            if what in ['W','V','Var','Alt','TAS']:
                routes=list(meta.Session.query(Route).filter(sa.and_(
                    Route.user==session['user'],Route.trip==session['current_trip'],
                    Route.waypoint1==a.ordinal,Route.waypoint2==b.ordinal)).all())
                if len(routes)==1:
                    route=routes[0]
                    if what=='W':
                        return int(route.winddir+0.5)
                    elif what=='V':
                        return int(route.windvel+0.5)
                    elif what=='Var':
                        return route.variation if route.variation!=None else ''
                    elif what=='Alt':
                        print "Altitude is:",repr(route.altitude)
                        return route.altitude                    
                    elif what=='TAS':
                        if not route.tas:
                            return 75                        
                        return route.tas
                return ""            
                
            return ""
        c.get=get
        c.tripname=session['current_trip']
         
        c.cols=[
                dict(width=3,short='W',desc="Wind Direction (deg)",extra=""),
                dict(width=2,short='V',desc="Wind Velocity (kt)",extra=""),
                #dict(width=3,short='Temp',desc="Outside Air Temperature (C)",extra=""),
                dict(width=5,short='Alt',desc="Altitude/Flight Level",extra="(Altitude above mean sea level/flight level, e.g 4500ft or FL045)"),
                dict(width=3,short='TAS',desc="True Air Speed (kt)",extra="(the speed of the aircraft in relation to the air around it)"),
                dict(width=3,short='TT',desc="True Track (deg)",extra="(the true direction the aircraft is flying, relative to ground)"),
                dict(width=3,short='WCA',desc="Wind correction angle (deg)",extra=" (the compensation due to wind needed to stay on the True Track. Negative means you have to aim left, positive to aim right)"),
                dict(width=2,short='Var',desc="Variation (deg)",extra="(How much to the right of the true north pole, the compass is pointing. Negative numbers means the compass points to the left of the true north pole)"),
                dict(width=2,short='Dev',desc="Deviation (deg)",extra="(How much to the right of the magnetic north, the aircraft compass will be pointing, while travelling in the direction of the true track)"),
                dict(width=3,short='CH',desc="Compass Heading (deg)",extra="(The heading that should be flown on the airplane compass to end up at the right place)"),
                dict(width=3,short='D',desc="Distance (NM)",extra=""),
                dict(width=3,short='GS',desc="Ground Speed (kt)",extra=""),
                dict(width=5,short='Time',desc="Time (hours, minutes)",extra="")
                ]
       
        c.acname=trip.trip
        c.all_aircraft=meta.Session.query(Aircraft).filter(sa.and_(
                 Aircraft.user==session['user'])).all()
        
        return render('/flightplan.mako')
    def select_aircraft(self):
        tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==session['user'],Trip.trip==session['current_trip'])).one()
        tripobj.aircraft=request.params['change_aircraft']
        meta.Session.flush()
        meta.Session.commit()
        redirect_to(h.url_for(controller='flightplan',action="fuel"))
        
    def fuel(self):
        routes=list(meta.Session.query(Route).filter(sa.and_(
            Route.user==session['user'],Route.trip==session['current_trip'])).order_by(Route.waypoint1).all())
        tripobj=meta.Session.query(Trip).filter(sa.and_(
            Trip.user==session['user'],Trip.trip==session['current_trip'])).one()
        c.trip=tripobj.trip
        c.all_aircraft=list(meta.Session.query(Aircraft).filter(sa.and_(
            Aircraft.user==session['user'])).order_by(Aircraft.aircraft).all())
        if tripobj.acobj==None:
            c.routes=[]
            c.acwarn=True
            c.ac=None
        else:        
            c.routes=get_route(session['user'],session['current_trip'])
            c.acwarn=False
            c.ac=tripobj.acobj
            
        return render('/fuel.mako')
        
