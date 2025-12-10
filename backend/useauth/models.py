from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save


class Perfil(models.Model):
    perfil = models.CharField(max_length=250, blank=True, null=True)
    descripcion = models.CharField(max_length=250, blank=True, null=True)
    
    # Permisos básicos por módulo
    can_view_cartera = models.BooleanField(default=False, verbose_name="Puede ver Cartera")
    can_view_ajustes = models.BooleanField(default=False, verbose_name="Puede ver Ajustes")
    can_view_usuarios = models.BooleanField(default=False, verbose_name="Puede ver Usuarios")
    
    # Permisos específicos dentro de "Cartera"
    can_export_excel_cartera = models.BooleanField(default=False, verbose_name="Puede exportar Cartera a Excel")
    can_export_pdf_cartera = models.BooleanField(default=False, verbose_name="Puede exportar Cartera a PDF")
    
    def __str__(self):
        return self.perfil
    
    class Meta:
        db_table='perfil'
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

class User(AbstractUser):
    username = models.CharField(unique=True, max_length=100)
    email = models.EmailField(unique=True)
    full_name = models.CharField(unique=True, max_length=300)
    cedula = models.CharField(unique=True, max_length=10, blank=True, null=True)
    genero = models.CharField(max_length=10, choices=[('Masculino', 'Masculino'), ('Femenino', 'Femenino')])
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=10, blank=True, null=True)
    id_perfil_FK = models.ForeignKey(Perfil, on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.full_name
    
    class Meta:
        db_table='usuarios'
        verbose_name = 'Usuarios'
        verbose_name_plural = 'Usuarios'

    def save(self, *args, **kwargs):
        email_username, _ = self.email.split("@")
        if self.full_name == "" or self.full_name == None:
            self.full_name = email_username
        if self.username == "" or self.username == None:
            self.username = email_username

        super(User, self).save(*args, **kwargs)
        
            