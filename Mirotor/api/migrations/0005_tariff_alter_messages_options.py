# Generated by Django 4.2 on 2023-04-23 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_messages'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tariff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='Время обновления')),
                ('days', models.IntegerField(default=0, verbose_name='Дни')),
                ('amount', models.IntegerField(default=0, verbose_name='Сумма')),
            ],
            options={
                'verbose_name': 'Тариф',
                'verbose_name_plural': 'Тарифы',
            },
        ),
        migrations.AlterModelOptions(
            name='messages',
            options={'verbose_name': 'Сообщение', 'verbose_name_plural': 'Сообщения'},
        ),
    ]
