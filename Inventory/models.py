
from django.db import models
from django.urls import reverse
from django.utils import timezone


class bin(models.Model):
    id = models.IntegerField(max_length=64, )
    name = models.CharField(max_length=100, )
    location_id = models.IntegerField(max_length=64, )
    Inventory_bin_location_id_1ddfd1cf_fk_Inventory_location_id = models.ForeignKey('Inventory_location', on_delete=models.CASCADE, related_name='Inventory_bin_location_id_1ddfd1cf_fk_Inventory_location_id')


class bin_items(models.Model):
    id = models.IntegerField(max_length=64, )
    bin_id = models.IntegerField(max_length=64, )
    items_id = models.IntegerField(max_length=64, )
    Inventory_bin_items_bin_id_ffef0ad8_fk_Inventory_bin_id = models.ForeignKey('Inventory_bin', on_delete=models.CASCADE, related_name='Inventory_bin_items_bin_id_ffef0ad8_fk_Inventory_bin_id')
    Inventory_bin_items_items_id_92ca6290_fk_Items_items_id = models.ForeignKey('Items_items', on_delete=models.CASCADE, related_name='Inventory_bin_items_items_id_92ca6290_fk_Items_items_id')


class inventory(models.Model):
    id = models.IntegerField(max_length=64, )
    quantity = models.IntegerField(max_length=32, )
    last_updated = models.DateTimeField(max_length=6, )
    typeI = models.CharField(max_length=10, )
    item_id = models.IntegerField(max_length=64, )
    Inventory_inventory_item_id_7b7c9e4a_fk_Items_items_id = models.ForeignKey('Items_items', on_delete=models.CASCADE, related_name='Inventory_inventory_item_id_7b7c9e4a_fk_Items_items_id')


class inventoryhistory(models.Model):
    id = models.IntegerField(max_length=64, )
    quantity = models.IntegerField(max_length=32, )
    change = models.IntegerField(max_length=32, )
    typeI = models.CharField(max_length=10, )
    timestamp = models.DateTimeField(max_length=6, )
    inventory_id = models.IntegerField(max_length=64, )
    item_id = models.IntegerField(max_length=64, )
    Inventory_inventoryh_inventory_id_73a70a49_fk_Inventory = models.ForeignKey('Inventory_inventory', on_delete=models.CASCADE, related_name='Inventory_inventoryh_inventory_id_73a70a49_fk_Inventory')
    Inventory_inventoryhistory_item_id_2785e3cf_fk_Items_items_id = models.ForeignKey('Items_items', on_delete=models.CASCADE, related_name='Inventory_inventoryhistory_item_id_2785e3cf_fk_Items_items_id')


class location(models.Model):
    id = models.IntegerField(max_length=64, )
    name = models.CharField(max_length=100, )
    amount_of_bins = models.IntegerField(max_length=32, )


class pick(models.Model):
    id = models.IntegerField(max_length=64, )
    is_complete = models.BooleanField()
    location_id = models.IntegerField(max_length=64, )
    order_id = models.IntegerField(max_length=64, )
    Inventory_pick_location_id_e5a85fa0_fk_Inventory_location_id = models.ForeignKey('Inventory_location', on_delete=models.CASCADE, related_name='Inventory_pick_location_id_e5a85fa0_fk_Inventory_location_id')
    Inventory_pick_order_id_9b509292_fk_Orders_orders_id = models.ForeignKey('Orders_orders', on_delete=models.CASCADE, related_name='Inventory_pick_order_id_9b509292_fk_Orders_orders_id')


class pick_items(models.Model):
    id = models.IntegerField(max_length=64, )
    pick_id = models.IntegerField(max_length=64, )
    orderitem_id = models.IntegerField(max_length=64, )
    Inventory_pick_items_orderitem_id_443416dd_fk_Orders_or = models.ForeignKey('Orders_orderitem', on_delete=models.CASCADE, related_name='Inventory_pick_items_orderitem_id_443416dd_fk_Orders_or')
    Inventory_pick_items_pick_id_1a71d8fb_fk_Inventory_pick_id = models.ForeignKey('Inventory_pick', on_delete=models.CASCADE, related_name='Inventory_pick_items_pick_id_1a71d8fb_fk_Inventory_pick_id')


