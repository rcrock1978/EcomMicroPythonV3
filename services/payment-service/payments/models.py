from django.db import models

class Payment(models.Model):
    order_id = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)  # e.g., credit_card, paypal
    status = models.CharField(max_length=50, default='pending')  # pending, completed, failed
    transaction_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
