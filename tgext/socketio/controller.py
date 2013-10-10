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
            abort(406)

        socketio_manage(request.environ, self._socketio_namespaces, request)
        return 'done'
