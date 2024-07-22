from celery import shared_task
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from account.models import Child, Student, Parent, User
from subscription.models import Subscription
from account.utils import generate_password, render_email
from django.utils import timezone
from datetime import timedelta, time

frontend_url = settings.FRONTEND_URL


def send_mass_html_mail(datatuple, fail_silently=False):
    messages = []
    for subject, text_content, html_content, from_email, recipient_list in datatuple:
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        messages.append(msg)
    connection = get_connection(fail_silently=fail_silently)
    return connection.send_messages(messages)


@shared_task
def send_daily_email_to_all_students():
    students = Student.objects.all().select_related('user')
    datatuple = []
    for student in students:
        html_content, text_content = render_email(student.user.first_name, student.user.last_name, student.cups, student.level)
        msg = (
            'Daily Update',
            text_content,
            html_content,
            settings.DEFAULT_FROM_EMAIL,
            [student.user.email]
        )
        datatuple.append(msg)
    
    send_mass_html_mail(datatuple, fail_silently=False)


@shared_task
def send_daily_email_to_all_parents():
    parents = Parent.objects.prefetch_related('children').select_related('user').all()
    datatuple = []
    for parent in parents:
        if parent.user.is_active:
            if parent.children.all().count() == 0:
                return
            context = {
                'first_name': parent.user.first_name,
                'last_name': parent.user.last_name,
                'children': parent.children.all()
            }
            html_content = render_to_string('parent_email_template.html', context)
            text_content = strip_tags(html_content)
            msg = (
                'Your Children’s Daily Update',
                text_content,
                html_content,
                settings.DEFAULT_FROM_EMAIL,
                [parent.user.email]
            )
            datatuple.append(msg)
    
    send_mass_html_mail(datatuple, fail_silently=False)


@shared_task
def send_mass_activation_email(user_ids):
    users = User.objects.filter(id__in=user_ids)
    datatuple = []
    
    for user in users:
        password = generate_password()
        user.set_password(password)
        user.save()
        activation_url = f"{frontend_url}activate/{user.activation_token}/"
        context = {'user': user, 'activation_url': activation_url, 'password': password}
        subject = 'Activate your Vunderkids Account'
        html_message = render_to_string('activation_email.html', context)
        plain_message = strip_tags(html_message)
        msg = (
            subject,
            plain_message,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        datatuple.append(msg)
    
    send_mass_html_mail(datatuple, fail_silently=False)


@shared_task
def send_activation_email(user_id, password):
    user = User.objects.get(pk=user_id)
    activation_url = f"{frontend_url}activate/{user.activation_token}/"
    context = {'user': user, 'activation_url': activation_url, 'password': password}
    subject = 'Activate your Vunderkids Account'
    html_message = render_to_string('activation_email.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    msg.send()


@shared_task
def send_password_reset_request_email(user_id):
    user = User.objects.get(pk=user_id)
    reset_password_url = f"{frontend_url}reset-password/{user.reset_password_token}/"
    context = {'user': user, 'reset_password_url': reset_password_url}
    subject = 'Password reset Vunderkids account'
    html_message = render_to_string('password_reset_request_email.html', context)
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    msg.send()



@shared_task
def check_streaks():
    now = timezone.now()
    today = now.date()

    students = Student.objects.all()
    for student in students:
        if student.last_task_completed_at:
            last_date = student.last_task_completed_at.date()
            if today > last_date and today != (last_date + timedelta(days=1)):
                student.streak = 0
                student.save()
        else:
            student.streak = 0
            student.save()
    
    # Adjust query to prefetch related user through parent
    parents = Parent.objects.all()

    for parent in parents:
        for child in parent.children.all():
            if child.last_task_completed_at:
                last_date = child.last_task_completed_at.date()
                if today > last_date and today != (last_date + timedelta(days=1)):
                    child.streak = 0
                    child.save()
            else:
                child.streak = 0
                child.save()


@shared_task
def delete_expired_subscriptions():
    subscriptions = Subscription.objects.all().select_related('user')

    inactive_subscriptions = [sub for sub in subscriptions if not sub.is_active]

    datatuple = []
    for subscription in inactive_subscriptions:
        user = subscription.user
        context = {'user': user}
        html_message = render_to_string('subscription_expired_email.html', context)
        plain_message = strip_tags(html_message)
        msg = (
            'Your subscription has expired',
            plain_message,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        datatuple.append(msg)

    # Send all emails
    send_mass_html_mail(datatuple, fail_silently=False)

    # Delete expired subscriptions
    count = len(inactive_subscriptions)
    for subscription in inactive_subscriptions:
        subscription.delete()

    return f"Deleted {count} expired subscriptions"

@shared_task
def example_task():
    for i in range(1000):
        print("HELLO")
