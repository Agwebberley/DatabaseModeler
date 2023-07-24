
from django.db import models
from django.urls import reverse
from django.utils import timezone


class accountsreceivable(models.Model):
    id = models.IntegerField(max_length=64, )
    amount = models.DecimalField(max_length=10, decimal_places=2, )
    due_date = models.DateField()
    paid = models.BooleanField()
    paid_date = models.DateField()
    amount_paid = models.DecimalField(max_length=10, decimal_places=2, )
    order_id = models.IntegerField(max_length=64, )
    AccountsReceivable_a_order_id_7254f55e_fk_Orders_or = models.ForeignKey('Orders_orders', on_delete=models.CASCADE, related_name='AccountsReceivable_a_order_id_7254f55e_fk_Orders_or')


class accountsreceivablehistory(models.Model):
    id = models.IntegerField(max_length=64, )
    field = models.CharField(max_length=100, )
    old_value = models.CharField(max_length=100, )
    new_value = models.CharField(max_length=100, )
    date = models.DateTimeField(max_length=6, )
    accounts_receivable_id = models.IntegerField(max_length=64, )
    AccountsReceivable_a_accounts_receivable__26029ab2_fk_AccountsR = models.ForeignKey('AccountsReceivable_accountsreceivable', on_delete=models.CASCADE, related_name='AccountsReceivable_a_accounts_receivable__26029ab2_fk_AccountsR')


class accountsreceivablepayment(models.Model):
    id = models.IntegerField(max_length=64, )
    amount = models.DecimalField(max_length=10, decimal_places=2, )
    date = models.DateField()
    accounts_receivable_id = models.IntegerField(max_length=64, )
    AccountsReceivable_a_accounts_receivable__d147c8b2_fk_AccountsR = models.ForeignKey('AccountsReceivable_accountsreceivable', on_delete=models.CASCADE, related_name='AccountsReceivable_a_accounts_receivable__d147c8b2_fk_AccountsR')


