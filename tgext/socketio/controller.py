import json
from tg import TGController, expose, request, abort
from socketio import socketio_manage
from socketio.namespace import BaseNamespace


class SocketIOController(TGController):
    def __init__(self, *args, **kw):
        super(SocketIOController, self).__init__()
        self._socketio_namespaces = {}
        for name, value in vars(self.__class__).items():
            try:
                is_socketio_namespace = issubclass(value, BaseNamespace)
            except TypeError:
                is_socketio_namespace = False

            if is_socketio_namespace:
                self._socketio_namespaces['/' + name] = value

    @expose()
    def _default(self, *args, **kw):
        req = request._current_obj()

        if 'socketio' not in req.environ:
            abort(400)

        if 'paste.testing_variables' in req.environ:
            # We are in a test unit called by WebTest
            # simulate a socketio server by directly sending
            # data from wsgi.input to the namespace
            namespace_path = '/' + args[0]
            namespace = self._socketio_namespaces.get(namespace_path)
            if not namespace:
                abort(400)

            namespace_instance = namespace(req.environ, namespace_path, req)
            req.environ['socketio.namespace'] = namespace_instance
            packet = json.loads(req.environ['wsgi.input'].read())
            namespace_instance.process_packet(packet)
        else:  # pragma: no cover
            socketio_manage(req.environ, self._socketio_namespaces, req)

        return 'done'
