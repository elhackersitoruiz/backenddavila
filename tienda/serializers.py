from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import (
    Proveedor,
    Producto,
    CustomUser,
    Cart,
    CartItem,
    Categoria,
    Marca,
    PendingUser,Order, OrderItem,Wishlist, Producto,Cart, CartItem, Producto
)
from django.core.exceptions import ValidationError
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

class PendingUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = PendingUser
        fields = ["email", "nombre", "apellidos", "password", "password2"]

class ProveedorSerializer(serializers.ModelSerializer):
    marcas_list = serializers.SerializerMethodField()
    categorias_list = serializers.SerializerMethodField()

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
            'marcas',
            'categorias',
            'marcas_list',
            'categorias_list',
            'fecha_registro',
        ]
        read_only_fields = ['id', 'fecha_registro', 'marcas_list', 'categorias_list']

    def get_marcas_list(self, obj):
        return obj.get_marcas_list()

    def get_categorias_list(self, obj):
        return obj.get_categorias_list()

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'slug']
        read_only_fields = ['id', 'slug']
class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'slug']
        read_only_fields = ['id', 'slug']


class ProductoSerializer(serializers.ModelSerializer):
    proveedor_detalle = serializers.SerializerMethodField()
    proveedor_marcas = serializers.SerializerMethodField()
    proveedor_categorias = serializers.SerializerMethodField()
    imagen = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'codigo',
            'imagen',
            'nombre_producto',
            'descripcion',
            'proveedor',
            'proveedor_detalle',
            'marca',
            'categoria',
            'procedencia',
            'stock',
            'fecha_registro',
            'es_nuevo',
            'fecha_novedad',
            'es_destacado',
            'slug',
            'precio_unitario',
            'precio_mayoreo',
            'proveedor_marcas',
            'proveedor_categorias',
        ]
        read_only_fields = [
            'id',
            'slug',
            'proveedor_detalle',
            'proveedor_marcas',
            'proveedor_categorias',
        ]
        extra_kwargs = {
            'imagen': {'required': False, 'allow_null': True},
        }

    def get_proveedor_detalle(self, obj):
        if obj.proveedor:
            return {
                "id": obj.proveedor.id,
                "nombre_empresa": obj.proveedor.nombre_empresa
            }
        return None
    def get_proveedor_marcas(self, obj):
        if obj.proveedor:
            return obj.proveedor.get_marcas_list()
        return []

    def get_proveedor_categorias(self, obj):
        if obj.proveedor:
            return obj.proveedor.get_categorias_list()
        return []
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user if request else None
        data["isNew"] = instance.es_reciente()

        if instance.imagen and request:
            data["imagen"] = instance.imagen.url

        if user and user.is_authenticated:
            if user.is_staff or user.is_superuser:
                pass
            elif getattr(user, "puede_ver_precios_mayoreo", False):
                data.pop("precio_unitario", None)
            else:
                data.pop("precio_mayoreo", None)
        else:
            data.pop("precio_mayoreo", None)

        return data

class CartItemSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True) 
    subtotal = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ["id", "producto", "cantidad", "subtotal"]

    def get_subtotal(self, obj):
        user = self.context.get("request").user
        if getattr(user, "puede_ver_precios_mayoreo", False) and obj.producto.precio_mayoreo:
            return obj.cantidad * obj.producto.precio_mayoreo
        elif getattr(user, "puede_ver_precios", False) or not user.is_authenticated:
            return obj.cantidad * obj.producto.precio_unitario
        return None  

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "usuario", "creado", "items", "total"]
        read_only_fields = ["usuario", "creado"]

    def get_total(self, obj):
        user = self.context.get("request").user
        if getattr(user, "puede_ver_precios_mayoreo", False):
            total = sum(
                item.cantidad * (item.producto.precio_mayoreo or item.producto.precio_unitario)
                for item in obj.items.all()
            )
            return total
        elif getattr(user, "puede_ver_precios", False) or not user.is_authenticated:
            total = sum(item.cantidad * item.producto.precio_unitario for item in obj.items.all())
            return total
        return None

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "nombre",
            "apellidos",
            "direccion",
            "is_active",
            "is_staff",
            "puede_ver_precios",
            "puede_ver_precios_mayoreo",
        ]
        read_only_fields = ["is_staff", "is_active"]
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
        if not self.user.is_verified:
            raise serializers.ValidationError({"detail": "Tu correo no ha sido verificado. Revisa tu bandeja de entrada."})

        data.update({
            "id": self.user.id,
            "email": self.user.email,
            "nombre": self.user.nombre,
            "apellidos": self.user.apellidos,
        })
        return data
class WishlistProductoSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'codigo',
            'imagen',
            'nombre_producto',
            'procedencia',
            'stock',
            'precio_unitario',
            'precio_mayoreo',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = request.user if request else None
        if instance.imagen and request:
            data["imagen"] = request.build_absolute_uri(instance.imagen.url)

        if user and user.is_authenticated:
            if user.is_staff or user.is_superuser:
                pass  
            elif getattr(user, "puede_ver_precios_mayoreo", False):
                data.pop("precio_unitario", None)
            else:
                data.pop("precio_mayoreo", None)
        else:
            data.pop("precio_mayoreo", None)

        return data


class WishlistSerializer(serializers.ModelSerializer):
    producto = WishlistProductoSerializer(read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source='producto',
        write_only=True
    )
    class Meta:
        model = Wishlist
        fields = ['id', 'producto', 'producto_id', 'fecha_agregado']
        read_only_fields = ['id', 'producto', 'fecha_agregado']

    def create(self, validated_data):
        user = self.context['request'].user
        producto = validated_data['producto']
        wishlist_item, created = Wishlist.objects.get_or_create(usuario=user, producto=producto)
        return wishlist_item

class OrderItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre_producto", read_only=True)
    producto_imagen = serializers.ImageField(source="producto.imagen", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "producto", "producto_nombre", "producto_imagen", "cantidad", "price", "subtotal"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    nombre = serializers.CharField(source="user.nombre", read_only=True)
    apellidos = serializers.CharField(source="user.apellidos", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    code = serializers.CharField(read_only=True)
    cart_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "code",           
            "nombre",
            "apellidos",
            "email",
            "dni",
            "phone",
            "address",
            "city",
            "state",
            "country",
            "notes",
            "subtotal",
            "shipping",
            "total",
            "status",
            "cart_id",
            "items",
            "created_at",
        ]
        read_only_fields = ["subtotal", "total", "status", "created_at","code"]
    def validate_cart_id(self, value):
        user = self.context["request"].user
        try:
            cart = Cart.objects.get(id=value, usuario=user, activo=True)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("El carrito no existe o ya fue procesado.")
        if not cart.items.exists():
            raise serializers.ValidationError("El carrito está vacío.")
        return value
    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        cart_id = validated_data.pop("cart_id")

        try:
            cart = Cart.objects.get(id=cart_id, usuario=user, activo=True)
        except Cart.DoesNotExist:
            raise ValidationError("El carrito no existe o ya fue procesado.")
        validated_data.pop("user", None)
        validated_data.pop("cart", None)
        order = Order.objects.create(user=user, cart=cart, **validated_data)
        order.create_items_from_cart(cart)

        return order
