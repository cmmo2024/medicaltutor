# -*- coding: utf-8 -*-
"""
Created on Sun Jan 26 23:06:28 2025

@author: Alejandro
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, UserStats

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create UserStats first
        stats = UserStats.objects.create(user=instance)
        # Then create UserProfile with the stats
        UserProfile.objects.create(user=instance, stats=stats)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()