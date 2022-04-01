from django.db.models import Model, CharField, SmallIntegerField, TextField, ManyToManyField


class Genre(Model):
    name = CharField(max_length=20,
                     help_text='The name of the genre', unique=True)


class Star(Model):
    name = CharField(max_length=100, help_text='The name of the star')


class Movie(Model):
    # Required fields
    id = CharField(max_length=12, primary_key=True, help_text='IMDB film ID')
    title = CharField(max_length=100,
                      help_text='The English title of the film')
    # Required to differentiate rereleased films
    year = SmallIntegerField(help_text='The year of release')

    # Optional fields
    runtime = SmallIntegerField(null=True, blank=True,
                                help_text='Runtime in minutes')
    plot = TextField(blank=True, help_text='The year of release')
    content_rating = CharField(max_length=12, blank=True,
                               help_text='The MPAA rating of the film')

    # Database links
    genres = ManyToManyField(Genre, blank=True, related_name='movies')
    stars = ManyToManyField(Star, blank=True, related_name='movies')
