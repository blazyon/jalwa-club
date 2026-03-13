from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from .models import FiveDRound, FiveDbet
from .serializers import FiveDRoundSerializer, PlaceFiveDSerializer, FiveDBetSerializer
from .services import get_or_create_current_round, place_bet
from core.services import InsufficientBalanceError


class CurrentFiveDRoundAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(FiveDRoundSerializer(get_or_create_current_round()).data)


class FiveDHistoryAPIView(generics.ListAPIView):
    serializer_class = FiveDRoundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FiveDRound.objects.filter(status='COMPLETED').order_by('-round_number')[:50]


class PlaceFiveDAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = 'bet'

    def post(self, request):
        serializer = PlaceFiveDSerializer(data=request.data)
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
            return Response(FiveDBetSerializer(bet).data, status=status.HTTP_201_CREATED)
        except InsufficientBalanceError as e:
            return Response({'error': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred.'}, status=500)


class MyFiveDBetsAPIView(generics.ListAPIView):
    serializer_class = FiveDBetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FiveDbet.objects.filter(
            user=self.request.user
        ).select_related('round').order_by('-created_at')[:50]
