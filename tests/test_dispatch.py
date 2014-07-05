import gevent
import gevent.monkey
gevent.monkey.patch_all()

from webtest import TestApp
import json
from tg import AppConfig, config
from tg.configuration import milestones
from tg.configuration.auth import TGAuthMetadata
from tg import TGController, expose, request

from socketio.virtsocket import Socket
from tgext.socketio import SocketIOTGNamespace
from mock import MagicMock


class PingPong(SocketIOTGNamespace):
    def on_ping(self, attack):
        if attack['type'] == 'fireball':
            for i in range(10):
                self.emit('pong',{'sound':'bang!'})
        else:
            self.emit('pong',{'sound':'pong'})

class MockSocketIOServer(object):
    """Mock a SocketIO server"""
    def __init__(self, *args, **kwargs):
        self.sockets = {}

    def get_socket(self, socket_id=''):
        return self.sockets.get(socket_id)


class MockSocket(Socket):
    pass

def configure_app(namespace):
    # Simulate starting configuration process from scratch
    if milestones.renderers_ready.reached:
        milestones._reset_all()

    from tgext.socketio import SocketIOController

    class SocketIO(SocketIOController):
        test = namespace

    class RootController(TGController):
        socketio = SocketIO()

        def __call__(self, *args, **kwargs):
            if request.environ.get('mocksocketio', True) != 'false':
                server = MockSocketIOServer()
                socket = MockSocket(server, {})
                socket.error = MagicMock()
                socket.send_packet = MagicMock()
                request.environ['socketio'] = socket

            request.identity = request.environ.get('repoze.who.identity')
            return super(TGController, self).__call__(*args, **kwargs)

    app_cfg = AppConfig(minimal=True, root_controller=RootController())
    return app_cfg


def create_app(app_config, auth=False):
    app = app_config.make_wsgi_app(skip_authentication=True)
    if auth:
        return TestApp(app, extra_environ=dict(REMOTE_USER='user'))
    else:
        return TestApp(app)


class TestSocketIODispatch(object):
    def test_basic_request(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'ping'}]}))
        print resp.req.environ['socketio'].send_packet.call_args_list

    def test_invalid_request_notsocketio(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', environ={'mocksocketio': 'false'}, status=406)

    def test_invalid_request_nonamespace(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/none', status=406)



