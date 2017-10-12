from django.db import models


# Create your models here.



class Master(models.Model):
    cityName = models.CharField(max_length=50)
    numTrunks= models.IntegerField()


class Cubes(models.Model):
    CubeName = models.CharField(max_length=50)
    idMaster = models.ForeignKey(Master)
    ip= models.GenericIPAddressField()
    usr= models.CharField(max_length=50)
    pwd= models.CharField(max_length=50)

class City(models.Model):
    CityName =  models.CharField(max_length=60)
    idMaster = models.ForeignKey(Master)
    ActualMaxConn = models.IntegerField()
    DialPeer = models.IntegerField()



