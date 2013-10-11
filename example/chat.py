from tg import expose, TGController, AppConfig
from tgext.socketio import SocketIOController
from tgext.socketio.pubsub import PubSubTGNamespace
from tgext.socketio.server import socketio_server_runner
import uuid


class ChatNamespace(PubSubTGNamespace):
    def subscribe_room(self, roomid):
        self.session['uid'] = str(uuid.uuid4())
        self.session['channel'] = 'room-%s' % roomid
        self.emit('userid', self.session['uid'])
        return self.session['channel']

    def on_user_message(self, message):
        self.publish(self.session['channel'], {'uid': self.session['uid'],
                                               'message': message})


class SocketIO(SocketIOController):
    chat = ChatNamespace


class RootController(TGController):
    socketio = SocketIO()

    @expose()
    def index(self):
        return '''<!DOCTYPE html>
<html>
    <head>
        <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
        <script type="text/javascript" src="//cdnjs.cloudflare.com/ajax/libs/socket.io/0.9.16/socket.io.min.js"></script>
        <script>
            WEB_SOCKET_DEBUG = true;
            var socket = io.connect('/chat', {'resource':'socketio'});
            var userid = null;

            $(window).bind("beforeunload", function() {
                socket.disconnect();
            });

            socket.on('connect', function () {
                socket.emit('subscribe', 'room', '1');
            });

            socket.on('pubblication', function (data) {
                var sender = data.uid;
                var msg = data.message;
                $('#lines').append($('<p>').append($('<em>').text(msg)));
            });

            socket.on('userid', function (myid) {
                userid = myid;
            });

            $(function () {
                $('#send-message').submit(function () {
                    socket.emit('user_message', $('#message').val());
                    $('#message').val('').focus();
                    $('#lines').get(0).scrollTop = 10000000;
                    return false;
                });
            });
        </script>
    </head>
    <body>
      <div id="chat">
        <div id="messages">
          <div id="lines"></div>
        </div>
        <form id="send-message">
          <input id="message">
          <button>Send</button>
        </form>
      </div>
    </body>
</html>
'''


config = AppConfig(minimal=True, root_controller=RootController())
config['anypubsub.backend'] = 'redis'
socketio_server_runner(config.make_wsgi_app(), config, socketio_resource='socketio')