# middleware.py
import time
from django.http import HttpResponse

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.visitors = {}

    def __call__(self, request):
        ip_address = request.META.get('REMOTE_ADDR')
        current_time = time.time()
        time_window = 60  # 1 minute
        max_requests = 100  # limit to 100 requests per minute

        if ip_address not in self.visitors:
            self.visitors[ip_address] = []

        
        # Filter out timestamps older than the time window
        self.visitors[ip_address] = [timestamp for timestamp in self.visitors[ip_address] if timestamp > current_time - time_window]
        
        if len(self.visitors[ip_address]) >= max_requests:
            return HttpResponse("Too many requests", status=429)
        
        # Record new request timestamp
        self.visitors[ip_address].append(current_time)

        response = self.get_response(request)
        return response
