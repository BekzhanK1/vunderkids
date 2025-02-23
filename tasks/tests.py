from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from account.models import Child, Student

from .models import Content, Course, Question, Section, Task

User = get_user_model()

class CourseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', password='password')
        self.course = Course.objects.create(
            name='Math', description='Math course', grade=5, created_by=self.user, language='en'
        )

    def test_course_creation(self):
        self.assertEqual(self.course.name, 'Math')
        self.assertEqual(self.course.grade, 5)

class SectionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', password='password')
        self.course = Course.objects.create(
            name='Math', description='Math course', grade=5, created_by=self.user, language='en'
        )
        self.section = Section.objects.create(
            course=self.course, title='Algebra', description='Basic Algebra', order=1
        )

    def test_section_creation(self):
        self.assertEqual(self.section.title, 'Algebra')
        self.assertEqual(self.section.course, self.course)

class ContentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', password='password')
        self.course = Course.objects.create(
            name='Math', description='Math course', grade=5, created_by=self.user, language='en'
        )
        self.section = Section.objects.create(
            course=self.course, title='Algebra', description='Basic Algebra', order=1
        )
        self.content = Content.objects.create(
            title='Lesson 1', description='Introduction to Algebra', order=1, section=self.section, content_type='lesson'
        )

    def test_content_creation(self):
        self.assertEqual(self.content.title, 'Lesson 1')
        self.assertEqual(self.content.section, self.section)

class APITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.course = Course.objects.create(
            name='Math', description='Math course', grade=5, created_by=self.user, language='en'
        )
        self.section = Section.objects.create(
            course=self.course, title='Algebra', description='Basic Algebra', order=1
        )
        self.content = Content.objects.create(
            title='Lesson 1', description='Introduction to Algebra', order=1, section=self.section, content_type='lesson'
        )
        self.task = Task.objects.create(
            title='Task 1', description='Solve equations', order=1, section=self.section, content_type='task'
        )
        self.question = Question.objects.create(
            task=self.task, title='Question 1', question_text='What is 2+2?', question_type='multiple_choice_text',
            options={'1': '3', '2': '4'}, correct_answer='2'
        )

    def test_get_courses(self):
        response = self.client.get('/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Math')

    def test_create_course(self):
        data = {
            'name': 'Science', 'description': 'Science course', 'grade': 5,
            'language': 'en', 'created_by': self.user.id
        }
        response = self.client.post('/courses/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Science')

    def test_get_sections(self):
        response = self.client.get(f'/courses/{self.course.id}/sections/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Algebra')

    def test_create_section(self):
        data = {
            'title': 'Geometry', 'description': 'Basic Geometry', 'order': 2,
            'course': self.course.id
        }
        response = self.client.post(f'/courses/{self.course.id}/sections/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Geometry')

    def test_get_content(self):
        response = self.client.get(f'/courses/{self.course.id}/sections/{self.section.id}/contents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_content(self):
        data = {
            'title': 'Lesson 2', 'description': 'Advanced Algebra', 'order': 2,
            'section': self.section.id, 'content_type': 'lesson'
        }
        response = self.client.post(f'/courses/{self.course.id}/sections/{self.section.id}/contents/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Lesson 2')

    def test_get_tasks(self):
        response = self.client.get(f'/courses/{self.course.id}/sections/{self.section.id}/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Task 1')

    def test_create_task(self):
        data = {
            'title': 'Task 2', 'description': 'Advanced equations', 'order': 2,
            'section': self.section.id, 'content_type': 'task'
        }
        response = self.client.post(f'/courses/{self.course.id}/sections/{self.section.id}/tasks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Task 2')

    def test_answer_question(self):
        data = {
            'answer': '2'  # Assuming the correct answer is option 2 ('4')
        }
        response = self.client.post(f'/tasks/{self.task.id}/questions/{self.question.id}/answer/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_correct'])

class StudentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='studentuser', password='password')
        self.student = Student.objects.create(user=self.user, grade=5)

    def test_student_creation(self):
        self.assertEqual(self.student.grade, 5)
        self.assertEqual(self.student.user, self.user)

class ChildModelTest(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(username='parentuser', password='password')
        self.child = Child.objects.create(parent=self.parent, grade=3)

    def test_child_creation(self):
        self.assertEqual(self.child.grade, 3)
        self.assertEqual(self.child.parent, self.parent)
