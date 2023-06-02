# Generated by Django 4.2 on 2023-04-23 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_results'),
    ]

    operations = [
        migrations.CreateModel(
            name='Messages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='Время обновления')),
                ('tag', models.CharField(max_length=30, unique=True, verbose_name='Тег')),
                ('text', models.CharField(max_length=4096, verbose_name='Текст')),
            ],
            options={
                'verbose_name': 'Результат',
                'verbose_name_plural': 'Результаты',
            },
        ),
    ]
