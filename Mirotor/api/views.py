from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from .models import User, Request, Results, Messages, Tariff
from . import serializers
from django.dispatch import receiver
from django.db.models.signals import pre_save
from datetime import datetime, timedelta
from rest_framework import filters


class RegistrationView(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    permission_classes = [AllowAny]
    serializer_class = serializers.RegistrationSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        telegram_id = self.request.GET.get('telegram_id', None)
        if telegram_id:
            return User.objects.filter(telegram_id=telegram_id)
        else:
            return User.objects.all()


class RequestView(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    permission_classes = [AllowAny]
    serializer_class = serializers.RequestSerializer
    queryset = Request.objects.all()
    ordering_fields = ['pk']
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self):
        telegram_id = self.request.GET.get('telegram_id', None)
        if telegram_id:
            return Request.objects.filter(telegram_id=telegram_id)
        else:
            return Request.objects.all()


class ResultsView(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    permission_classes = [AllowAny]
    serializer_class = serializers.ResultsSerializer
    queryset = Results.objects.all()
    ordering_fields = ['pk']
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self):
        telegram_id = self.request.GET.get('telegram_id', None)
        if telegram_id:
            return Results.objects.filter(telegram_id=telegram_id)
        else:
            return Results.objects.all()


class AdminRequestView(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                       mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    permission_classes = [AllowAny]
    serializer_class = serializers.RequestSerializer
    queryset = Request.objects.filter(status=False, viewed=False)


class MessagesView(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                   mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    permission_classes = [AllowAny]
    serializer_class = serializers.MessagesSerializer
    queryset = Messages.objects.all()

    def get_queryset(self):
        tag = self.request.GET.get('tag', None)
        if tag:
            return Messages.objects.filter(tag=tag)
        else:
            return Messages.objects.all()


class TariffView(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin,
                 mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    permission_classes = [AllowAny]
    serializer_class = serializers.TariffSerializer
    queryset = Tariff.objects.all()
    ordering_fields = ['days']
    filter_backends = [filters.OrderingFilter]


@receiver(pre_save, sender=Request)
def my_callback(sender, instance, *args, **kwargs):
    current_request = Request.objects.filter(pk=instance.pk)
    if current_request:
        current_request = current_request.first()
        if current_request.telegram_id != instance.telegram_id:
            raise Exception('Changing telegram_id')
        if current_request.amount != instance.amount:
            raise Exception('Changing amount')
        if current_request.tariff != instance.tariff:
            raise Exception('Changing tariff')
        if not current_request.status and instance.status:
            user = User.objects.get(telegram_id=instance.telegram_id)
            if user:
                user.subscription_end = max(user.subscription_end, datetime.today().date()) + timedelta(
                    days=instance.tariff)
                user.save()
