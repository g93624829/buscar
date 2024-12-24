from django.db import models

# Create your models here.
class Datos(models.Model):
    dni = models.CharField(max_length=8, verbose_name="Número")
    nombres_completos = models.CharField(max_length=300, verbose_name="Nombres Completos")

    class Meta:
        verbose_name = "Dato"
        verbose_name_plural = "Datos"

    def __str__(self):
        return f"{self.numero} - {self.nombres_completos}"
