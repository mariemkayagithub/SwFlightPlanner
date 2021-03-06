"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])
    map.minimization = False

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('/error/{action}', controller='error')
    map.connect('/error/{action}/{id}', controller='error')

    map.connect('/', controller='splash', action="index")

    map.connect('/recordings/download/{starttime}.kml', controller='recordings', action="kml")
    map.connect('/flightplan/{tripname}.gpx', controller='flightplan', action="gpx")
    map.connect('/flightplan/{tripname}.csv', controller='flightplan', action="excel")
    map.connect('/customsets/view/{setname}/{version}', controller='customsets', action="view")
    map.connect('/customsets/save/{setname}/{version}', controller='customsets', action="save")
    map.connect('/customsets/rename/{setname}', controller='customsets', action="rename")

    # CUSTOM ROUTES HERE

    map.connect('/{controller}/{action}')
    map.connect('/{controller}/{action}/{id}')

    return map
