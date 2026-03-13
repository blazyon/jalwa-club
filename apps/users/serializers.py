from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        # BUG FIX: removed 'avatar' — ImageField requires Pillow + multipart form;
        # omitting from registration serializer avoids crashes when Pillow is absent
        fields = ['username', 'email', 'password', 'password2', 'phone', 'referral_code']

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters.")
        if not value.isalnum() and '_' not in value:
            raise serializers.ValidationError(
                "Username may only contain letters, numbers, and underscores.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_referral_code(self, value):
        if value:
            try:
                return User.objects.get(referral_code=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid referral code.")
        return None

    def create(self, validated_data):
        referrer = validated_data.pop('referral_code', None)
        user = User.objects.create_user(**validated_data)
        if referrer:
            user.referred_by = referrer
            user.save(update_fields=['referred_by'])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone',
            'referral_code', 'date_joined', 'wallet_balance'
        ]
        read_only_fields = ['id', 'username', 'referral_code', 'date_joined', 'wallet_balance']

    def get_wallet_balance(self, obj):
        try:
            return str(obj.wallet.balance)
        except Exception:
            return '0.00'


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'referral_code',
            'is_blocked', 'is_active', 'date_joined', 'referred_by'
        ]
        read_only_fields = ['id', 'date_joined', 'referral_code']
