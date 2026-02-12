
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator, EmailValidator
from django.db import models
from django.db.models import Sum, F
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from decimal import Decimal
from django.db import models
import random, string
from django.db.models.signals import post_delete
from django.dispatch import receiver
from storages.backends.s3boto3 import S3Boto3Storage

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    TIPO_PROVEEDOR_CHOICES = [
        ('nacional', 'Nacional'),
        ('internacional', 'Internacional'),
    ]

    nombre_empresa = models.CharField(max_length=200, unique=True)
    nombre_contacto = models.CharField(max_length=150)
    telefono = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Ingrese un número de teléfono válido.')]
    )
    correo = models.EmailField(unique=True, validators=[EmailValidator(message="Ingrese un correo válido.")])
    direccion = models.TextField()
    ruc_documento = models.CharField(
        "RUC / Documento Legal",
        max_length=50,
        unique=True,
        validators=[RegexValidator(r'^[0-9A-Za-z\-]+$', 'Ingrese un documento válido (solo letras, números y guiones).')]
    )
    tipo_proveedor = models.CharField(
        max_length=20,
        choices=TIPO_PROVEEDOR_CHOICES,
        default='nacional'
    )
    marcas = models.TextField(
        blank=True,
        help_text="Ingrese las marcas separadas por comas. Ej: Marca1, Marca2, Marca3"
    )
    categorias = models.TextField(
        blank=True,
        help_text="Ingrese las categorías separadas por comas. Ej: Categoria1, Categoria2"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre_empresa']

    def __str__(self):
        return f"{self.nombre_empresa} ({self.get_tipo_proveedor_display()})"

    def get_marcas_list(self):
        return [m.strip() for m in self.marcas.split(',') if m.strip()]

    def get_categorias_list(self):
        return [c.strip() for c in self.categorias.split(',') if c.strip()]

media_storage = S3Boto3Storage(location=settings.AWS_LOCATION)


class Producto(models.Model):
    codigo = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código único del producto."
    )
    imagen = models.ImageField(storage=media_storage, blank=True, null=True)

    nombre_producto = models.CharField(
        max_length=200,
        unique=False
    )
    descripcion = models.TextField(
        blank=True,
        null=True
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='productos'
    )
    marca = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)
    procedencia = models.CharField(max_length=150, blank=True, null=True)
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    precio_mayoreo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(1000000)]
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    es_nuevo = models.BooleanField(default=False, help_text="Marcar si el producto es nuevo.")
    fecha_novedad = models.DateTimeField(blank=True, null=True, help_text="Fecha en que se marcó como nuevo.")
    es_destacado = models.BooleanField(default=False, help_text="Marcar si el producto es destacado.")
    
    slug = models.SlugField(unique=True, blank=True, editable=False)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_registro']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.nombre_producto}-{self.codigo}")
            unique_slug = base_slug
            num = 1
            while Producto.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        if self.es_nuevo and not self.fecha_novedad:
            self.fecha_novedad = timezone.now()

        super().save(*args, **kwargs)

    def es_reciente(self):
        """Retorna True si el producto tiene menos de 30 días desde su novedad o creación."""
        limite = timedelta(days=7)
        if self.fecha_novedad:
            return timezone.now() - self.fecha_novedad <= limite
        return timezone.now() - self.fecha_registro <= limite

    def __str__(self):
        return f"{self.nombre_producto} - {self.proveedor.nombre_empresa}"


