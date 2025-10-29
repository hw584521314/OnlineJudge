

from django.db import models
from account.models import User


class TypingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #正确率
    accuracy = models.FloatField(default=0.0)
    #练习时间
    practice_munites = models.IntegerField(default=0)
    #每分钟击键数
    tpm = models.IntegerField(default=0)
    #总的击键数
    total_hit = models.IntegerField(default=0)
    #错误的击键数
    error_hit = models.IntegerField(default=0)
    #提交时间
    create_time = models.DateTimeField(auto_now_add=True)
    