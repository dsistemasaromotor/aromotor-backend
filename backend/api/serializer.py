from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from useauth.models import  User, Perfil
from api import models as api_models
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["full_name"] = user.full_name
        token["email"] = user.email
        token["username"] = user.username
        token["cedula"] = user.cedula
        token["perfil"] = user.id_perfil_FK
        token["perfil"] = user.id_perfil_FK.id if user.id_perfil_FK else None

        # Agregar permisos del perfil al token
        if user.id_perfil_FK:
            perfil = user.id_perfil_FK
            token["permisos"] = {
                "can_view_cartera": perfil.can_view_cartera,
                "can_view_ajustes": perfil.can_view_ajustes,
                "can_view_usuarios": perfil.can_view_usuarios,
                "can_export_excel_cartera": perfil.can_export_excel_cartera,
                "can_export_all_cartera": perfil.can_export_all_cartera,
                "can_export_pdf_cartera": perfil.can_export_pdf_cartera,
            }
        else:
            # Si no hay perfil, permisos por defecto (todos False)
            token["permisos"] = {
                "can_view_cartera": False,
                "can_view_ajustes": False,
                "can_view_usuarios": False,
                "can_export_excel_cartera": False,
                "can_export_all_cartera": False,
                "can_export_pdf_cartera": False,
            }

        return token

#################################
###  Serializador de Usuario  ###
#################################

class UserSerializer(serializers.ModelSerializer):
    # Agregar campos de permisos del perfil
    can_view_cartera = serializers.SerializerMethodField()
    can_view_ajustes = serializers.SerializerMethodField()
    can_view_usuarios = serializers.SerializerMethodField()
    can_export_excel_cartera = serializers.SerializerMethodField()
    can_export_all_cartera = serializers.SerializerMethodField()
    can_export_pdf_cartera = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id','username', 'email', 'full_name', 'cedula', 
            'genero', 'fecha_nacimiento', 'telefono', 'id_perfil_FK',
            'can_view_cartera', 'can_view_ajustes', 'can_view_usuarios',
            'can_export_excel_cartera','can_export_all_cartera', 'can_export_pdf_cartera' 
        ]
    
    def get_can_view_cartera(self, obj):
        return obj.id_perfil_FK.can_view_cartera if obj.id_perfil_FK else False
    
    def get_can_view_ajustes(self, obj):
        return obj.id_perfil_FK.can_view_ajustes if obj.id_perfil_FK else False
    
    def get_can_view_usuarios(self, obj):
        return obj.id_perfil_FK.can_view_usuarios if obj.id_perfil_FK else False
    
    def get_can_export_excel_cartera(self, obj):
        return obj.id_perfil_FK.can_export_excel_cartera if obj.id_perfil_FK else False
    
    def get_can_export_all_cartera(self, obj):
        return obj.id_perfil_FK.can_export_all_cartera if obj.id_perfil_FK else False
    
    def get_can_export_pdf_cartera(self, obj):
        return obj.id_perfil_FK.can_export_pdf_cartera if obj.id_perfil_FK else False
    



class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'perfil', 'descripcion']  # Campos que quieres devolver

#############################################  
###  Serializador de Registro de Usuario  ###
#############################################  
 
class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    id_perfil_FK = serializers.PrimaryKeyRelatedField(queryset=Perfil.objects.all())
    
    class Meta:
        model = User
        fields = ['full_name', 'email', 'password', 'password2','cedula', 'genero','fecha_nacimiento','telefono' ,'id_perfil_FK']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2') 

        user = User(**validated_data)
        user.set_password(password) 
        user.save()

        return user
    

# Modificación: Nuevo serializer para crear usuario SIN contraseña (solo datos básicos)
class CrearUsuarioSinPasswordSerializer(serializers.ModelSerializer):
    id_perfil_FK = serializers.PrimaryKeyRelatedField(queryset=Perfil.objects.all())
    
    class Meta:
        model = User
        fields = ['full_name', 'email', 'cedula', 'genero', 'fecha_nacimiento', 'telefono', 'id_perfil_FK']
    
    def create(self, validated_data):
        # Crear usuario sin contraseña (password=None)
        user = User(**validated_data)
        user.set_unusable_password()  # Marca la contraseña como no usable inicialmente
        user.save()
        return user
    
# Nuevo serializer para set password (validar token y nueva contraseña)
class SetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Las contraseñas no coinciden."})
        return attrs
