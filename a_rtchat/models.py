from django.db import models
from django.contrib.auth.models import User 
import shortuuid

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    users_online = models.ManyToManyField(User, related_name='online_is_groups', blank=True)
    members = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self) -> str: 
        return self.group_name
    

class GroupMessage(models.Model):
    group = models.ForeignKey(to=ChatGroup, related_name='chat_message', on_delete=models.CASCADE)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.author.username} : {self.body}'
    
    class Meta:
        ordering = ['-created']
        