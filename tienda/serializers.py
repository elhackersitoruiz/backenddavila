from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Proveedor, Producto, CustomUser, Cart, CartItem, Checkout

class CartItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre_producto", read_only=True)
    precio_unitario = serializers.DecimalField(source="producto.precio_unitario", max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ["id", "producto", "producto_nombre", "cantidad", "precio_unitario", "subtotal"]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ["id", "user", "creado", "items", "total"]
        read_only_fields = ["user", "creado"]

class CheckoutSerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)

    class Meta:
        model = Checkout
        fields = [
            "id",
            "user",
            "cart",
            "direccion",
            "telefono",
            "ciudad",
            "departamento",
            "postal",
            "nota_adi",
            "creado",
        ]
        read_only_fields = ["user", "creado"]

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["nombre"] = user.nombre
        token["apellidos"] = user.apellidos
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # 🔒 Bloquear si no está verificado
        if not self.user.is_verified:
            raise serializers.ValidationError({"detail": "Tu correo no ha sido verificado. Revisa tu bandeja de entrada."})

        data.update({
            "id": self.user.id,
            "email": self.user.email,
            "nombre": self.user.nombre,
            "apellidos": self.user.apellidos,
        })
        return data

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "nombre",
            "apellidos",
            "password",
            "password2",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            nombre=validated_data.get("nombre", ""),
            apellidos=validated_data.get("apellidos", ""),
            password=validated_data["password"],
        )
        return user
    
from rest_framework import serializers
from .models import PendingUser

class PendingUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)


    class Meta:
        model = PendingUser
        fields = ["email", "nombre", "apellidos", "password", "password2"]

    
class ProveedorSerializer(serializers.ModelSerializer):
    categorias = serializers.SerializerMethodField()
    categorias_input = serializers.ListField(
        child=serializers.ChoiceField(choices=Proveedor.CATEGORIA_CHOICES),
        write_only=True
    )

    class Meta:
        model = Proveedor
        fields = [
            'id',
            'nombre_empresa',
            'nombre_contacto',
            'telefono',
            'correo',
            'direccion',
            'ruc_documento',
            'tipo_proveedor',
            'categorias',      
            'categorias_input', 
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro', 'categorias']

    def get_categorias(self, obj):
        if not obj.categorias:
            return []
        if isinstance(obj.categorias, list):
            return obj.categorias
        
        return obj.categorias.split(',')

    def create(self, validated_data):
        categorias = validated_data.pop('categorias_input', [])
        validated_data['categorias'] = ','.join(categorias)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        categorias = validated_data.pop('categorias_input', None)
        if categorias is not None:
            instance.categorias = ','.join(categorias)
        return super().update(instance, validated_data)
    
class ProductoSerializer(serializers.ModelSerializer):
    proveedor_detalle = ProveedorSerializer(source='proveedor', read_only=True)
    imagen = serializers.ImageField(use_url=True, required=False)  # 🔹 Aquí agregamos la imagen

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre_producto',
            'descripcion',
            'proveedor',
            'proveedor_detalle',
            'categoria',
            'precio_unitario',
            'precio_mayoreo',
            'oferta',
            'stock',
            'fecha_registro',
            'imagen',  
        ]
        read_only_fields = ['id', 'fecha_registro']

    def validate(self, data):
        if data.get('precio_mayoreo') and data['precio_mayoreo'] > data['precio_unitario']:
            raise serializers.ValidationError(
                {"precio_mayoreo": "El precio por mayoreo no puede ser mayor que el precio unitario."}
            )
        return data

