from django.contrib import admin
from .models import Request, User, Results, Messages, Tariff


@admin.register(Messages)
class MessagesAdmin(admin.ModelAdmin):
    list_display = ("tag", "create_time")
    readonly_fields = ("create_time",)


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("days", "amount", "create_time")
    readonly_fields = ("create_time",)


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    search_fields = ["telegram_id"]
    list_display = ("telegram_id", "amount", "status", "tariff", "create_time")
    readonly_fields = ("telegram_id", "amount", "tariff", "create_time",)
    date_hierarchy = "create_time"


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ["telegram_id", "name", "username"]
    list_display = ("telegram_id", "name", "username", "subscription_end", "create_time")
    readonly_fields = ("telegram_id", "name", "create_time",)
    date_hierarchy = "create_time"


@admin.register(Results)
class ResultsAdmin(admin.ModelAdmin):
    search_fields = ["telegram_id"]
    list_display = ("telegram_id", "result", "create_time")
    # readonly_fields = ("telegram_id", "result", "create_time",)
    date_hierarchy = "create_time"
