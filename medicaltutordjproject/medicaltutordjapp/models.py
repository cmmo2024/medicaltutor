from django.db import models
from django.contrib.auth.models import User  


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    plan = models.ForeignKey('Plans', on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.plan_name if self.plan else 'No Plan'}"


class Payments(models.Model):
    payment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  
    amount = models.FloatField()
    card_number = models.TextField()
    payment_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'payments'


class Plans(models.Model):
    plan_id = models.AutoField(primary_key=True)
    plan_name = models.TextField()
    price = models.FloatField()
    max_queries_per_month = models.IntegerField(blank=True, null=True)
    max_quizzes_per_month = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'plans'


class Quizzes(models.Model):
    quiz_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # Link to Django's User model
    topic = models.TextField()
    matter = models.TextField()
    questions_count = models.IntegerField()
    score = models.FloatField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'quizzes'


class UserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, primary_key=True)  # Link to Django's User model
    total_quizzes = models.IntegerField(blank=True, null=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    average_score = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'user_stats'

