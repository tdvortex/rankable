from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from core.models import Movie as MovieNode, User as UserNode
from movies.models import Movie
from users.models import User
from preferences.cypher import delete_ranker, delete_item


@receiver(post_save, sender=Movie)
def create_node_for_new_movie(sender, **kwargs):
    if kwargs['created']:
        created_movie = kwargs['instance']
        MovieNode(item_id=created_movie.id).save()  

@receiver(post_delete, sender=Movie)
def delete_node_of_deleted_movie(sender, **kwargs):
    deleted_movie = kwargs['instance']
    node_to_delete = MovieNode.nodes.get(item_id=deleted_movie.id)
    delete_item(node_to_delete)

@receiver(post_save, sender=User)
def create_node_for_new_user(sender, **kwargs):
    if kwargs['created']:
        created_user = kwargs['instance']
        UserNode(ranker_id=created_user.id).save()  

@receiver(post_delete, sender=User)
def delete_node_of_deleted_user(sender, **kwargs):
    deleted_user = kwargs['instance']
    node_to_delete = UserNode.nodes.get(ranker_id=deleted_user.id)
    delete_ranker(node_to_delete)