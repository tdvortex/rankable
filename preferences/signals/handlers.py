from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from preferences.models import Item, Ranker
from preferences.cypher import delete_ranker, delete_item

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_ranker_for_new_user(sender, **kwargs):
    if kwargs['created']:
        created_user = kwargs['instance']
        Ranker(ranker_id=created_user.id).save()

@receiver(post_delete, sender=settings.AUTH_USER_MODEL)
def delete_ranker_of_deleted_user(sender, **kwargs):
    deleted_user = kwargs['instance']
    ranker_to_delete = Ranker.nodes.get(ranker_id=deleted_user.id)
    delete_ranker(ranker_to_delete)

@receiver(post_save, sender=settings.RANKED_ITEM_MODEL)
def create_item_for_new_object(sender, **kwargs):
    if kwargs['created']:
        created_item = kwargs['instance']
        Item(item_id=created_item.id).save()

@receiver(post_delete, sender=settings.RANKED_ITEM_MODEL)
def delete_item_of_deleted_object(sender, **kwargs):
    deleted_item = kwargs['instance']
    item_to_delete = Item.nodes.get(item_id=deleted_item.id)
    delete_item(item_to_delete)