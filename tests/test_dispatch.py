import gevent
import gevent.monkey
gevent.monkey.patch_all()

import json
from tgext.socketio import SocketIOTGNamespace
from .utils import create_app, configure_app


class PingPong(SocketIOTGNamespace):
    def on_ping(self, attack):
        if attack['type'] == 'fireball':
            for i in range(10):
                self.emit('pong', {'sound':'bang!'})
        else:
            self.emit('pong', {'sound':'pong'})


class TestSocketIODispatch(object):
    def test_basic_request(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'ping'}]}))

        socketio_send_packet = resp.req.environ['socketio'].send_packet
        socketio_send_packet.assert_called_once_with({'endpoint': '/test',
                                                      'type': 'event',
                                                      'name': 'pong',
                                                      'args': ({'sound': 'pong'},)})

    def test_invalid_request_notsocketio(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', environ={'mocksocketio': 'false'}, status=406)

    def test_invalid_request_nonamespace(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/none', status=406)

    def test_method_not_found(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'missingmethod',
                                                              'endpoint': '',
                                                              'args': [{'type': 'ping'}]}))

        socketio_error = resp.req.environ['socketio'].error
        socketio_error.assert_called_once_with('no_such_method',
                                               'The method "on_missingmethod" was not found',
                                               msg_id=None, endpoint='/test', quiet=False)
