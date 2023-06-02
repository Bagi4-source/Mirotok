from rest_framework import serializers
from . import models


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = [
            'pk',
            'telegram_id',
            'name',
            'username',
            'subscription_end',
            'create_time',
            'update_time'
        ]
        read_only_fields = [
            'create_time',
            'update_time'
        ]


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Request
        fields = [
            'pk',
            'telegram_id',
            'amount',
            'status',
            'tariff',
            'viewed',
            'create_time',
            'update_time'
        ]
        read_only_fields = [
            'create_time',
            'update_time'
        ]


class ResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Results
        fields = [
            'pk',
            'telegram_id',
            'result',
            'create_time'
        ]
        read_only_fields = [
            'create_time'
        ]


class MessagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Messages
        fields = [
            'pk',
            'tag',
            'text',
            'create_time'
        ]
        read_only_fields = [
            'create_time'
        ]


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tariff
        fields = [
            'pk',
            'days',
            'amount'
        ]
        read_only_fields = [
            'create_time'
        ]
