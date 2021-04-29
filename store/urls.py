from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name = "store"),
    path('search/', views.search, name = "search"),
    path('cart/', views.cart, name = "cart"),
    path('checkout/', views.checkout, name = "checkout"),
    path('account/', views.account, name = "account"),
    path('update-item/', views.userUpdateItemInCart, name= "update-item"),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
]