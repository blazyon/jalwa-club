from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from .models import WingoRound, WingoBet
from .serializers import WingoRoundSerializer, PlaceBetSerializer, WingoBetSerializer
from .services import get_or_create_current_round, place_bet
from core.services import InsufficientBalanceError

VALID_MODES = {'1MIN', '3MIN', '5MIN'}


def _get_mode(request):
    mode = request.query_params.get('mode', '1MIN').upper()
    return mode if mode in VALID_MODES else '1MIN'


class CurrentRoundAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        mode = _get_mode(request)
        round_obj = get_or_create_current_round(mode=mode)
        return Response(WingoRoundSerializer(round_obj).data)


class RoundHistoryAPIView(generics.ListAPIView):
    serializer_class = WingoRoundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        mode = _get_mode(self.request)
        return WingoRound.objects.filter(
            mode=mode, status='COMPLETED'
        ).order_by('-round_number')[:50]


class PlaceBetAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = 'bet'

    def post(self, request):
        serializer = PlaceBetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mode = _get_mode(request)
        round_obj = get_or_create_current_round(mode=mode)
        try:
            bet = place_bet(
                user=request.user,
                round_id=round_obj.id,
                bet_type=serializer.validated_data['bet_type'],
                bet_value=serializer.validated_data['bet_value'],
                amount=serializer.validated_data['amount'],
            )
            return Response(WingoBetSerializer(bet).data, status=status.HTTP_201_CREATED)
        except InsufficientBalanceError as e:
            return Response({'error': str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred.'}, status=500)


class MyBetsAPIView(generics.ListAPIView):
    serializer_class = WingoBetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = WingoBet.objects.filter(
            user=self.request.user
        ).select_related('round').order_by('-created_at')

        mode = self.request.query_params.get('mode')
        if mode and mode.upper() in VALID_MODES:
            qs = qs.filter(round__mode=mode.upper())

        return qs[:100]
