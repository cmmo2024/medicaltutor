from django.db import models
from django.contrib.auth.models import User  

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    stats = models.OneToOneField('UserStats', on_delete=models.CASCADE, related_name="profile", null=True)
    plan = models.ForeignKey('Plan', on_delete=models.DO_NOTHING, null=True, blank=True)
    remaining_queries = models.IntegerField(default=0)
    remaining_quizzes = models.IntegerField(default=0)
    last_subject = models.CharField(max_length=100, null=True, blank=True)
    last_topic = models.CharField(max_length=100, null=True, blank=True)
    last_chat_content = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.plan_name if self.plan else 'Free Plan'}"

    @property
    def has_paid_plan(self):
        return self.remaining_queries > 0 or self.remaining_quizzes > 0

    def update_plan(self, new_plan):
        """Update user's plan and add the new limits to existing ones"""
        if self.plan:
            # Add new limits to existing ones
            self.remaining_queries += new_plan.max_queries
            self.remaining_quizzes += new_plan.max_quizzes
        else:
            # Set new limits
            self.remaining_queries = new_plan.max_queries
            self.remaining_quizzes = new_plan.max_quizzes
        
        self.plan = new_plan
        self.save()

    def decrement_queries(self):
        """Decrement remaining queries"""
        if self.remaining_queries > 0:
            self.remaining_queries -= 1
            self.save()
            return True
        return False

    def decrement_quizzes(self):
        """Decrement remaining quizzes and check if plan should be reset"""
        if self.remaining_quizzes > 0:
            self.remaining_quizzes -= 1
            # Only reset plan if both counters are 0
            if self.remaining_quizzes == 0 and self.remaining_queries == 0:
                self.plan = None
            self.save()
            return True
        return False

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    transaction_id = models.TextField()  
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    amount = models.FloatField()
    payment_date = models.DateTimeField(blank=True, null=True)
    receiver_id_card = models.CharField(max_length=255, null=False)

    class Meta:
        managed = True
        db_table = 'payments'
        
    def save(self, *args, **kwargs):
        # Get the receiver_id_card from the plan
        if hasattr(self, 'plan'):
            self.receiver_id_card = self.plan.receiver_id_card
        super().save(*args, **kwargs)
        
        
class Voucher(models.Model):
    voucher_id = models.AutoField(primary_key=True)
    transaction_id = models.TextField(unique=True)  # Make transaction_id unique
    card_id = models.CharField(max_length=255, null=False)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)  # Add used field to track usage

    class Meta:
        managed = True
        db_table = 'vouchers'

    def __str__(self):
        return f"Voucher {self.voucher_id} - {self.amount}"

    def mark_as_used(self):
        """Mark the voucher as used"""
        self.used = True
        self.save()


class Plan(models.Model):
    plan_id = models.AutoField(primary_key=True)
    plan_name = models.TextField()
    receiver_id_card = models.CharField(max_length=255, null=False)
    qr_code = models.ImageField(upload_to='payment_qr/', default='payment_qr/payment-qr.jpg')
    phone_number = models.CharField(max_length=20, unique=True, null=False)
    price = models.FloatField()
    max_queries = models.IntegerField(blank=True, null=True)
    max_quizzes = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'plans'
        
    def __str__(self):
        return self.plan_name


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
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING, primary_key=True)
    total_quizzes = models.IntegerField(blank=True, null=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    average_score = models.FloatField(blank=True, null=True)
    subject_averages = models.JSONField(default=dict, blank=True)  # Store subject averages as JSON

    class Meta:
        managed = True
        db_table = 'user_stats'

    def update_subject_averages(self):
        from django.db.models import Avg
        # Calculate averages for each subject
        subject_avgs = (Quizzes.objects
                       .filter(user=self.user)
                       .values('matter')
                       .annotate(avg_score=Avg('score')))
        
        # Convert to dictionary format
        self.subject_averages = {
            item['matter']: float(item['avg_score'])
            for item in subject_avgs
        }
        self.save()