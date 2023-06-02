from django.db import models
from datetime import date
from django.core.validators import MaxValueValidator, MinValueValidator


class TimeMixin(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    update_time = models.DateTimeField(auto_now=True, verbose_name='Время обновления')

    class Meta:
        abstract = True


class User(TimeMixin):
    telegram_id = models.BigIntegerField(verbose_name='ID телеграм', default=-1, unique=True)
    username = models.CharField(verbose_name='Ник пользователя', max_length=60, null=True, blank=True)
    name = models.CharField(verbose_name='Имя пользователя', max_length=60, null=True, blank=True)
    subscription_end = models.DateField(verbose_name='Дата окончания подписки', default=date.today)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Request(TimeMixin):
    telegram_id = models.BigIntegerField(verbose_name='ID телеграм', default=-1)
    amount = models.IntegerField(verbose_name='Сумма')
    status = models.BooleanField(verbose_name='Статус заявки', default=False)
    tariff = models.IntegerField(verbose_name='Количество дней')
    viewed = models.BooleanField(verbose_name='Просмотрена', default=False)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def user_link(self):
        return self.telegram_id


class Results(TimeMixin):
    telegram_id = models.BigIntegerField(verbose_name='ID телеграм', default=-1)
    result = models.IntegerField(verbose_name='Результат')

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'


class Messages(TimeMixin):
    tag = models.CharField(verbose_name='Тег', max_length=30, unique=True)
    text = models.CharField(verbose_name='Текст', max_length=4096)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'


class Tariff(TimeMixin):
    days = models.IntegerField(verbose_name='Дни', default=0)
    amount = models.IntegerField(verbose_name='Сумма', default=0)

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'
