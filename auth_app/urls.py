from django.urls import path, include
from auth_app.views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('customer/', CustomerListCreate.as_view(), name='user-list-create'),
    path('customer/<int:customer_id>/verify-otp/', CustomerVerifyOTP.as_view(), name='user-verify-otp'),
    path('customer/<int:customer_id>/regenerate-otp/', CustomerRegenerateOTP.as_view(), name='user-regenerate-otp'),
    path('product-admins/', ProductAdminListCreate.as_view(), name='product_admin_list_create'),
    path('product-admins-edit/<int:productadmin_id>', ProductAdminEdit.as_view(), name='product_admin_edit'),
    path('order-admins/', OrderAdminListCreate.as_view(), name='order_admin_list_create'),
    path('order-admins-edit/<int:orderadmin_id>', OrderAdminEdit.as_view(), name='order_admin_edit'),
    path('admin/login/', AdminLoginView.as_view()),
    path('dashboard/', DashboardView.as_view()),
    
    
    path('category/', CategoryCreate.as_view(), name='category_create'),
    path('category-edit/<int:category_id>', CategoryEdit.as_view(), name='category_edit'),
    path('subcategory/', SubCategoryCreate.as_view(), name='subcategory_create'),
    path('subcategory-edit/<int:subcategory_id>', SubCategoryEdit.as_view(), name='subcategory_edit'),
]