from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator, EmailValidator
from multiselectfield import MultiSelectField
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta
class Proveedor(models.Model):
    TIPO_PROVEEDOR_CHOICES = [
        ('nacional', 'Nacional'),
        ('internacional', 'Internacional'),
    ]
    CATEGORIA_CHOICES = [
        ('motor', 'Motor'),
        ('arrastre', 'Arrastre'),
        ('transmision', 'Transmisión'),
        ('empaque', 'Empaque'),
        ('bateria', 'Batería'),
        ('bujia', 'Bujía'),
        ('jebe', 'Jebe'),
        ('suspension', 'Suspensión'),
        ('llantas', 'Llantas'),
        ('accesorios', 'Accesorios'),
        ('filtro', 'Filtro'),
        ('otros', 'Otros'),
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
    categorias = MultiSelectField(choices=CATEGORIA_CHOICES, default='otros')

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre_empresa']

    def __str__(self):
        return f"{self.nombre_empresa} ({self.get_tipo_proveedor_display()})"

class Producto(models.Model):
    CATEGORIA_CHOICES = [
        ('accesorios', 'Accesorios'),
        ('arrastre', 'Arrastre'),
        ('bateria', 'Batería'),
        ('bujia', 'Bujía'),
        ('empaque', 'Empaque'),
        ('filtro', 'Filtro'),
        ('jebe', 'Jebe'),
        ('motor', 'Motor'),
        ('suspension', 'Suspensión'),
        ('transmision', 'Transmisión'),
        ('llantas', 'Llantas'),
        ('otros', 'Otros'),
    ]
    imagen = models.ImageField(
        upload_to="productos/",  
        blank=True,              
        null=True
    )

    nombre_producto = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    proveedor = models.ForeignKey(
        'Proveedor', 
        on_delete=models.PROTECT,  
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default='otros'
    )

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0, "El precio no puede ser negativo.")]
    )
    precio_mayoreo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0, "El precio no puede ser negativo.")]
    )
    oferta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0, "El precio de oferta no puede ser negativo.")]
    )
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(1000000, "El stock no puede superar 1 millón.")]
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre_producto']

    def __str__(self):
        return f"{self.nombre_producto} - {self.proveedor.nombre_empresa}"
    

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

        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True")

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    nombre = models.CharField(max_length=150, blank=True, null=True)
    apellidos = models.CharField(max_length=150, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)  # 🔢 Código
    code_expires_at = models.DateTimeField(blank=True, null=True)
    resend_count = models.PositiveIntegerField(default=0)
    last_resend_time = models.DateTimeField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"   
    REQUIRED_FIELDS = []
    def set_verification_code(self, code):
        """Guarda el código y establece su expiración en 10 minutos"""
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

User = get_user_model()

class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="carrito"
    )
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carrito de {self.user.email}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )
    producto = models.ForeignKey(
        'Producto',
        on_delete=models.CASCADE
    )
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre_producto}"

    @property
    def subtotal(self):
        return self.cantidad * self.producto.precio_unitario

class Checkout(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="checkouts"
    )
    cart = models.OneToOneField( 
        "Cart",
        on_delete=models.CASCADE,
        related_name="checkout"
    )
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    ciudad = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    postal = models.CharField(max_length=20, blank=True, null=True)
    nota_adi = models.TextField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Checkout {self.id} - {self.user.email}"