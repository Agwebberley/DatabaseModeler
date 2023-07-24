
from django.db import models
from django.urls import reverse
from django.utils import timezone


class orderitem(models.Model):
    id = models.IntegerField(max_length=64, )
    quantity = models.IntegerField(max_length=32, )
    item_id = models.IntegerField(max_length=64, )
    order_id = models.IntegerField(max_length=64, )
    Orders_orderitem_item_id_ac00d823_fk_Items_items_id = models.ForeignKey('Items_items', on_delete=models.CASCADE, related_name='Orders_orderitem_item_id_ac00d823_fk_Items_items_id')
    Orders_orderitem_order_id_3570cd78_fk_Orders_orders_id = models.ForeignKey('Orders_orders', on_delete=models.CASCADE, related_name='Orders_orderitem_order_id_3570cd78_fk_Orders_orders_id')


class orders(models.Model):
    id = models.IntegerField(max_length=64, )
    ordered_date = models.DateTimeField(max_length=6, )
    updated_date = models.DateTimeField(max_length=6, )
    customer_id = models.IntegerField(max_length=64, )
    Orders_orders_customer_id_dea32023_fk_Customers_customers_id = models.ForeignKey('Customers_customers', on_delete=models.CASCADE, related_name='Orders_orders_customer_id_dea32023_fk_Customers_customers_id')


