from gevent.monkey import patch_all
from gevent import reinit
from socketio.server import SocketIOServer
from paste.deploy.converters import asbool


class DebugModeForbiddenException(Exception):
    pass


def socketio_server_runner(wsgi_app, global_config, **kw):
    ioresource = kw.get('socketio_resource', 'socketio')
    host = kw.get('host', '0.0.0.0')
    port = int(kw.get('port', 8080))
 
    reinit()
    patch_all(dns=False)

    debug = asbool(global_config.get('debug', False))
    if debug is True:
        raise DebugModeForbiddenException("The SocketIO server currently doesn't work "
                                          "with debug mode enabled. Set debug=false")

    print('Starting SocketIO HTTP server on http://%s:%s, resource %s' % (host, port, ioresource))
    SocketIOServer((host, port), wsgi_app, resource=ioresource).serve_forever()

