About tgext.socketio
-------------------------

tgext.socketio provides an easy way to implement SocketIO in TurboGears2.
SocketIO support is provided by gevent-socketio and specific SocketIO server
based on gevent is provided.

Installing
-------------------------------

tgextsocketio can be installed from pypi::

    pip install tgext.socketio

Running
------------------------------

SocketIO support requires a custom GEvent based HTTP server to work
correctly, remember to edit your ``development.ini`` and add::

    [server:main]
    use = egg:tgext.socketio#socketio
    socketio-resource = socketio

    host = 127.0.0.1
    port = 8080

``tgext.socketio#socketio`` is the server provided by tgext.socketio
to correctly support SocketIO, while ``socketio-resource`` is the
path of your ``SocketIOController`` class.

By default ``socketio`` is used so you can mount a ``SocketIOController``
subclass under the ``RootController`` or you can mount it in any other location
and change your ``socketio-resource`` option.

Using SocketIOController
----------------------------------

``SocketIOController`` works like any other TurboGears controller but supports
serving ``SocketIOTGNamespace`` as sub controllers. ``SocketIOController`` can
also behave like any other TG Controller and provide normal web pages.

``SocketIOTGNamespace`` are subclasses of ``socketio.namespace.Basenamespace`` with
additional TurboGears features like ``@validate`` and ``@require`` support.
Please keep in mind that ``SocketIOTGNamespace`` requires at least TurboGears **2.3.1**,
if you want to use a previous TurboGears version you can still use ``SocketIOController``
with plain ``socketio.namespace.Basenamespace`` classes.

Usage Example
=====================

The following is a very simple example that handles two type of events
``ping`` and ``fireball`` and response on real time to those::

    from tgext.socketio import SocketIOTGNamespace, SocketIOController

    class PingPong(SocketIOTGNamespace):
        def on_ping(self, attack):
            if attack['type'] == 'fireball':
                for i in range(10):
                    self.emit('pong',{'sound':'bang!'})
            else:
                self.emit('pong',{'sound':'pong'})


    class SocketIO(SocketIOController):
        pingpong = PingPong

        @expose()
        def page(self, **kw):
            return '''
    <html>
    <body>
        <div>
            <a class="ping" href="#" data-attack="ping">Ping</a>
            <a class="ping" href="#" data-attack="fireball">Fireball</a>
            <a class="ping" href="#" data-attack="auto">Auto</a>
            <a class="ping" href="#" data-attack="error">Error</a>
        </div>
        <div id="result"></div>
        <script src="/javascript/jquery.js"></script>
        <script src="/javascript/socket.io.min.js"></script>
        <script>
        $(function(){
            var socket = io.connect('/pingpong', {'resource':'giovanni'});
            socket.on('pong',function(data){
                $('#result').append(data.sound + '<br/>');
            });
            socket.on('error',function(error, info) {
                if (error == 'method_access_denied') { alert(info); }
                else { console.log(info); alert(error); }
            });
            $('.ping').click(function(event){
                event.preventDefault();
                socket.emit('ping',{'type':$(this).data('attack')});
            });
        });
        </script>
    </body>
    </html>
    '''

    class RootController(BaseController):
        socketio = SocketIO()

Keep in mind that the ``SocketIOController`` must be mounted in the same location
specified by ``socketio-resource`` property in your configuration file.

Using Validators and Requirements
=====================================

``SocketIOTGNamespace`` also supports using ``@validate`` and
``@require`` TurboGears decorators.

The same example can be changed to provide validation and
permission checks with a few lines of code::

    from tg.validation import TGValidationError
    import random

    class NoFireBallValidator(object):
        def to_python(self, value, *args, **kw):
            type_ = value['type']
            if type_ == 'auto':
                return {'type': random.choice(['ping', 'fireball'])}
            elif type_ == 'error':
                raise TGValidationError('Got an error!')

            return value


    class PingPong(SocketIOTGNamespace):
        @require(predicates.not_anonymous())
        @validate({'attack': NoFireBallValidator()})
        def on_ping(self, attack):
            if attack['type'] == 'fireball':
                for i in range(10):
                    self.emit('pong',{'sound':'bang!'})
            else:
                self.emit('pong',{'sound':'pong'})