@receiver(post_delete, sender=Producto)
def eliminar_imagen_producto(sender, instance, **kwargs):
    """Elimina el archivo de imagen del sistema cuando se borra el producto."""
    if instance.imagen:
        instance.imagen.delete(save=False)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("El superusuario debe tener is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    nombre = models.CharField(max_length=150, blank=True, null=True)
    apellidos = models.CharField(max_length=150, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_expires_at = models.DateTimeField(blank=True, null=True)
    resend_count = models.PositiveIntegerField(default=0)
    last_resend_time = models.DateTimeField(blank=True, null=True)
    puede_ver_precios = models.BooleanField(default=False, help_text="Permite ver el precio unitario de los productos.")
    puede_ver_precios_mayoreo = models.BooleanField(default=False, help_text="Permite ver el precio por mayoreo de los productos.")
    failed_login_attempts = models.IntegerField(default=0)
    blocked_until = models.DateTimeField(blank=True, null=True)
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def set_verification_code(self, code):
        self.verification_code = code
        self.code_expires_at = timezone.now() + timedelta(minutes=10)
        self.save()

    def is_code_valid(self, code):
        if self.verification_code != code:
            return False
        if self.code_expires_at and timezone.now() > self.code_expires_at:
            return False
        return True

    def __str__(self):
        return self.email

class PendingUser(models.Model):
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    password = models.CharField(max_length=128)
    password2 = models.CharField(max_length=128)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_expires_at = models.DateTimeField(blank=True, null=True)
    resend_count = models.PositiveIntegerField(default=0)
    last_resend_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
class Cart(models.Model):
    usuario = models.ForeignKey("tienda.CustomUser", on_delete=models.CASCADE)
    creado = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True) 

    def __str__(self):
        return f"Carrito de {self.usuario.email}"
    def add_producto(self, producto, cantidad=1):
        item, created = self.items.get_or_create(producto=producto)
        if not created:
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad
        item.save()
        return item
    def update_cantidad(self, producto, cantidad):
        item = self.items.filter(producto=producto).first()
        if item:
            if cantidad <= 0:
                item.delete()
            else:
                item.cantidad = cantidad
                item.save()
    def remove_producto(self, producto):
        self.items.filter(producto=producto).delete()
    @property
    def total(self):
        user = getattr(self, "usuario", None)
        if not user:
            return None
        if getattr(user, "puede_ver_precios_mayoreo", False):
            total = sum(
                item.cantidad * (item.producto.precio_mayoreo or item.producto.precio_unitario)
                for item in self.items.all()
            )
            return total
        elif getattr(user, "puede_ver_precios", False):
            total = sum(item.cantidad * item.producto.precio_unitario for item in self.items.all())
            return total
        return None


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey("Producto", on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "producto") 

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre_producto}"

    @property
    def subtotal(self):
        return self.cantidad * Decimal(self.producto.precio_unitario)


def generate_unique_order_code():
    """Genera un código aleatorio único para la orden"""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Order.objects.filter(code=code).exists():
            return code

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ("accepted", "Aceptado"), 
        ("rejected", "Rechazado"),
        ('processing', 'En proceso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    code = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
        default=generate_unique_order_code
    )

    user = models.ForeignKey("tienda.CustomUser", on_delete=models.CASCADE)
    dni = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Perú")
    notes = models.TextField(blank=True, null=True)
    cart = models.ForeignKey(
        'Cart',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pedido {self.code} - {self.user.email if hasattr(self.user, 'email') else self.user}"

    def create_items_from_cart(self, cart):
        """
        Crea los OrderItems basándose en los productos del carrito.
        🔹 Ya no descuenta stock del producto.
        🔹 Solo valida que el stock sea suficiente.
        """
        if not cart:
            raise ValidationError("No se puede crear una orden sin un carrito.")

        subtotal_total = Decimal("0.00")

        for item in cart.items.all():
            producto = item.producto
            cantidad = item.cantidad

            if producto.stock < cantidad:
                raise ValidationError(f"Stock insuficiente para {producto.nombre_producto}.")

            if getattr(self.user, "puede_ver_precios_mayoreo", False) and producto.precio_mayoreo:
                price = producto.precio_mayoreo
            else:
                price = producto.precio_unitario

            subtotal = cantidad * price

            OrderItem.objects.create(
                order=self,
                producto=producto,
                cantidad=cantidad,
                price=price,
                subtotal=subtotal,
            )

            subtotal_total += subtotal

        self.subtotal = subtotal_total
        self.total = subtotal_total + Decimal(self.shipping or 0)
        self.save()

        cart.activo = False
        cart.save()

        return self

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.SET_NULL,
        null=True
    )
    cantidad = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.price
        super().save(*args, **kwargs)

    def __str__(self):
        producto_nombre = self.producto.nombre_producto if self.producto else "Producto eliminado"
        return f"{self.cantidad} x {producto_nombre}"

class Wishlist(models.Model):
    usuario = models.ForeignKey(
        "CustomUser",
        on_delete=models.CASCADE,
        related_name="wishlist",
        verbose_name="Usuario"
    )
    producto = models.ForeignKey(
        "Producto",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name="Producto"
    )
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "producto")
        verbose_name = "Lista de deseos"
        verbose_name_plural = "Listas de deseos"
        ordering = ['-fecha_agregado']

    def __str__(self):
        return f"{self.usuario.email} ❤️ {self.producto.nombre_producto}"
