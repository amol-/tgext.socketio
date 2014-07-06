import gevent
import gevent.monkey
gevent.monkey.patch_all()

import json
from tgext.socketio import SocketIOTGNamespace
from .utils import create_app, configure_app
from tg import validate
from tg.validation import TGValidationError
from formencode import Invalid


class NoFireBallValidator(object):
    def to_python(self, value, *args, **kw):
        type_ = value['type']
        if type_ in ('auto', 'ping'):
            return {'type': 'ping'}
        elif type_ == 'formencode':
            raise Invalid('Invalid Type', value, {})
        elif type_ == 'exception_handler':
            # Let it pass to test PingPong.exception_handler_decorator
            return 'exception_handler'

        raise TGValidationError('Invalid Type')


class CustomSchema(object):
    def validate(self, params, state):
        return {'attack': NoFireBallValidator().to_python(params['attack'])}


class PingPong(SocketIOTGNamespace):
    def exception_handler_decorator(self, method):
        def wrap(*args, **kwargs):
            if kwargs['attack'] == 'exception_handler':
                self.emit('handled')
            else:
                method(*args, **kwargs)
        return wrap

    @validate({'attack': NoFireBallValidator()})
    def on_ping(self, attack):
        self.emit('pong', {'sound': 'pong'})

    @validate(CustomSchema())
    def on_custom_schema_ping(self, attack):
        self.emit('pong', {'sound': 'pong'})

    def ping_error(self, attack):
        self.emit('ping_error', {'attack': attack})

    @validate({'attack': NoFireBallValidator()},
              error_handler=ping_error)
    def on_handled_ping(self, attack):
        self.emit('pong', {'sound': 'pong'})


class TestSocketIOValidation(object):
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

    def test_auto_request(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'auto'}]}))

        socketio_send_packet = resp.req.environ['socketio'].send_packet
        socketio_send_packet.assert_called_once_with({'endpoint': '/test',
                                                      'type': 'event',
                                                      'name': 'pong',
                                                      'args': ({'sound': 'pong'},)})

    def test_failed_validation(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'invalid'}]}))

        socketio_error = resp.req.environ['socketio'].error
        socketio_error.assert_called_once_with('invalid_method_args',
                                               {'attack': 'Invalid Type'},
                                               msg_id=None, endpoint='/test', quiet=False)

    def test_failed_validation_formencode(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'formencode'}]}))

        socketio_error = resp.req.environ['socketio'].error
        socketio_error.assert_called_once_with('invalid_method_args',
                                               {'attack': 'Invalid Type'},
                                               msg_id=None, endpoint='/test', quiet=False)

    def test_failed_validation_custom_schema(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'custom_schema_ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'formencode'}]}))

        socketio_error = resp.req.environ['socketio'].error
        socketio_error.assert_called_once_with('invalid_method_args',
                                               'Invalid Type',
                                               msg_id=None, endpoint='/test', quiet=False)

    def test_exception_handler(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({
            'type': 'event',
            'name': 'ping',
            'endpoint': '',
            'args': [{'type': 'exception_handler'}]
        }))

        socketio_send_packet = resp.req.environ['socketio'].send_packet
        socketio_send_packet.assert_called_once_with({'endpoint': '/test',
                                                      'type': 'event',
                                                      'name': 'handled',
                                                      'args': tuple()})

    def test_error_handled_request(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'handled_ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'ping'}]}))

        socketio_send_packet = resp.req.environ['socketio'].send_packet
        socketio_send_packet.assert_called_once_with({'endpoint': '/test',
                                                      'type': 'event',
                                                      'name': 'pong',
                                                      'args': ({'sound': 'pong'},)})

    def test_error_handled_auto_request(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'handled_ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'auto'}]}))

        socketio_send_packet = resp.req.environ['socketio'].send_packet
        socketio_send_packet.assert_called_once_with({'endpoint': '/test',
                                                      'type': 'event',
                                                      'name': 'pong',
                                                      'args': ({'sound': 'pong'},)})

    def test_error_handled_failed_validation(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'handled_ping',
                                                              'endpoint': '',
                                                              'args': [{'type': 'invalid'}]}))

        socketio_error = resp.req.environ['socketio'].send_packet
        socketio_error.assert_called_once_with({'endpoint': '/test',
                                                'type': 'event',
                                                'name': 'ping_error',
                                                'args': ({'attack': {u'type': u'invalid'}},)})
