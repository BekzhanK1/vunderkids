from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from account.models import Student, Parent, Child
from account.utils import render_email
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail


@shared_task
def send_daily_email_to_all_students():
    students = Student.objects.all()

    for student in students:
        html_content, text_content = render_email(student.user.first_name, student.user.last_name, student.xp)
        msg = EmailMultiAlternatives(
            subject='Daily Update',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[student.user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()



@shared_task
def send_daily_email_to_all_parents():
    parents = Parent.objects.prefetch_related('children').all()
    for parent in parents:
        if parent.user.is_active:
            context = {
                'first_name': parent.user.first_name,
                'last_name': parent.user.last_name,
                'children': parent.children.all()
            }
            html_content = render_to_string('parent_email_template.html', context)
            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(
                subject='Your Children’s Daily Update',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[parent.user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()


@shared_task
def send_activation_email(user_id):
    from .models import User
    user = User.objects.get(pk=user_id)
    activation_url = f"http://127.0.0.1:8000/api/activate/{user.activation_token}/"
    
    context = {
        'user': user,
        'activation_url': activation_url,
    }

    subject = 'Activate your Vunderkids Account'
    html_message = render_to_string('activation_email.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    send_mail(subject, plain_message, from_email, [to], html_message=html_message)

