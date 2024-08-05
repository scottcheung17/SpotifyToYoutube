from django.db import models

class Users(models.Model):
    name = models.CharField(max_length=128, unique=True)

class Artists(models.Model):
    name = models.CharField(max_length=128, unique=True)

class Albums(models.Model):
    name = models.CharField(max_length=128, unique=True)
    artist = models.ForeignKey(Artists, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['name', 'artist']

class Playlists(models.Model):
    name = models.CharField(max_length=128)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['name', 'user']

class Tracks(models.Model):
    name = models.CharField(max_length=128)
    artist = models.ForeignKey(Artists, on_delete=models.CASCADE)
    album = models.ForeignKey(Albums, on_delete=models.CASCADE)
    duration = models.IntegerField()
    playlist = models.ManyToManyField(Playlists)

    class Meta:
        unique_together = ['name', 'album', 'duration', 'artist']