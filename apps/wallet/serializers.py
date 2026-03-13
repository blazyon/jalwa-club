from rest_framework import serializers
from .models import Wallet, Transaction


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'updated_at']
        read_only_fields = ['id', 'balance', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        # BUG FIX: cannot reference 'fields' as a variable inside read_only_fields
        fields = [
            'id', 'tx_type', 'amount', 'balance_after',
            'reference', 'description', 'category', 'created_at'
        ]
        read_only_fields = [
            'id', 'tx_type', 'amount', 'balance_after',
            'reference', 'description', 'category', 'created_at'
        ]
