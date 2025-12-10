from django.contrib import admin
from useauth.models import User, Perfil

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name','date']

admin.site.register(User)
admin.site.register(Perfil)