import gevent
import gevent.monkey
gevent.monkey.patch_all()

import json
from tg import predicates, require
from tgext.socketio import SocketIOTGNamespace
from .utils import create_app, configure_app


class AuthPong(SocketIOTGNamespace):
    @require(predicates.not_anonymous())
    def on_authenticated(self):
        self.emit('ok', {'sound':'pong'})

    @require(None)  # This is actually unsupported in TG. Here only to test to 100%
    def on_nopred(self):
        self.emit('ok', {'sound':'pong'})


class TestSocketIOAuth(object):
    def test_basic_request(self):
        app = create_app(configure_app(AuthPong), auth=True)
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'authenticated',
                                                              'endpoint': '',
                                                              'args': []}))

        socketio_send_packet = resp.req.environ['socketio'].send_packet
        socketio_send_packet.assert_called_once_with({'endpoint': '/test',
                                                      'type': 'event',
                                                      'name': 'ok',
                                                      'args': ({'sound': 'pong'},)})

    def test_unauthenticated(self):
        app = create_app(configure_app(AuthPong), auth=False)
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'authenticated',
                                                              'endpoint': '',
                                                              'args': []}))

        socketio_error = resp.req.environ['socketio'].error
        socketio_error.assert_called_once_with(
            'method_access_denied',
            'You do not have access to method "on_authenticated"',
            msg_id=None, endpoint='/test', quiet=False
        )

    def test_method_with_no_predicate(self):
        app = create_app(configure_app(AuthPong), auth=True)
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'nopred',
                                                              'endpoint': '',
                                                              'args': []}))

        socketio_error = resp.req.environ['socketio'].error
        socketio_error.assert_called_once_with('method_access_denied',
                                               'You do not have access to method "on_nopred"',
                                               msg_id=None, endpoint='/test', quiet=False)

    def test_method_not_found(self):
        app = create_app(configure_app(AuthPong), auth=True)
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'missingmethod',
                                                              'endpoint': '',
                                                              'args': []}))

        socketio_error = resp.req.environ['socketio'].error
        socketio_error.assert_called_once_with('no_such_method',
                                               'The method "on_missingmethod" was not found',
                                               msg_id=None, endpoint='/test', quiet=False)
