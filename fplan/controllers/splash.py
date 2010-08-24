import logging
import sqlalchemy as sa
from md5 import md5
from fplan.model import meta,User,Trip,Waypoint,Route
from datetime import datetime
from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
import routes.util as h
from fplan.extract.extracted_cache import get_aip_download_time
from fplan.lib.base import BaseController, render
from fplan.lib.maptilereader import get_tiles_timestamp
log = logging.getLogger(__name__)

class SplashController(BaseController):

    def index(self):
        c.expl=request.params.get("explanation","")
        return render('/splash.mako')
    def logout(self):
        del session['user']
        session.save()
        redirect_to(h.url_for(controller='splash',action="index"))
    def about(self):
        try:
            c.aipupdate=get_aip_download_time()            
        except Exception,cause:
            c.aipupdate=None
        try:
            c.mapupdate=get_tiles_timestamp()
        except:
            c.mapupdate=datetime(1970,1,1)
        
        return render('/about.mako')
    
    def login(self):
        users=meta.Session.query(User).filter(sa.and_(
                User.user==request.params['username'])
                ).all()
        if len(users)==1:
            user=users[0]
            print "Attempt to login as %s with password %s (correct password is %s)"%(request.params['username'],md5(request.params['password']).hexdigest(),user.password)
            if user.password==md5(request.params['password']).hexdigest():
                session['user']=users[0].user
                session.save()
                redirect_to(h.url_for(controller='mapview',action="index"))
            else:
                print "Bad password!"
                user.password=md5(request.params['password']).hexdigest()                
                redirect_to(h.url_for(controller='splash',action="index",explanation="Wrong password"))
        else:
            redirect_to(h.url_for(controller='splash',action="index",explanation="No such user"))
       
