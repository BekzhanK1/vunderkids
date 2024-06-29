from datetime import date, timedelta
from django.utils import timezone
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.conf import settings


GRADE_CHOICES = [(i, str(i)) for i in range(0, 5)]
SECTION_CHOICES = [(chr(i), chr(i)) for i in range(ord('А'), ord('Я') + 1)]
GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
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
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('supervisor', 'Supervisor'),  # Added 'supervisor' role
    )
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_parent(self):
        return self.role == 'parent'

    @property
    def is_supervisor(self):
        return self.role == 'supervisor'  # Added 'is_supervisor' property

class School(models.Model):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=150)
    email = models.EmailField(unique=False)
    supervisor = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='school')

    def __str__(self):
        return f"{self.name} ({self.city})"

class Class(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classes')
    grade = models.IntegerField(choices=GRADE_CHOICES)
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)

    def __str__(self):
        return f"{self.grade}{self.section}"
    

class LevelRequirement(models.Model):
    level = models.PositiveIntegerField(unique=True)
    cups_required = models.PositiveIntegerField()

    def __str__(self):
        return f'Level {self.level}: {self.cups_required} cups'

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student', )
    school_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    grade = models.IntegerField(choices=GRADE_CHOICES)
    level = models.PositiveIntegerField(default=1)
    streak = models.PositiveIntegerField(default=0)
    cups = models.PositiveIntegerField(default=0)
    stars = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="O")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    birth_date = models.DateField(default=date(2015, 1, 1))
    last_task_completed_at = models.DateTimeField(null=True, blank = True)

    def __str__(self):
        return f"[Student: {self.pk}] {self.user.first_name} {self.user.last_name}"
    
    def update_level(self):
        level_requirements = LevelRequirement.objects.order_by('level')
        for requirement in level_requirements:
            if self.cups >= requirement.cups_required:
                self.level = requirement.level
            else:
                break
        self.save()

    def update_streak(self):
        now = timezone.now()
        if self.last_task_completed_at:
            if now.date() == self.last_task_completed_at.date():
                return
            elif now.date() == (self.last_task_completed_at + timedelta(days=1)).date():
                self.streak += 1
            else:
                self.streak = 0
        else:
            self.streak = 1
        self.last_task_completed_at = now
        self.save()

    def add_question_reward(self):
        question_reward = settings.QUESTION_REWARD
        self.cups += question_reward
        self.stars += question_reward
        self.save()
            
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent')

    def __str__(self):
        return f"[Parent] {self.user.first_name} {self.user.last_name}"

class Child(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    grade = models.IntegerField(choices=GRADE_CHOICES)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="O")
    cups = models.PositiveIntegerField(default=0)
    stars = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    streak = models.PositiveIntegerField(default=0)
    birth_date = models.DateField(default=date(2015, 1, 1))
    last_task_completed_at = models.DateTimeField(null=True, blank = True)

    def update_level(self):
        level_requirements = LevelRequirement.objects.order_by('level')
        for requirement in level_requirements:
            if self.cups >= requirement.cups_required:
                self.level = requirement.level
            else:
                break
        self.save()

    def update_streak(self):
        now = timezone.now()
        if self.last_task_completed_at:
            if now.date() == self.last_task_completed_at.date():
                return
            elif now.date() == (self.last_task_completed_at + timedelta(days=1)).date():
                self.streak += 1
            else:
                self.streak = 0
        else:
            self.streak = 1
        self.last_task_completed_at = now
        self.save()

    def add_question_reward(self):
        question_reward = settings.QUESTION_REWARD
        self.cups += question_reward
        self.stars += question_reward
        self.save()

    def __str__(self):
        return f"[Child: {self.pk}] {self.first_name} {self.last_name}"
    