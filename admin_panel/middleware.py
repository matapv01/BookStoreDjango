from django.middleware.csrf import CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt

class CsrfExemptMiddleware(MiddlewareMixin):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Set csrf_exempt attribute on the view function
        if not getattr(callback, 'csrf_exempt', False):
            callback = csrf_exempt(callback)
        return callback(request, *callback_args, **callback_kwargs) 