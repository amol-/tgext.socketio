from mock import MagicMock
from tg.configuration.auth import TGAuthMetadata
from webtest import TestApp
from tg import AppConfig
from tg.configuration import milestones
from tg import TGController, request

from socketio.virtsocket import Socket


class FakeUser(object):
    """
    Fake user that emulates an users without the need to actually
    query it from the database, it is able to trick sprox when
    resolving relations to the blog post Author.
    """
    def __int__(self):
        return 1

    def __getattr__(self, item):
        if item == 'user_id':
            return 1
        elif item == '_id':
            return self
        return super(FakeUser, self).__getattr__(item)


class TestAuthMetadata(TGAuthMetadata):
    def authenticate(self, environ, identity):
        return 'user'

    def get_user(self, identity, userid):
        if userid:
            return FakeUser()

    def get_groups(self, identity, userid):
        if userid:
            return ['managers']
        return []

    def get_permissions(self, identity, userid):
        if userid:
            return ['turbopress']
        return []


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
    app_cfg.sa_auth.authmetadata = TestAuthMetadata()
    app_cfg['beaker.session.secret'] = 'SECRET'
    app_cfg.auth_backend = 'ming'

    return app_cfg


def create_app(app_config, auth=False):
    app = app_config.make_wsgi_app(skip_authentication=True)
    if auth:
        return TestApp(app, extra_environ=dict(REMOTE_USER='user'))
    else:
        return TestApp(app)

