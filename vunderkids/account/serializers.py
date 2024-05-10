from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import get_user_model
from account.models import *
from .tasks import send_activation_email


User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'phone_number', 'role', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number', ''),
            role=validated_data.get('role', 'student'),
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'role']
        

        
class ParentRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField()

    class Meta:
        model = Parent
        fields = ['email', 'password', 'first_name', 'last_name', 'phone_number']


    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email format.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        # Create user
        user_data = {
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'phone_number': validated_data.pop('phone_number'),
            'role': 'parent',
            'is_active': False
        }
        user = User.objects.create_user(**user_data)
        user.set_password(validated_data.pop('password'))
        user.save()
        send_activation_email.delay(user.id)

        # Create parent profile
        parent = Parent.objects.create(user=user, **validated_data)
        return parent

        
class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = '__all__'
        
        
class SchoolRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=17, required=False, allow_blank=True)
    
    class Meta:
        model = School
        fields = ('name', 'city', 'email', 'password', 'first_name', 'last_name', 'phone_number')


    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email format.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        # Create user
        user_data = {
            key: validated_data.pop(key) for key in ['email', 'first_name', 'last_name', 'phone_number']
        }
        password = validated_data.pop('password')
        user = User.objects.create_user(**user_data, role='principal', is_active=False)
        user.set_password(password)
        user.save()
        send_activation_email.delay(user.id)

        # Create school associated with this user
        school = School.objects.create(user=user, **validated_data)
        return school
    
class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'
        
        
class TeacherRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=17, required=False, allow_blank=True)        
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), write_only=True)

    
    class Meta:
        model = Teacher
        fields = ('email', 'password', 'first_name', 'last_name', 'phone_number', 'subject', 'school')
    
    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email format.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        school = validated_data.pop('school')
        # Create user
        user_data = {
            key: validated_data.pop(key) for key in ['email', 'first_name', 'last_name', 'phone_number']
        }
        password = validated_data.pop('password')
        user = User.objects.create_user(**user_data, role='teacher')
        user.set_password(password)
        user.save()

        # Create teacher associated with this user
        teacher = Teacher.objects.create(user=user, school = school, **validated_data)
        return teacher
    
class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Teacher
        fields = '__all__'
        
class ClassSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(allow_null=True, required=False)
    class Meta:
        model = Class
        fields = '__all__'


class StudentRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=17, required=False, allow_blank=True)
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), write_only=True)
    
    class Meta:
        model = Student
        fields = ('email', 'password', 'first_name', 'last_name', 'phone_number', 'school', 'gpa')

    def validate_email(self, value):
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email format.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        school = validated_data.pop('school')
        # Create user
        user_data = {
            key: validated_data.pop(key) for key in ['email', 'first_name', 'last_name', 'phone_number']
        }
        password = validated_data.pop('password')
        user = User.objects.create_user(**user_data, role='student')
        user.set_password(password)
        user.save()

        # Create student associated with this user
        student = Student.objects.create(user=user, school = school,**validated_data)
        return student
    
class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Student
        fields = '__all__'
        
        
class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child       
        fields = '__all__'
        
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)


        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.is_principal():
            enitity_id = School.objects.get(user=self.user).pk
        elif self.user.is_teacher():
            enitity_id = Teacher.objects.get(user=self.user).pk
        elif self.user.is_student():
            enitity_id = Student.objects.get(user=self.user).pk
        elif self.user.is_parent():
            enitity_id = Parent.objects.get(user=self.user).pk
        else:
            enitity_id = None

        data['user'] = {
            'user_id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'entity_id': enitity_id
        }

        return data