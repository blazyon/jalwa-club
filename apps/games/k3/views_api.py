from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from .models import K3Round, K3Bet
from .serializers import K3RoundSerializer, PlaceK3BetSerializer, K3BetSerializer
from .services import get_or_create_current_round, place_bet
from core.services import InsufficientBalanceError


class CurrentK3RoundAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        round_obj = get_or_create_current_round()
        return Response(K3RoundSerializer(round_obj).data)


class K3RoundHistoryAPIView(generics.ListAPIView):
    serializer_class = K3RoundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return K3Round.objects.filter(status='COMPLETED').order_by('-round_number')[:50]


class PlaceK3BetAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = 'bet'

    def post(self, request):
        serializer = PlaceK3BetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        round_obj = get_or_create_current_round()
        try:
            bet = place_bet(
                user=request.user,
                round_id=round_obj.id,
                bet_type=serializer.validated_data['bet_type'],
                bet_value=serializer.validated_data['bet_value'],
                amount=serializer.validated_data['amount'],
            )
            return Response(K3BetSerializer(bet).data, status=status.HTTP_201_CREATED)
        except InsufficientBalanceError as e:
            return Response({'error': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred.'}, status=500)


class MyK3BetsAPIView(generics.ListAPIView):
    serializer_class = K3BetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return K3Bet.objects.filter(
            user=self.request.user
        ).select_related('round').order_by('-created_at')[:50]
