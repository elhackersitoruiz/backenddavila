from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, filters, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
import random
from .models import (
    Proveedor,
    Producto,
    CustomUser,
    Cart,
    PendingUser,
    Marca,
    Categoria,
    Order,
    Wishlist,
    OrderItem
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from .serializers import (
    ProveedorSerializer,
    ProductoSerializer,
    UserRegisterSerializer,
    CartSerializer,
    CustomUserSerializer,
    MarcaSerializer,
    CategoriaSerializer,
    OrderSerializer,
    WishlistSerializer
)
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
User = get_user_model()
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
token_generator = PasswordResetTokenGenerator()
from urllib.parse import urlencode
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            nombre = serializer.validated_data.get("nombre", "")
            apellidos = serializer.validated_data.get("apellidos", "")
            password = serializer.validated_data["password"]
            password2 = serializer.validated_data["password2"]

            if CustomUser.objects.filter(email=email).exists():
                return Response({"error": "El correo ya está registrado."}, status=status.HTTP_400_BAD_REQUEST)

            pending, created = PendingUser.objects.get_or_create(
                email=email,
                defaults={
                    "nombre": nombre,
                    "apellidos": apellidos,
                    "password": password,
                    "password2": password2  
                }
            )

            codigo = enviar_codigo_verificacion(email)
            pending.verification_code = codigo
            pending.code_expires_at = timezone.now() + timedelta(minutes=10)
            pending.resend_count = 0
            pending.last_resend_time = None
            pending.save()

            return Response({
                "message": "Se ha enviado un código de verificación a tu correo.",
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        codigo = request.data.get("code")

        if not email or not codigo:
            return Response(
                {"error": "El correo y el código son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pending = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response(
                {"error": "No existe un usuario con ese correo."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not pending.verification_code:
            return Response(
                {"error": "No se ha enviado un código de verificación."},
                status=status.HTTP_400_BAD_REQUEST
            )
        codigo_db = pending.verification_code.strip()
        codigo_input = str(codigo).strip()

        if pending.code_expires_at and timezone.now() > pending.code_expires_at:
            return Response(
                {"error": "El código ha expirado. Solicita uno nuevo."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if str(pending.verification_code).strip() != str(codigo).strip():
            return Response(
                {"error": "El código ingresado no es correcto."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = CustomUser.objects.create_user(
            email=pending.email,
            password=pending.password,
            nombre=pending.nombre,
            apellidos=pending.apellidos
        )
        pending.delete()
        return Response({"message": "Cuenta verificada y creada correctamente."}, status=status.HTTP_200_OK)
def enviar_codigo_verificacion(email):
    """
    Envía un código de verificación ultra animado, con iconos flotando alrededor de la tarjeta,
    colores neutros con acento rojo y logo embebido.
    """
    try:
        pending_user = PendingUser.objects.get(email=email)
    except PendingUser.DoesNotExist:
        return None

    codigo = str(random.randint(100000, 999999))
    pending_user.verification_code = codigo
    pending_user.code_expires_at = timezone.now() + timedelta(minutes=10)
    pending_user.save()


    html_message = f"""
    <div style="font-family:'Arial',sans-serif; text-align:center; background:#f5f5f5; padding:50px;">
        <div style="position:relative; max-width:600px; margin:auto; background:#ffffff; border-radius:20px; overflow:hidden; box-shadow:0 20px 50px rgba(0,0,0,0.15); padding:50px 20px;">

            <!-- Iconos flotantes -->
            <span style="position:absolute; top:-10px; left:10%; font-size:24px; animation:floatA 6s ease-in-out infinite;">🔧</span>
            <span style="position:absolute; top:20%; right:-10px; font-size:28px; animation:floatB 7s ease-in-out infinite;">🛵</span>
            <span style="position:absolute; bottom:-10px; left:25%; font-size:24px; animation:floatC 5s ease-in-out infinite;">🛠️</span>
            <span style="position:absolute; bottom:15%; right:15%; font-size:22px; animation:floatD 8s ease-in-out infinite;">⚙️</span>
            <span style="position:absolute; top:50%; left:-10px; font-size:26px; animation:floatE 6s ease-in-out infinite;">🔩</span>

            <h2 style="font-size:28px; margin-bottom:20px; color:#2c3e50;">¡Verifica tu correo!</h2>
            <p style="font-size:16px; line-height:1.6; color:#34495e;">Gracias por registrarte en <strong>MOTOREPUESTO DAVILA</strong>, tu tienda de repuestos de moto. Usa el siguiente código para completar tu registro:</p>
            
            <div style="font-size:42px; font-weight:bold; margin:30px 0; color:#c0392b; background:#ecf0f1; padding:25px; border-radius:12px; display:inline-block; letter-spacing:2px; border:2px dashed #f39c12;">
                {codigo}
            </div>

            <p style="font-size:14px; color:#7f8c8d; margin-top:15px;">Este código expirará en 10 minutos.</p>
            <p style="margin-top:10px; font-size:13px; color:#95a5a6;">Si no solicitaste este correo, ignóralo.</p>

            <div style="background:#ecf0f1; padding:15px; margin-top:30px; border-radius:10px; font-size:12px; color:#95a5a6;">
                <span style="margin:0 5px;">🔧</span>
                <span style="margin:0 5px;">🛠️</span>
                <span style="margin:0 5px;">🛵</span>
                <span style="margin:0 5px;">⚙️</span>
                <p style="margin-top:10px;">© 2025 MOTOREPUESTO DAVILA - Repuestos de moto. Todos los derechos reservados.</p>
            </div>
        </div>

    </div>
    """

    send_mail(
        subject="Código de verificación - Davila Tienda",
        message=f"Tu código de verificación es: {codigo}",
        from_email="no-reply@davilatienda.com",
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )

    return codigo

class ResendCodeView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")

        try:
            peding = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()

        if peding.last_resend_time and now - peding.last_resend_time < timedelta(hours=1):
            if peding.resend_count >= 3:
                return Response(
                    {"error": "Has alcanzado el límite de 3 reenvíos por hora."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            peding.resend_count = 0 

        if peding.last_resend_time and now - peding.last_resend_time < timedelta(minutes=1):
            tiempo_restante = 60 - (now - peding.last_resend_time).seconds
            return Response(
                {"error": f"Debes esperar {tiempo_restante} segundos antes de reenviar el código."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        new_code = enviar_codigo_verificacion(email)
        peding.verification_code = new_code
        peding.code_expires_at = now + timedelta(minutes=10)
        peding.last_resend_time = now
        peding.resend_count += 1
        peding.save()

        send_mail(
            "Nuevo código de verificación",
            f"Tu nuevo código es: {new_code}",
            "no-reply@tuservidor.com",
            [peding.email],
            fail_silently=False,
        )
        return Response(
            {"message": "Nuevo código enviado correctamente."},
            status=status.HTTP_200_OK,
        )
class ProveedorListAPIView(generics.ListAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminUser]

class ProveedorCreateAPIView(generics.CreateAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminUser] 

class ProveedorRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminUser] 

class ProveedorUpdateAPIView(generics.UpdateAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminUser]  

class ProveedorDeleteAPIView(generics.DestroyAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminUser] 

class ProductoListView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre_producto', 'descripcion', 'categoria', 'marca']
    ordering_fields = ['precio_unitario', 'fecha_registro']

    def get_queryset(self):
        hace_7_dias = timezone.now() - timedelta(days=30)
        queryset = Producto.objects.all().order_by('-fecha_registro')

        categoria = self.request.query_params.get('categoria')
        marca = self.request.query_params.get('marca')
        procedencia = self.request.query_params.get('procedencia')

        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        if marca:
            queryset = queryset.filter(marca__icontains=marca)
        if procedencia:
            queryset = queryset.filter(procedencia__icontains=procedencia)

        return queryset

class ProductoCreateView(generics.CreateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminUser]  

class ProductoDetailView(generics.RetrieveAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]  
    lookup_field = 'slug'  

class ProductoUpdateView(generics.UpdateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    parser_classes = [MultiPartParser, FormParser] 
    permission_classes = [IsAdminUser] 

class ProductoDeleteView(generics.DestroyAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminUser]  

class ProductoNuevoListView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]  
    def get_queryset(self):
        hace_30_dias = timezone.now().date() - timedelta(days=30)
        return Producto.objects.filter(
            Q(es_nuevo=True) | Q(fecha_novedad__gte=hace_30_dias)
        ).order_by('-fecha_novedad')

class ProductoDestacadoListView(generics.ListAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]  

    def get_queryset(self):
        nombre = self.request.query_params.get('nombre', None)
        queryset = Producto.objects.filter(es_destacado=True)

        if nombre:
            queryset = queryset.filter(
                Q(nombre_producto__icontains=nombre) |
                Q(categoria__nombre__icontains=nombre)
            )
        return queryset.order_by('-fecha_registro')

class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        carrito, created = Cart.objects.get_or_create(usuario=self.request.user, activo=True)
        return carrito
    
class CartAddProductView(generics.GenericAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        producto_id = request.data.get("producto_id")
        cantidad = int(request.data.get("cantidad", 1))

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response({"detail": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        carrito, created = Cart.objects.get_or_create(usuario=request.user, activo=True)

        carrito.add_producto(producto, cantidad)
        serializer = self.get_serializer(carrito, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Producto
from .serializers import ProductoSerializer

class ProductosRelacionadosView(generics.GenericAPIView):
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]

    def get(self, request, categoria, producto_id=None):
        """
        Devuelve productos relacionados por categoría,
        excluyendo el producto actual (si se pasa producto_id)
        y limitando a 8 resultados.
        """
        queryset = Producto.objects.filter(categoria=categoria)

        # Excluir el producto actual si se pasa su ID
        if producto_id:
            queryset = queryset.exclude(id=producto_id)

        # Limitamos los resultados
        queryset = queryset.order_by('-fecha_registro')[:8]

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class CartUpdateProductView(generics.GenericAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    def put(self, request, producto_id, *args, **kwargs):
        return self.update_cart(request, producto_id)

    def patch(self, request, producto_id, *args, **kwargs):
        return self.update_cart(request, producto_id)

    def update_cart(self, request, producto_id):
        try:
            cantidad = int(request.data.get("cantidad", 1))
            if cantidad < 0:
                return Response({"detail": "La cantidad no puede ser negativa."},
                                status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"detail": "Cantidad inválida."},
                            status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.filter(usuario=request.user, activo=True).first()
        if not cart:
            return Response({"detail": "Carrito no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response({"detail": "Producto no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        cart.update_cantidad(producto, cantidad)
        serializer = self.get_serializer(cart, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class CartRemoveProductView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, producto_id, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(usuario=request.user, activo=True)

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response({"detail": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        item = cart.items.filter(producto=producto).first()
        if not item:
            return Response({"detail": "El producto ya no estaba en el carrito."}, status=status.HTTP_200_OK)

        item.delete()
        return Response({"detail": "Producto eliminado del carrito."}, status=status.HTTP_200_OK)

class CartClearView(APIView):
    """
    Vacía completamente el carrito del usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        try:
            cart, created = Cart.objects.get_or_create(usuario=request.user, activo=True)
            cart.items.all().delete()
            return Response({"message": "Carrito vaciado correctamente"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CategoriaListAPIView(generics.ListAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminUser]  

class CategoriaCreateAPIView(generics.CreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminUser]  

class CategoriaRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminUser]  

class CategoriaUpdateAPIView(generics.UpdateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminUser]  

class CategoriaDeleteAPIView(generics.DestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAdminUser]  

class MarcaListAPIView(generics.ListAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminUser]  

class MarcaCreateAPIView(generics.CreateAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminUser]  

class MarcaRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminUser]  

class MarcaUpdateAPIView(generics.UpdateAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminUser]  

class MarcaDeleteAPIView(generics.DestroyAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminUser]  

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAdminUser]  
    def get_queryset(self):
        return User.objects.filter(is_staff=False)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
class UpdatePricePermissionView(APIView):
    permission_classes = [IsAdminUser]  
    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        puede_ver = request.data.get("puede_ver_precios", None)
        if puede_ver is None:
            return Response({"error": "Debes enviar el campo 'puede_ver_precios'."},
                            status=status.HTTP_400_BAD_REQUEST)

        user.puede_ver_precios = bool(puede_ver)
        user.save()
        return Response({"message": f"Permiso actualizado correctamente para {user.email}."})
    
class AsignarPrecioMayoreoView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        puede_ver = request.data.get("puede_ver_precios_mayoreo", None)
        if puede_ver is not None:
            user.puede_ver_precios_mayoreo = bool(puede_ver)
            user.save()
            return Response({
                "id": user.id,
                "puede_ver_precios": user.puede_ver_precios_mayoreo,
                "mensaje": f"Permiso actualizado para {user.email}"
            })

class LoginView(APIView):
    permission_classes = [AllowAny]

    MAX_ATTEMPTS = 3
    BLOCK_MINUTES = 15

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = User.objects.filter(email=email).first()

        if user and not user.is_active:
            return Response(
                {"detail": "Usuario bloqueado. Comuníquese con soporte."},
                status=status.HTTP_403_FORBIDDEN
            )

        if user and user.blocked_until and user.blocked_until > timezone.now():
            return Response(
                {"detail": f"Usuario bloqueado hasta {user.blocked_until.strftime('%H:%M:%S')}"},
                status=status.HTTP_403_FORBIDDEN
            )

        auth_user = authenticate(request, email=email, password=password)

        if not auth_user:
            if user:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= self.MAX_ATTEMPTS:
                    user.blocked_until = timezone.now() + timedelta(minutes=self.BLOCK_MINUTES)
                    user.failed_login_attempts = 0
                user.save()
            return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        user.failed_login_attempts = 0
        user.blocked_until = None
        user.save()

        refresh = RefreshToken.for_user(auth_user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            "user": {
                "email": auth_user.email,
                "nombre": auth_user.nombre,
                "apellidos": auth_user.apellidos,
                "is_staff": auth_user.is_staff,
                "puede_ver_precios_mayoreo": auth_user.puede_ver_precios_mayoreo
            },
            "access": access_token,
            "refresh": refresh_token,
            "message": "Inicio de sesión exitoso."
        })

        response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="Lax", max_age=3600)
        response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="Lax", max_age=7*24*3600)

        return response

class UserInfoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "email": user.email,
            "nombre": user.nombre,
            "apellidos": user.apellidos,
            "is_staff": user.is_staff
        })
    
class WishlistListView(generics.ListAPIView):
    """
    Retorna todos los productos en la wishlist del usuario autenticado.
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(usuario=self.request.user).select_related("producto")


class WishlistCreateView(generics.CreateAPIView):
    """
    Agrega un producto a la wishlist del usuario autenticado.
    """
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


class WishlistDeleteView(generics.DestroyAPIView):
    """
    Elimina un producto de la wishlist del usuario autenticado.
    """
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, pk, *args, **kwargs):
        try:
            wishlist_item = Wishlist.objects.get(usuario=request.user, producto_id=pk)
            wishlist_item.delete()
            return Response({"detail": "Producto eliminado de la wishlist."},
                            status=status.HTTP_204_NO_CONTENT)
        except Wishlist.DoesNotExist:
            return Response(
                {"detail": "Producto no encontrado en la wishlist."},
                status=status.HTTP_404_NOT_FOUND
            )

class OrderListView(generics.ListAPIView):
    """
    GET: Lista todas las órdenes del usuario autenticado.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")
    
class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = serializer.save()  
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = self.get_serializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderUpdateView(generics.UpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        order = self.get_object()
        if order.status not in ["pending", "processing"]:
            raise PermissionDenied("No se puede modificar una orden completada o cancelada.")
        serializer.save()

class OrderDeleteView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.status not in ["pending", "cancelled"]:
            raise PermissionDenied("Solo se pueden eliminar órdenes pendientes o canceladas.")
        instance.delete()

class AdminOrderListView(generics.ListAPIView):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminOrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

class AdminOrderUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        order = self.get_object()
        previous_status = order.status
        new_status = self.request.data.get("status", previous_status)

        serializer.save(status=new_status)
        updated_order = serializer.instance

        order_items = getattr(updated_order, "items", None)
        if order_items is None or not hasattr(order_items, "all"):
            order_items = OrderItem.objects.filter(order=updated_order)

        if new_status in ["completed", "processing"] and previous_status not in ["completed", "processing"]:
            for item in order_items.all():
                product = item.producto
                if product.stock >= item.cantidad:
                    product.stock -= item.cantidad
                    product.save()
                    print(f"🟢 Stock descontado: {product.nombre_producto} → {product.stock}")
                else:
                    print(f"⚠️ Stock insuficiente para {product.nombre_producto}")

        elif new_status in ["rejected", "cancelled"] and previous_status in ["processing", "completed"]:
            for item in order_items.all():
                product = item.producto
                product.stock += item.cantidad
                product.save()
                print(f"🔁 Stock devuelto: {product.nombre_producto} → {product.stock}")

        print(f"📦 Estado actualizado: {previous_status} → {new_status}")

    def update(self, request, *args, **kwargs):
        """
        Sobrescribimos el método update para devolver una respuesta más clara al frontend.
        """
        response = super().update(request, *args, **kwargs)
        order = self.get_object()
        return Response({
            "detail": f"Estado de la orden actualizado correctamente a '{order.status}'.",
            "order_id": order.id,
            "new_status": order.status
        }, status=status.HTTP_200_OK)

class AdminOrderDeleteView(generics.DestroyAPIView):

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]

class MisPedidosView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(user=user).order_by("-created_at")

class PasswordResetValidateTokenView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if token_generator.check_token(user, token):
            return Response({"valid": True})
        else:
            return Response({"error": "Token inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        password = request.data.get("password")

        if not password:
            return Response(
                {"error": "Debe ingresar una nueva contraseña."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if not token_generator.check_token(user, token):
            return Response(
                {"error": "Token inválido o expirado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(password)
        user.save()

        return Response({"message": "✅ Contraseña restablecida correctamente."}, status=status.HTTP_200_OK)
    
class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Correo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"https://www.motorepuestodavila.com/reset-password?uid={uidb64}&token={token}"

        send_mail(
            "Recupera tu contraseña",
            f"Hola {user.nombre} {user.apellidos or ''}, usa el siguiente enlace para restablecer tu contraseña: {reset_link}",
            "no-reply@tuapp.com",
            [email],
            fail_silently=False,
        )

        return Response({"message": "Correo de recuperación enviado."}, status=status.HTTP_200_OK)
    
class AdminProveedorStatsView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        now = timezone.now()
        primer_dia_mes = timezone.datetime(now.year, now.month, 1, tzinfo=timezone.get_current_timezone())

        items_mes = OrderItem.objects.filter(
            order__status='completed',
            order__created_at__gte=primer_dia_mes
        )

        proveedores_data = (
            items_mes
            .values('producto__proveedor__nombre_empresa')
            .annotate(
                ventas=Sum('cantidad'),
                ganancias=Sum('subtotal')
            )
            .order_by('-ventas') 
        )

        sales_data = [
            {
                "proveedor": p['producto__proveedor__nombre_empresa'],
                "ventas": p['ventas'],
                "ganancias": float(p['ganancias'])
            } for p in proveedores_data
        ]
        categorias_data = (
            items_mes
            .values('producto__categoria')
            .annotate(
                ventas=Sum('cantidad'),
                ganancias=Sum('subtotal')
            )
            .order_by('-ventas')
        )
        categorias_data = [
            {
                "categoria": c['producto__categoria'],
                "ventas": c['ventas'],
                "ganancias": float(c['ganancias'])
            } for c in categorias_data
        ]
        productos_data = (
            items_mes
            .values('producto__nombre_producto')
            .annotate(ventas=Sum('cantidad'))
            .order_by('-ventas')
        )
        productos_data = [
            {"producto": p['producto__nombre_producto'], "ventas": p['ventas']}
            for p in productos_data
        ]

        totales_mes = {
            "ventas": items_mes.aggregate(total_ventas=Sum('cantidad'))['total_ventas'] or 0,
            "ganancias": float(items_mes.aggregate(total_ganancias=Sum('subtotal'))['total_ganancias'] or 0.0)
        }
        data = {
            "salesData": sales_data,
            "categoriasData": categorias_data,
            "productosData": productos_data,
            "totalesMes": totales_mes
        }

        return Response(data)
    
class AdminBlockUserView(APIView):
    permission_classes = [permissions.IsAdminUser]  
    def post(self, request, user_id):
        """Permite al administrador bloquear o desbloquear manualmente a un usuario."""
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        if "is_active" not in request.data:
            return Response(
                {"detail": "Debe incluir el campo 'is_active' (true o false)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        is_active = request.data["is_active"]
        user.is_active = is_active
        if not is_active:
            user.blocked_until = None  
        else:
            user.failed_login_attempts = 0
            user.blocked_until = None
        user.save()
        action = "desbloqueado" if is_active else "bloqueado"
        return Response(
            {"message": f"El usuario {user.email} fue {action} correctamente."},
            status=status.HTTP_200_OK
        )
