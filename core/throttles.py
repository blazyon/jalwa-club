from rest_framework.throttling import UserRateThrottle


class BetRateThrottle(UserRateThrottle):
    scope = 'bet'
