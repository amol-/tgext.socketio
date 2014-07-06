from .namespace import SocketIOTGNamespace
from tg import config
from anypubsub import create_pubsub_from_settings
from threading import Lock
import json

PUBSUB_CREATION_LOCK = Lock()


class PubSubTGNamespace(SocketIOTGNamespace):
    @classmethod
    def pubsub(cls):
        globals = config['tg.app_globals']
        pubsub = getattr(globals, 'anypubsub', None)

        if pubsub is None:
            PUBSUB_CREATION_LOCK.acquire()
            pubsub = getattr(globals, 'anypubsub', None)
            if pubsub is None:
                pubsub = create_pubsub_from_settings(config, prefix='anypubsub.')
                globals.anypubsub = pubsub
            PUBSUB_CREATION_LOCK.release()

        return pubsub

    def on_subscribe(self, packet):
        args = packet['args']
        if not args:
            self.error('channel_not_specified', 'You must specify the channel you want '
                                                'to subscribe')
            return False

        channel = args.pop(0)
        method_name = 'subscribe_' + channel.replace(' ', '_')

        subscribe_handler = getattr(self, method_name, None)
        if subscribe_handler is None:
            self.error('channel_not_available', 'Trying to subscribe to a channel not available')
            return False

        suggested_channel = self.call_method_with_acl(method_name, packet, *args)
        if suggested_channel is not False:
            channel = suggested_channel or channel
            self.spawn(self._listen, channel)
            return True

        self.error('subscription_rejected', 'Your subscription has been rejected by server')
        return False

    def publish(self, channel, message):
        message = json.dumps(message)
        self.pubsub().publish(channel, message)

    def _listen(self, channel):
        subscription = PubSubTGNamespace.pubsub().subscribe(channel)
        for message in subscription:
            data = json.loads(message)
            self.emit('pubblication', data)



