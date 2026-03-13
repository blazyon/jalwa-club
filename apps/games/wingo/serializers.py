from rest_framework import serializers
from .models import WingoRound, WingoBet


class WingoRoundSerializer(serializers.ModelSerializer):
    seconds_remaining = serializers.IntegerField(read_only=True)
    is_accepting_bets = serializers.BooleanField(read_only=True)
    duration_seconds = serializers.IntegerField(read_only=True)

    class Meta:
        model = WingoRound
        fields = [
            'id', 'mode', 'round_number', 'status',
            'result_number', 'result_color', 'result_size',
            'seed_hash', 'starts_at', 'ends_at',
            'seconds_remaining', 'is_accepting_bets', 'duration_seconds',
        ]
        read_only_fields = fields


class PlaceBetSerializer(serializers.Serializer):
    bet_type = serializers.ChoiceField(choices=['NUMBER', 'COLOR', 'SIZE'])
    bet_value = serializers.CharField(max_length=16)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=10, max_value=10000)

    def validate_bet_value(self, value):
        return value.strip().upper()


class WingoBetSerializer(serializers.ModelSerializer):
    round_number = serializers.IntegerField(source='round.round_number', read_only=True)
    round_mode = serializers.CharField(source='round.mode', read_only=True)
    bet_type_display = serializers.CharField(source='get_bet_type_display', read_only=True)
    result_number = serializers.IntegerField(source='round.result_number', read_only=True)
    result_color = serializers.CharField(source='round.result_color', read_only=True)
    result_size = serializers.CharField(source='round.result_size', read_only=True)

    class Meta:
        model = WingoBet
        fields = [
            'id', 'round_number', 'round_mode', 'bet_type', 'bet_type_display',
            'bet_value', 'amount', 'potential_payout',
            'is_winner', 'payout_amount', 'settled_at', 'created_at',
            'result_number', 'result_color', 'result_size',
        ]
        read_only_fields = fields
