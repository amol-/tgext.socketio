from tgext.socketio.server import socketio_server_runner, DebugModeForbiddenException
import mock
from nose.tools import raises


class TestServer(object):
    def test_configuration(self):
        with mock.patch('socketio.server.SocketIOServer.serve_forever') as sockio_serve:
            with mock.patch('socketio.server.SocketIOServer.__init__',
                            return_value=None) as sockio_init:
                    socketio_server_runner(None, {'debug': False},
                                           host='192.168.0.1',
                                           port=9100,
                                           socketio_resource='somewhere')
            sockio_init.assert_called_once_with(('192.168.0.1', 9100), None, resource='somewhere')
        sockio_serve.assert_called_once()

    @raises(DebugModeForbiddenException)
    def test_debug_disabled(self):
        socketio_server_runner(None, {'debug': True},
                               host='192.168.0.1',
                               port=9100,
                               socketio_resource='somewhere')


