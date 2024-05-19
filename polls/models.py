from django.db import models
from django.contrib.auth.models import User
from users.models import User as TgUser
from utils.models import CreateUpdateTracker


class Poll(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Question(models.Model):
    poll = models.ForeignKey(Poll, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=50, choices=[('button', 'Button'), ('text', 'Text')])


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)


class Answer(models.Model):
    tg_user = models.ForeignKey(TgUser, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, null=True, blank=True, on_delete=models.SET_NULL)
    response = models.TextField(null=True, blank=True)
    # Eather choice or response will be set and another be null, not both at the same time


class Thread(models.Model):
    tg_user = models.ForeignKey(TgUser, related_name='threads', on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, related_name='threads', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    thread = models.ForeignKey(Thread, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    sent_by_bot = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
