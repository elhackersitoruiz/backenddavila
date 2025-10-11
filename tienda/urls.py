from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CartCreateView, CartListView, CartUpdateView, CartDeleteView,
    CartItemCreateView, CartItemListView, CartItemUpdateView, CartItemDeleteView,
    CheckoutCreateView, CheckoutListView, CheckoutUpdateView, CheckoutDeleteView, ProductoSlugRetrieveAPIView,
    ProveedorListAPIView, ProveedorCreateAPIView,
    ProveedorUpdateAPIView, ProveedorDeleteAPIView,
    ProductoListAPIView, ProductoCreateAPIView,
    ProductoUpdateAPIView, ProductoDeleteAPIView,
    RegisterView, RegisterView, LoginView, UserDeleteView, UserListView, VerifyCodeView, ResendCodeView
)

urlpatterns = [
    # -------------------
    # CART
    # -------------------
    path("cart/create/", CartCreateView.as_view(), name="cart-create"),
    path("cart/list/", CartListView.as_view(), name="cart-list"),
    path("cart/update/<int:pk>/", CartUpdateView.as_view(), name="cart-update"),
    path("cart/delete/<int:pk>/", CartDeleteView.as_view(), name="cart-delete"),

    # -------------------
    # CART ITEMS
    # -------------------
    path("cartitem/create/", CartItemCreateView.as_view(), name="cartitem-create"),
    path("cartitem/list/", CartItemListView.as_view(), name="cartitem-list"),
    path("cartitem/update/<int:pk>/", CartItemUpdateView.as_view(), name="cartitem-update"),
    path("cartitem/delete/<int:pk>/", CartItemDeleteView.as_view(), name="cartitem-delete"),

    # -------------------
    # CHECKOUT
    # -------------------
    path("checkout/create/", CheckoutCreateView.as_view(), name="checkout-create"),
    path("checkout/list/", CheckoutListView.as_view(), name="checkout-list"),
    path("checkout/update/<int:pk>/", CheckoutUpdateView.as_view(), name="checkout-update"),
    path("checkout/delete/<int:pk>/", CheckoutDeleteView.as_view(), name="checkout-delete"),

    # -------------------
    # PROVEEDORES
    # -------------------
    path("proveedores/", ProveedorListAPIView.as_view(), name="proveedor-list"),
    path("proveedores/create/", ProveedorCreateAPIView.as_view(), name="proveedor-create"),
    path("productos/slug/<str:nombre_producto>/", ProductoSlugRetrieveAPIView.as_view(), name="producto-detail-slug"),
    path("proveedores/<int:pk>/update/", ProveedorUpdateAPIView.as_view(), name="proveedor-update"),
    path("proveedores/<int:pk>/delete/", ProveedorDeleteAPIView.as_view(), name="proveedor-delete"),

    # -------------------
    # PRODUCTOS
    # -------------------
    path("productos/", ProductoListAPIView.as_view(), name="producto-list"),
    path("productos/create/", ProductoCreateAPIView.as_view(), name="producto-create"),
    path("productos/slug/<str:nombre_producto>/", ProductoSlugRetrieveAPIView.as_view(), name="producto-detail-slug"),
    path("productos/<int:pk>/update/", ProductoUpdateAPIView.as_view(), name="producto-update"),
    path("productos/<int:pk>/delete/", ProductoDeleteAPIView.as_view(), name="producto-delete"),


    path("usuarios/", UserListView.as_view(), name="user-list"),                # GET
    path("usuarios/<int:pk>/eliminar/", UserDeleteView.as_view(), name="user-delete"),  # DELETE
    path("register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path('verify/', VerifyCodeView.as_view(), name='verify'),
    path('resend-code/', ResendCodeView.as_view(), name='resend_code'),

]



