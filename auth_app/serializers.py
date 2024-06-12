from rest_framework import serializers
from .models import *
from datetime import timedelta
import random
from django.conf import settings
from django.utils import timezone
from .utils import send_otp

class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model used in POST and GET requests.
    """

    class Meta:
        model = User
        fields = ("id", "phone_number")
        read_only_fields = ("id",)

    def create(self, validated_data):
        """
        Method to create a new user with OTP verification.
        """
        phone_number = validated_data["phone_number"]

        if User.objects.filter(phone_number=phone_number, is_active=True).exists():
            # If phone number already exists, update existing user's OTP
            user = User.objects.get(phone_number=phone_number)
            otp = random.randint(1000, 9999)
            otp_expiry = timezone.now() + timedelta(minutes=10)
            
            user.otp = otp
            user.otp_expiry = otp_expiry
            user.max_otp_try = settings.MAX_OTP_TRY
            user.is_customer = True
            user.save()

            send_otp(phone_number, otp)

            return user
        else:
            # If phone number doesn't exist, create a new user
            otp = random.randint(1000, 9999)
            otp_expiry = timezone.now() + timedelta(minutes=10)

            user = User.objects.create(
                phone_number=phone_number,
                otp=otp,
                otp_expiry=otp_expiry,
                max_otp_try=settings.MAX_OTP_TRY,
                is_customer=True
            )

            send_otp(phone_number, otp)

            return user



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        


class AdminSerializer(serializers.ModelSerializer):
    # GENDER = (('Male','Male'),('Female','Female'),('Others','Others'))
    first_name = serializers.CharField(source='profile.first_name',required=False)
    last_name = serializers.CharField(source='profile.last_name',required=False)
    gender = serializers.CharField(source='profile.gender',required=False)
    address = serializers.CharField(source='profile.address',required=False)
    image = serializers.ImageField(source='profile.image',required=False)

    class Meta:
        model = User
        fields = ("id", "username", "password", "is_product_admin", "is_order_admin", "is_sales_admin", "email", "phone_number", "first_name", "last_name", "gender", "address","image")
        # extra_kwargs = {'password': {'write_only': False}}

    # def create(self, validated_data):
    #     profile_data = validated_data.pop('profile')
    #     user= User.objects.create(username = validated_data['username'], email = validated_data['email'])
        
    #     user.set_password(validated_data['password'])
    #     UserProfile.objects.create(user=user, **profile_data)
    #     user.save()
    #     return validated_data
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        user = User.objects.create_user(is_active=True, **validated_data)
        UserProfile.objects.create(user=user, **profile_data)
        return user
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If this is an update operation, set all fields to not required
        if self.instance:
            for field_name, field in self.fields.items():
                # Keep the fields that were originally required still required during creation
                if field_name in ['username', 'password', 'email', 'phone_number', 'first_name', 'image']:
                    continue
                field.required = False

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})

        # Update User instance fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.save()

        # Update UserProfile instance fields
        profile = instance.profile
        profile.first_name = profile_data.get('first_name', profile.first_name)
        profile.image = profile_data.get('image', profile.image)
        profile.save()

        return instance
    

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):
    # category = serializers.CharField(source='category.name', read_only= True)
    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'image', 'category']