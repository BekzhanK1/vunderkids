from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import RegexValidator
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)




class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('principal', 'Principal'),
        ('admin', 'Admin'),
        
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=False)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

    def is_parent(self):
        return self.role == 'parent'
    
    def is_principal(self):
        return self.role == 'principal'

    
    
class School(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'school')
    name = models.CharField(max_length=150, blank=False)
    city = models.CharField(max_length=150, blank=False)
    
    def __str__(self):
        return f"{self.name}"
    
    

    
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    subject = models.CharField(max_length=150, blank=False)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null = True, blank = True, related_name='teachers')
    
    
class Class(models.Model):
    GRADE_CHOICES = [(i, str(i)) for i in range(0, 13)]  # Generates grade choices from 0 to 12
    SECTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
        ('F', 'F'),
        ('G', 'G'),
    ]
    
    grade = models.IntegerField(choices=GRADE_CHOICES)
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='classes')

    def __str__(self):
        return f"{self.grade}{self.section}"
    
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student')
    gpa = models.SmallIntegerField(default=4, blank=True, null=True)
    school_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null = True, blank = True, related_name='students')
    
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'parent')
    
class Child(models.Model):
    GRADE_CHOICES = [(i, str(i)) for i in range(0, 13)]
    parent = models.ForeignKey(Parent, on_delete = models.CASCADE, related_name = 'children')
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    date_of_birth = models.DateField(null=True, blank=True)
    school = models.CharField(max_length = 255, default = "NIS")
    grade = models.IntegerField(choices=GRADE_CHOICES)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"[Child] {self.first_name} {self.last_name}"
    
    
    
