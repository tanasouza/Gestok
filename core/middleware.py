"""
Core middleware for Gestok.
"""
from django.shortcuts import redirect
from django.urls import reverse


class FirstAccessMiddleware:
    """
    Middleware that forces users with primeiro_acesso=True
    to change their password before accessing any other page.
    """

    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/primeiro-acesso/',
        '/admin/',
        '/static/',
        '/api/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user has primeiro_acesso flag
            if hasattr(request.user, 'primeiro_acesso') and request.user.primeiro_acesso:
                # Allow access only to exempt URLs
                path = request.path
                if not any(path.startswith(url) for url in self.EXEMPT_URLS):
                    try:
                        return redirect(reverse('accounts:primeiro_acesso'))
                    except Exception:
                        pass

        response = self.get_response(request)
        return response


import threading

_thread_locals = threading.local()

def get_current_request():
    """Returns the current HTTP request from thread storage."""
    return getattr(_thread_locals, 'request', None)

class ThreadLocalMiddleware:
    """Middleware that stores the current request object in thread-local storage."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            if hasattr(_thread_locals, 'request'):
                del _thread_locals.request
        return response
