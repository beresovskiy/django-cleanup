import os
from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.db.models.loading import cache
from django.core.files.storage import get_storage_class

def find_models_with_filefield(): 
    result = []
    for app in cache.get_apps():
        model_list = cache.get_models(app)
        for model in model_list:
            for field in model._meta.fields:
                if isinstance(field, models.FileField):
                    result.append(model)
                    break
    return result

def remove_old_files(sender, instance, **kwargs):
    if not instance.id:
        return

    try:
        old_instance = instance.__class__.objects.get(id=instance.id)
    except instance.DoesNotExist:
        return

    for field in instance._meta.fields:
        if not isinstance(field, models.FileField):
            continue
        old_file = getattr(old_instance, field.name)
        new_file = getattr(instance, field.name)
        storage = old_file.storage
        if old_file and old_file != new_file and storage.exists(old_file.name):
            try:
                storage.delete(old_file.name)
            except OSError, NotImplementedError:
                pass

def remove_files(sender, instance, **kwargs):
    import pprint

    for field in instance._meta.fields:
        if not isinstance(field, models.FileField):
            continue
        file = getattr(instance, field.name)
        storage = file.storage
        if file and storage and storage.exists(file.name):
            try:
                storage.delete(file.name)
            except OSError, NotImplementedError:
                pass


for model in find_models_with_filefield():
    pre_save.connect(remove_old_files, sender=model)
    post_delete.connect(remove_files, sender=model)

