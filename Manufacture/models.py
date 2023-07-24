
from django.db import models
from django.urls import reverse
from django.utils import timezone


class manufacture(models.Model):
    id = models.IntegerField(max_length=64, )
    quantity = models.IntegerField(max_length=32, )
    date = models.DateField()
    item_id = models.IntegerField(max_length=64, )
    Manufacture_manufacture_item_id_837185b2_fk_Items_items_id = models.ForeignKey('Items_items', on_delete=models.CASCADE, related_name='Manufacture_manufacture_item_id_837185b2_fk_Items_items_id')
    fk_Manufacture_manufacture_Manufacture_manufacturehistory_1 = models.ForeignKey('Manufacture_manufacturehistory', on_delete=models.CASCADE, related_name='fk_Manufacture_manufacture_Manufacture_manufacturehistory_1')


class manufacturehistory(models.Model):
    id = models.IntegerField(max_length=64, )
    manufacture = models.IntegerField(max_length=32, )
    item = models.IntegerField(max_length=32, )
    quantity = models.IntegerField(max_length=32, )
    timestamp = models.DateTimeField(max_length=6, )
    is_complete = models.BooleanField()


