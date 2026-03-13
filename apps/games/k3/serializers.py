from rest_framework import serializers
from .models import K3Round, K3Bet


class K3RoundSerializer(serializers.ModelSerializer):
    seconds_remaining = serializers.IntegerField(read_only=True)
    is_accepting_bets = serializers.BooleanField(read_only=True)

    class Meta:
        model = K3Round
        fields = [
            'id', 'round_number', 'status',
            'dice1', 'dice2', 'dice3', 'total', 'result_tags',
            'seed_hash', 'starts_at', 'ends_at',
            'seconds_remaining', 'is_accepting_bets',
        ]
        read_only_fields = [
            'id', 'round_number', 'status',
            'dice1', 'dice2', 'dice3', 'total', 'result_tags',
            'seed_hash', 'starts_at', 'ends_at',
            'seconds_remaining', 'is_accepting_bets',
        ]


class PlaceK3BetSerializer(serializers.Serializer):
    bet_type = serializers.ChoiceField(choices=[
        'TOTAL', 'SIZE', 'PARITY', 'SPECIFIC_TRIPLE',
        'ANY_TRIPLE', 'SPECIFIC_DOUBLE', 'TWO_DIFFERENT', 'THREE_DIFFERENT'
    ])
    bet_value = serializers.CharField(max_length=32)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=10, max_value=10000)

    def validate_bet_value(self, value):
        return value.strip().upper()


class K3BetSerializer(serializers.ModelSerializer):
    round_number = serializers.IntegerField(source='round.round_number', read_only=True)
    bet_type_display = serializers.CharField(source='get_bet_type_display', read_only=True)

    class Meta:
        model = K3Bet
        fields = [
            'id', 'round_number', 'bet_type', 'bet_type_display',
            'bet_value', 'amount', 'potential_payout',
            'is_winner', 'payout_amount', 'settled_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'round_number', 'bet_type', 'bet_type_display',
            'bet_value', 'amount', 'potential_payout',
            'is_winner', 'payout_amount', 'settled_at', 'created_at',
        ]
