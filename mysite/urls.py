"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include 
from register import views as vreg
from managers import views as mg

from django.conf.urls.static import static
from django.conf import settings
from rest_framework.authtoken import views


urlpatterns = [
	path('s/',include('snippets.urls')),
    path('admin/', admin.site.urls),
    path('', include("store.urls")), #eğer domainde bişi yazmıyosa maine yolla
    path("register/", vreg.register, name="register" ),
    path("login/", vreg.loginPage, name="login" ),
    path("logout/", vreg.logoutPage, name="logout" ),
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="register/password-reset.html", success_url="done/"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="register/password-reset-done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view(template_name="register/password-reset-confirm.html"), name="password_reset_confirm"),
    path('', include("django.contrib.auth.urls")), 
    path('api-auth/', include('rest_framework.urls')),
    path('api-token-auth/', views.obtain_auth_token, name='api-token-auth'),
    path("api/", include("api.urls", namespace='api')),
    path('product-manager/', mg.productManager, name='product-manager'),
    path('tables/', mg.pmTables, name='tables'),
    path('delete_product/<int:id>/', mg.deleteProduct, name='delete_product'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)