from rest_framework import serializers
from .models import FiveDRound, FiveDbet


class FiveDRoundSerializer(serializers.ModelSerializer):
    seconds_remaining = serializers.IntegerField(read_only=True)
    is_accepting_bets = serializers.BooleanField(read_only=True)
    digits = serializers.ListField(
        child=serializers.IntegerField(),
        read_only=True
    )
    total_size = serializers.SerializerMethodField()
    total_parity = serializers.SerializerMethodField()

    class Meta:
        model = FiveDRound
        fields = [
            'id', 'round_number', 'status',
            'digit_a', 'digit_b', 'digit_c', 'digit_d', 'digit_e',
            'total', 'digits', 'total_size', 'total_parity',
            'seed_hash', 'starts_at', 'ends_at',
            'seconds_remaining', 'is_accepting_bets',
        ]
        read_only_fields = [
            'id', 'round_number', 'status',
            'digit_a', 'digit_b', 'digit_c', 'digit_d', 'digit_e',
            'total', 'digits', 'total_size', 'total_parity',
            'seed_hash', 'starts_at', 'ends_at',
            'seconds_remaining', 'is_accepting_bets',
        ]

    def get_total_size(self, obj):
        if obj.total is None:
            return None
        return 'BIG' if obj.total >= 23 else 'SMALL'

    def get_total_parity(self, obj):
        if obj.total is None:
            return None
        return 'ODD' if obj.total % 2 != 0 else 'EVEN'


class PlaceFiveDSerializer(serializers.Serializer):
    bet_type = serializers.ChoiceField(choices=[
        'POSITION', 'TOTAL_SIZE', 'TOTAL_PARITY', 'EXACT_TOTAL'
    ])
    bet_value = serializers.CharField(max_length=32)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=10, max_value=10000)

    def validate_bet_value(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        bet_type = attrs.get('bet_type', '').upper()
        bet_value = attrs.get('bet_value', '').upper()

        if bet_type == 'POSITION':
            # Must be format "A:3" through "E:9"
            parts = bet_value.split(':')
            if len(parts) != 2 or parts[0] not in 'ABCDE' or not parts[1].isdigit():
                raise serializers.ValidationError(
                    {'bet_value': 'Position bet must be in format "A:3" (position A-E, digit 0-9).'}
                )
            if not (0 <= int(parts[1]) <= 9):
                raise serializers.ValidationError(
                    {'bet_value': 'Digit must be between 0 and 9.'}
                )

        elif bet_type == 'TOTAL_SIZE':
            if bet_value not in ('BIG', 'SMALL'):
                raise serializers.ValidationError(
                    {'bet_value': 'TOTAL_SIZE must be BIG or SMALL.'}
                )

        elif bet_type == 'TOTAL_PARITY':
            if bet_value not in ('ODD', 'EVEN'):
                raise serializers.ValidationError(
                    {'bet_value': 'TOTAL_PARITY must be ODD or EVEN.'}
                )

        elif bet_type == 'EXACT_TOTAL':
            try:
                t = int(bet_value)
                if not (0 <= t <= 45):
                    raise ValueError
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    {'bet_value': 'EXACT_TOTAL must be a number between 0 and 45.'}
                )

        return attrs


class FiveDBetSerializer(serializers.ModelSerializer):
    round_number = serializers.IntegerField(source='round.round_number', read_only=True)
    bet_type_display = serializers.CharField(source='get_bet_type_display', read_only=True)

    class Meta:
        model = FiveDbet
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
