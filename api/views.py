from rest_framework import viewsets, permissions
from products.models import Category, Product
from api.serializers import CategorySerializer, ProductSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow administrators to edit objects.
    Read-only permissions are allowed for any authenticated user.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.perfil == 'ADMINISTRADOR'

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    queryset = Category.objects.all().order_by('nome')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = Product.objects.all().order_by('nome')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
