from rest_framework import generics, status
from rest_framework.response import Response

from .models import Proveedor, Producto, CustomUser, Cart, CartItem, Checkout, PendingUser
from .serializers import (
    ProveedorSerializer,
    ProductoSerializer,
    UserRegisterSerializer,
    CartSerializer,
    CartItemSerializer,
    CheckoutSerializer,
)
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail




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

from django.contrib.auth import authenticate

class LoginView(APIView):
    permission_classes = [AllowAny]  # Permite registrarse sin estar autenticado

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "user": {"email": user.email, "nombre": user.nombre},
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

User = get_user_model()

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


import random
from datetime import timedelta
from django.utils import timezone

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


from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

class ResendCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        try:
            peding = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()

        # Verificar límite de 3 reenvíos por hora
        if peding.last_resend_time and now - peding.last_resend_time < timedelta(hours=1):
            if peding.resend_count >= 3:
                return Response(
                    {"error": "Has alcanzado el límite de 3 reenvíos por hora."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            peding.resend_count = 0  # Reiniciar conteo después de 1 hora

        # Verificar espera mínima de 2 minutos
        if peding.last_resend_time and now - peding.last_resend_time < timedelta(minutes=1):
            tiempo_restante = 60 - (now - peding.last_resend_time).seconds
            return Response(
                {"error": f"Debes esperar {tiempo_restante} segundos antes de reenviar el código."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generar y guardar nuevo código
        new_code = enviar_codigo_verificacion(email)
        peding.verification_code = new_code
        peding.code_expires_at = now + timedelta(minutes=10)
        peding.last_resend_time = now
        peding.resend_count += 1
        peding.save()

        # Enviar correo
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
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login


class ProveedorCreateAPIView(generics.CreateAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login


from rest_framework.generics import RetrieveAPIView
from .models import Producto
from .serializers import ProductoSerializer

class ProductoSlugRetrieveAPIView(RetrieveAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    lookup_field = 'nombre_producto'  # O crea un campo slug en el modelo


class ProveedorUpdateAPIView(generics.UpdateAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

class ProveedorDeleteAPIView(generics.DestroyAPIView):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [AllowAny]

    def destroy(self, request, *args, **kwargs):
        proveedor = self.get_object()
        
        productos = proveedor.product_set.all()  # Cambia 'product_set' por el nombre real de tu relación
        if productos.exists():
            return Response(
                {
                    "detail": "No se puede eliminar proveedor",
                    "products": [p.nombre for p in productos]  # Ajusta 'nombre' según tu modelo
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)

class ProductoListAPIView(generics.ListAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login



class ProductoCreateAPIView(generics.CreateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login


from rest_framework.generics import RetrieveAPIView
from .models import Producto
from .serializers import ProductoSerializer

class ProductoSlugRetrieveAPIView(RetrieveAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    lookup_field = 'nombre_producto'  # O crea un campo slug en el modelo
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

class ProductoUpdateAPIView(generics.UpdateAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login


class ProductoDeleteAPIView(generics.DestroyAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

class CartCreateView(generics.CreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CartListView(generics.ListAPIView):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)


class CartUpdateView(generics.UpdateAPIView):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)


class CartDeleteView(generics.DestroyAPIView):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
class CartItemCreateView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)


class CartItemListView(generics.ListAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)


class CartItemUpdateView(generics.UpdateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)


class CartItemDeleteView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

class CheckoutCreateView(generics.CreateAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def perform_create(self, serializer):
        cart = Cart.objects.filter(user=self.request.user).first()
        if cart:
            serializer.save(user=self.request.user, cart=cart)


class CheckoutListView(generics.ListAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login

    def get_queryset(self):
        return Checkout.objects.filter(user=self.request.user)


class CheckoutDetailView(generics.RetrieveAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login
    lookup_field = "pk"

    def get_queryset(self):
        return Checkout.objects.filter(user=self.request.user)


class CheckoutUpdateView(generics.UpdateAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [AllowAny]  # 🔑 Aquí permitimos acceso sin login
    lookup_field = "pk"

    def get_queryset(self):
        return Checkout.objects.filter(user=self.request.user)


class CheckoutDeleteView(generics.DestroyAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [AllowAny] 
    lookup_field = "pk"

    def get_queryset(self):
        return Checkout.objects.filter(user=self.request.user)

class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class UserDeleteView(generics.DestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def delete(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            user.delete()
            return Response({"message": "Usuario eliminado correctamente"}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
