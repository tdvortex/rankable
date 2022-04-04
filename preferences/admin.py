from django.contrib import admin as dj_admin
from django_neomodel import admin as neo_admin
from .models import Item, Ranker


class ItemAdmin(dj_admin.ModelAdmin):
    list_display = ['item_id']


class RankerAdmin(dj_admin.ModelAdmin):
    list_display = ['ranker_id']


neo_admin.register(Ranker, RankerAdmin)
neo_admin.register(Item, ItemAdmin)
