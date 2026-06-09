from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

app_name = 'api'

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
