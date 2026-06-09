from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('primeiro-acesso/', views.FirstAccessView.as_view(), name='primeiro_acesso'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/new/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/toggle-active/', views.UserToggleActiveView.as_view(), name='user_toggle_active'),
    path('users/inactive/', views.InactiveUserListView.as_view(), name='user_inactive_list'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
]
