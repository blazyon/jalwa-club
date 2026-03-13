import logging
import time

logger = logging.getLogger('apps')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)
        duration = time.time() - start
        user = request.user.username if request.user.is_authenticated else 'anon'
        logger.info(
            f"{request.method} {request.path} | {response.status_code} | "
            f"{duration:.3f}s | user={user} | ip={self.get_client_ip(request)}"
        )
        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
