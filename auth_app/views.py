from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from .models import *
from .serializers import *
from .utils import send_otp
import random
import datetime
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.contrib.auth import authenticate, login


class CustomerListCreate(APIView):
    def get(self, request, format=None):
        try:
            # Retrieve customers who are flagged as 'customer'
            users = User.objects.filter(is_customer=True)
            if not users:
                return Response({"message": "The customer is empty"})
            serializer = CustomerSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to retrieve customers: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        try:
            serializer = CustomerSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            # Provide specific error messages for different validation failures
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to create customer: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomerDetail(APIView):
    def get_object(self, customer_id):
        return get_object_or_404(User, id=customer_id)

    def get(self, request, customer_id, format=None):
        try:
            user = self.get_object(customer_id)
            serializer = CustomerSerializer(user)
            return Response(serializer.data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    def put(self, request, customer_id, format=None):
        try:
            user = self.get_object(customer_id)
            serializer = CustomerSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, customer_id, format=None):
        try:
            user = self.get_object(customer_id)
            serializer = CustomerSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, customer_id, format=None):
        try:
            user = self.get_object(customer_id)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomerVerifyOTP(APIView):
    def patch(self, request, customer_id=None, format=None):
        try:
            user = get_object_or_404(User, id=customer_id)
            otp = request.data.get("otp")

            if user.is_active and user.otp == otp and user.otp_expiry and timezone.now() < user.otp_expiry:
                # User is already active, update OTP-related fields and generate token
                user.otp_expiry = None
                user.max_otp_try = settings.MAX_OTP_TRY
                user.otp_max_out = None
                user.save()

                refresh = RefreshToken.for_user(user)
                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'otp' : 'Successfully verified the customer',
                    'message' : 'The customer already exists'
                }
                return Response(data, status=status.HTTP_200_OK)

            elif not user.is_active and user.otp == otp and user.otp_expiry and timezone.now() < user.otp_expiry:
                # OTP verification successful, activate user and generate token
                user.is_active = True
                user.otp_expiry = None
                user.max_otp_try = settings.MAX_OTP_TRY
                user.otp_max_out = None
                user.save()

                refresh = RefreshToken.for_user(user)
                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'otp' : 'Successfully verified the customer',
                    'message' : 'New customer'
                }
                return Response(data,  status=status.HTTP_201_CREATED)
            else:
                return Response("incorrect OTP.", status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(f"Something went wrong: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomerRegenerateOTP(APIView):
    def patch(self, request, customer_id=None, format=None):
        try:
            user = get_object_or_404(User, id=customer_id)

            if int(user.max_otp_try) == 0 and timezone.now() < user.otp_max_out:
                return Response(
                    "Max OTP try reached, try after an hour",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            otp = random.randint(1000, 9999)
            otp_expiry = timezone.now() + datetime.timedelta(minutes=10)
            max_otp_try = int(user.max_otp_try) - 1

            user.otp = otp
            user.otp_expiry = otp_expiry
            user.max_otp_try = max_otp_try

            if max_otp_try == 0:
                otp_max_out = timezone.now() + datetime.timedelta(hours=1)
                user.otp_max_out = otp_max_out
            elif max_otp_try == -1:
                user.max_otp_try = settings.MAX_OTP_TRY
            else:
                user.otp_max_out = None
                user.max_otp_try = max_otp_try

            user.save()
            send_otp(user.phone_number, otp)
            return Response("Successfully generate new OTP.", status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ProductAdminListCreate(APIView):
    def get(self, request, format=None):
        try:
            users = User.objects.filter(is_product_admin=True)
            if not users:
                return Response({"message": "No product admins found."}, status=status.HTTP_204_NO_CONTENT)
            serializer = AdminSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to retrieve product admins: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        try:
            serializer = AdminSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(is_product_admin=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to create product admin: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class ProductAdminEdit(APIView):
    def get_object(self, productadmin_id):
        return get_object_or_404(User, id=productadmin_id)

    def get(self, request, productadmin_id, format=None):
        productadmin = User.objects.get(id = productadmin_id)
        serializer = AdminSerializer(productadmin)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def patch(self, request, productadmin_id):
        user = self.get_object(productadmin_id)
        serializer = AdminSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, productadmin_id, format=None):
        product = User.objects.get(id = productadmin_id)
        product.delete()
        return Response(status = status.HTTP_204_NO_CONTENT)

class OrderAdminListCreate(APIView):
    def get(self, request, format=None):
        try:
            users = User.objects.filter(is_order_admin=True)
            if not users:
                return Response({"message": "No order admins found."}, status=status.HTTP_204_NO_CONTENT)
            serializer = AdminSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to retrieve orderadmins: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        try:
            serializer = AdminSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(is_order_admin=True)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to create order admin: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class OrderAdminEdit(APIView):
    def get_object(self, orderadmin_id):
        return get_object_or_404(User, id=orderadmin_id)

    def get(self, request, orderadmin_id, format=None):
        orderadmin = User.objects.get(id = orderadmin_id)
        serializer = AdminSerializer(orderadmin)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def patch(self, request, orderadmin_id):
        user = self.get_object(orderadmin_id)
        serializer = AdminSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)     
    def delete(self, request, orderadmin_id, format=None):
        order = User.objects.get(id = orderadmin_id)
        order.delete()
        return Response(status = status.HTTP_204_NO_CONTENT) 

class AdminLoginView(APIView):
    def post(self, request, format=None):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                serializer = AdminSerializer(user)
                refresh = RefreshToken.for_user(user)
                response_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'message' : 'Login successful'
                }
                return Response({"user":serializer.data, "token":response_data}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"message": "An error occurred during login", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class DashboardView(APIView):
    def get(self, request, format=None):
        user = request.user
        return Response({
            "message":"its dashbord",
            "user":str(user)
        }, status=status.HTTP_200_OK)
        
        
class CategoryCreate(APIView):
    def get(self, request, format=None):
       try:
           category = Category.objects.all()
           serializer = CategorySerializer(category, many=True)
           return Response(serializer.data, status=status.HTTP_200_OK) 
       except Exception as e:
           return Response({"error": f"Failed to retrieve category list: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
    def post(self, request, format=None):
       try:
           serializer = CategorySerializer(data=request.data)
           if serializer.is_valid():
               serializer.save()
               return Response(serializer.data, status=status.HTTP_201_CREATED)
           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       except Exception as e:
           return Response({"error": f"Failed to create category: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryEdit(APIView):
    def get_object(self, category_id):
        return get_object_or_404(Category, id=category_id)
    
    def get(self, request, category_id, format=None):
        category = Category.objects.get(id = category_id)
        serializer = CategorySerializer(category)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def patch(self, request, category_id):
        category = self.get_object(category_id)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, category_id, format=None):
        category = self.get_object(category_id)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
#-----------SubCategory   
class SubCategoryCreate(APIView):
    def get(self, request, format=None):
       try:
           Subcategory = SubCategory.objects.all()
           serializer = SubCategorySerializer(Subcategory, many=True)
           return Response(serializer.data, status=status.HTTP_200_OK) 
       except Exception as e:
           return Response({"error": f"Failed to retrieve subcategory list: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       
    def post(self, request, format=None):
       try:
           serializer = SubCategorySerializer(data=request.data)
           if serializer.is_valid():
               serializer.save()
               return Response(serializer.data, status=status.HTTP_201_CREATED)
           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       except Exception as e:
           return Response({"error": f"Failed to create subcategory: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
        
class SubCategoryEdit(APIView):
    def get_object(self, subcategory_id):
        return get_object_or_404(SubCategory, id=subcategory_id)
    
    def delete(self, request, subcategory_id, format=None):
        subcategory = self.get_object(subcategory_id)
        subcategory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    
