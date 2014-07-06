import gevent
import gevent.monkey
gevent.monkey.patch_all()

import json
from tgext.socketio.pubsub import PubSubTGNamespace
from .utils import create_app, configure_app


class PingPong(PubSubTGNamespace):
    def on_publish_event(self):
        self.publish('test_channel', 'published_event')

    def subscribe_test_channel(self):
        return 'test_channel'

    def subscribe_blocked_channel(self):
        return False


class TestSocketIOPubSub(object):
    def test_basic_request(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'subscribe',
                                                              'endpoint': '',
                                                              'args': ['test_channel']}))
        sockio = resp.req.environ['socketio']
        namespace = resp.req.environ['socketio.namespace']

        listen_loop = namespace.jobs[0]
        listen_loop.join(0)  # Force context switch to _listen greenlet

        namespace.process_packet({'type': 'event',
                                  'name': 'publish_event',
                                  'endpoint': '',
                                  'args': []})

        listen_loop.join(0)  # Force context switch to _listen greenlet

        socketio_send_packet = sockio.send_packet
        socketio_send_packet.assert_called_once_with({'endpoint': '/test',
                                                      'type': 'event',
                                                      'name': 'pubblication',
                                                      'args': ('published_event',)})

    def test_subscribe_without_channel(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'subscribe',
                                                              'endpoint': '',
                                                              'args': []}))

        sockio = resp.req.environ['socketio']
        sockio.error.assert_called_once_with('channel_not_specified',
                                             'You must specify the channel you want to subscribe',
                                             msg_id=None, endpoint='/test', quiet=False)

    def test_subscribe_not_existing_channel(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'subscribe',
                                                              'endpoint': '',
                                                              'args': ['nonexisting']}))

        sockio = resp.req.environ['socketio']
        sockio.error.assert_called_once_with('channel_not_available',
                                             'Trying to subscribe to a channel not available',
                                             msg_id=None, endpoint='/test', quiet=False)

    def test_subscribe_blocked_channel(self):
        app = create_app(configure_app(PingPong))
        resp = app.request('/socketio/test', body=json.dumps({'type': 'event',
                                                              'name': 'subscribe',
                                                              'endpoint': '',
                                                              'args': ['blocked_channel']}))

        sockio = resp.req.environ['socketio']
        sockio.error.assert_called_once_with('subscription_rejected',
                                             'Your subscription has been rejected by server',
                                             msg_id=None, endpoint='/test', quiet=False)

