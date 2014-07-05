from socketio.namespace import BaseNamespace
from tg.predicates import NotAuthorizedError
from tg.decorators import Decoration
from tg._compat import default_im_func
from crank.util import get_params_with_argspec
from tg.controllers.decoratedcontroller import DecoratedController
from tg.validation import validation_errors, TGValidationError


class UnsupportedTGVersionException(Exception):
    pass


class SocketIOTGNamespace(BaseNamespace):
    def is_method_allowed(self, method_name):
        method = getattr(self, method_name, None)
        if method is None:
            return True  # method not found case handled later

        deco = Decoration.get_decoration(default_im_func(method))
        try:
            requirement = deco.requirement
        except AttributeError:  # pragma: no cover
            raise UnsupportedTGVersionException('tgext.socketio requires at least '
                                                'TurboGears 2.3.1')

        if requirement is None:
            return super(SocketIOTGNamespace, self).is_method_allowed(method_name)

        predicate = requirement.predicate
        if predicate is None:
            return False

        try:
            predicate.check_authorization(self.request.environ)
        except NotAuthorizedError as e:
            return False

        return super(SocketIOTGNamespace, self).is_method_allowed(method_name)

    def call_method(self, method_name, packet, *args):
        method = getattr(self, method_name, None)
        if method is not None:
            deco = Decoration.get_decoration(default_im_func(method))
            validation = deco.validation
            if validation:
                validate_params = get_params_with_argspec(method, {}, args)

                try:
                    params = DecoratedController._perform_validate(method, validate_params)
                except validation_errors as inv:
                    if deco.validation.error_handler:
                        handler, output = DecoratedController._handle_validation_errors(method,
                                                                                        args, {},
                                                                                        inv, self)
                        return output
                    else:
                        if isinstance(inv, TGValidationError):
                            error_dict = inv.error_dict.items()
                            error_dict = dict((key, str(error)) for key,error in error_dict)
                            self.error("invalid_method_args", error_dict)
                        else:
                            self.error("invalid_method_args", str(inv))
                        return

                # Check if we need to decorate to handle exceptions
                if hasattr(self, 'exception_handler_decorator'):
                    method = self.exception_handler_decorator(method)

                return method(**params)

        return super(SocketIOTGNamespace, self).call_method(method_name, packet, *args)