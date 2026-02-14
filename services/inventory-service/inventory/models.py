from django.db import models

class Inventory(models.Model):
    product_id = models.IntegerField(unique=True)
    quantity = models.IntegerField(default=0)
    reserved_quantity = models.IntegerField(default=0)  # for pending orders
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Inventory for product {self.product_id}"
