from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} in {self.room.name}: {self.content}'

class PrivateRoom(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user1_rooms')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user2_rooms')
    room_slug = models.SlugField(unique=True)

    def generate_room_slug(self):
        usernames = sorted([self.user1.username, self.user2.username])
        return f"{usernames[0]}_{usernames[1]}"
    
    def save(self, *args, **kwargs):
        if not self.room_slug:
            self.room_slug = self.generate_room_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user1.username} - {self.user2.username}"

class PrivateChatMessage(models.Model):
    room = models.ForeignKey(PrivateRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

