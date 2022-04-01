from urllib import response
from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html, urlize
from django.urls import reverse
from django.db.models import Count
from .models import Genre, Star, Movie
from .imdb import do_populate_movies


@admin.action(description='Pull 250 more movies from IMDB-API')
def get_new_movies(modeladmin, request, queryset):
    response = do_populate_movies()
    return


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'year', 'runtime', 'content_rating']
    search_fields = ['title']
    actions = [get_new_movies]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Star)
class StarAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
