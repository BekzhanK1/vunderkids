from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
# Create your models here.

class User(AbstractUser):
    ROLE_CHOICES = (
        ('school', 'School'),
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
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, blank=True, null=True)

    def is_school(self):
        return self.role == 'school'

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
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'teacher')
    subject = models.CharField(max_length=150, blank=False)
    
    
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
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'student')
    gpa = models.SmallIntegerField(default = 4, blank = True, null = True )
    
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'parent')
    
class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete = models.CASCADE, related_name = 'children')
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    date_of_birth = models.DateField(null=True, blank=True)
    school = models.CharField(max_length = 255, default = "NIS")
    grade = models.PositiveSmallIntegerField()
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"[Child] {self.first_name} {self.last_name}"
    
    
    
