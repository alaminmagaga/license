from django.db import models

class LicensePlate(models.Model):
    plate_number = models.CharField(max_length=10, unique=True)
    image = models.ImageField(upload_to='license_plates/')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.plate_number


class Driver(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    license_plate = models.ForeignKey(LicensePlate, on_delete=models.CASCADE)
    license_expiring_status = models.CharField(max_length=20)
    address = models.CharField(max_length=200)

    def __str__(self):
        return self.name
