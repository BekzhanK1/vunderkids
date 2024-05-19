from django.template.loader import render_to_string
from django.utils.html import strip_tags
import secrets

def render_email(first_name, last_name, current_xp):
    context = {
        'first_name': first_name,
        'last_name': last_name,
        'current_xp': current_xp
    }
    html_content = render_to_string('daily_email.html', context)
    text_content = strip_tags(html_content)
    return html_content, text_content


def generate_password():
    password_length = 8
    return secrets.token_urlsafe(password_length)

