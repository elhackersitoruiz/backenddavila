from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import (
    AdminBlockUserView, AdminProveedorStatsView, AsignarPrecioMayoreoView,CartDetailView,CartAddProductView,CartUpdateProductView,CartRemoveProductView, MisPedidosView,
    ProductoCreateView, ProductoDeleteView, ProductoDetailView, ProductoListView, ProductoUpdateView, ProductosRelacionadosView,
    ProveedorListAPIView, ProveedorCreateAPIView,CartClearView,
    ProveedorUpdateAPIView, ProveedorDeleteAPIView,
    RegisterView, RegisterView, LoginView, RequestPasswordResetView, UpdatePricePermissionView, UserInfoView, UserListView, UserProfileView, VerifyCodeView, ResendCodeView,
      CategoriaListAPIView, CategoriaCreateAPIView, CategoriaUpdateAPIView, CategoriaDeleteAPIView,
    MarcaListAPIView, MarcaCreateAPIView, MarcaUpdateAPIView, MarcaDeleteAPIView, WishlistListView, WishlistCreateView, WishlistDeleteView,    OrderListView,
    OrderCreateView,
    OrderDetailView,
    OrderUpdateView,
    OrderDeleteView,    AdminOrderListView,
    AdminOrderDetailView,
    AdminOrderUpdateView,
    AdminOrderDeleteView,    
    PasswordResetValidateTokenView,
    PasswordResetConfirmView,
)

urlpatterns = [

    path("cart/", CartDetailView.as_view(), name="cart-detail"),              # GET
    path("cart/add/", CartAddProductView.as_view(), name="cart-add"),          # POST
    path("cart/update/<int:producto_id>/", CartUpdateProductView.as_view(), name="cart-update"),
    path('cart/remove/<int:producto_id>/', CartRemoveProductView.as_view(), name='cart-remove'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),

    path("proveedores/", ProveedorListAPIView.as_view(), name="proveedor-list"),
    path("proveedores/create/", ProveedorCreateAPIView.as_view(), name="proveedor-create"),
    path("proveedores/<int:pk>/update/", ProveedorUpdateAPIView.as_view(), name="proveedor-update"),
    path("proveedores/<int:pk>/delete/", ProveedorDeleteAPIView.as_view(), name="proveedor-delete"),

    path('productos/', ProductoListView.as_view(), name='producto-list-create'),
    path('productos/create/', ProductoCreateView.as_view(), name='producto-list-create'),
    path('productos/<slug:slug>/', ProductoDetailView.as_view(), name='producto-detail'),
    path('productos/<int:pk>/update/', ProductoUpdateView.as_view(), name='producto-update'),
    path('productos/<int:pk>/delete/', ProductoDeleteView.as_view(), name='producto-delete'),

    path('categorias/', CategoriaListAPIView.as_view(), name='categoria-list'),
    path('categorias/create/', CategoriaCreateAPIView.as_view(), name='categoria-create'),
    path('categorias/<int:pk>/update/', CategoriaUpdateAPIView.as_view(), name='categoria-update'),
    path('categorias/<int:pk>/delete/', CategoriaDeleteAPIView.as_view(), name='categoria-delete'),

    path('marcas/', MarcaListAPIView.as_view(), name='marca-list'),
    path('marcas/create/', MarcaCreateAPIView.as_view(), name='marca-create'),
    path('marcas/<int:pk>/update/', MarcaUpdateAPIView.as_view(), name='marca-update'),
    path('marcas/<int:pk>/delete/', MarcaDeleteAPIView.as_view(), name='marca-delete'),

    path("usuarios/", UserListView.as_view(), name="user-list"),
    path("usuarios/perfil/", UserProfileView.as_view(), name="user-profile"),
    path("usuarios/<int:pk>/permiso/", UpdatePricePermissionView.as_view(), name="update-price-permission"),
    path('usuarios/<int:id>/asignar-precio-mayoreo/', AsignarPrecioMayoreoView.as_view(), name='asignar-precio-mayoreo'),
    path('api/user-info/', UserInfoView.as_view(), name='user-info'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),


    path("register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path('verify/', VerifyCodeView.as_view(), name='verify'),
    path('resend-code/', ResendCodeView.as_view(), name='resend_code'),

    path('wishlist/', WishlistListView.as_view(), name='wishlist-list'),
    path('wishlist/add/', WishlistCreateView.as_view(), name='wishlist-add'),
    path('wishlist/<int:pk>/delete/', WishlistDeleteView.as_view(), name='wishlist-delete'),

    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/create/", OrderCreateView.as_view(), name="order-create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/update/", OrderUpdateView.as_view(), name="order-update"),
    path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order-delete"),
    path("mis-pedidos/", MisPedidosView.as_view(), name="mis-pedidos"),


    path("admin/orders/", AdminOrderListView.as_view(), name="admin-order-list"),
    path("admin/orders/<int:pk>/", AdminOrderDetailView.as_view(), name="admin-order-detail"),
    path("admin/orders/<int:pk>/update/", AdminOrderUpdateView.as_view(), name="admin-order-update"),
    path("admin/orders/<int:pk>/delete/", AdminOrderDeleteView.as_view(), name="admin-order-delete"),

    path("password-reset/validate-token/", PasswordResetValidateTokenView.as_view(), name="password-reset-validate"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password-reset/", RequestPasswordResetView.as_view(), name="password-reset"),
    
    path('admin/proveedor-stats/', AdminProveedorStatsView.as_view(), name='admin-proveedor-stats'),
    path("admin/block-user/<int:user_id>/", AdminBlockUserView.as_view(), name="admin-block-user"),
path(
        "productos/relacionados/<str:categoria>/",
        ProductosRelacionadosView.as_view(),
        name="productos-relacionados",
    ),
    path(
        "productos/relacionados/<str:categoria>/<int:producto_id>/",
        ProductosRelacionadosView.as_view(),
        name="productos-relacionados-id",
    ),
]



