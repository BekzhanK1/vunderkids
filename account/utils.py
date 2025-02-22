from django.template.loader import render_to_string
from django.utils.html import strip_tags
import secrets
import pandas as pd


from account.models import Student


def render_email(first_name, last_name, current_cups, level):
    context = {
        "first_name": first_name,
        "last_name": last_name,
        "current_cups": current_cups,
        "level": level,
    }
    html_content = render_to_string("daily_email.html", context)
    text_content = strip_tags(html_content)
    return html_content, text_content


def generate_password():
    password_length = 8
    return secrets.token_urlsafe(password_length)


import boto3
from botocore.exceptions import NoCredentialsError


def get_presigned_url(bucket_name, key, expiration=3600):
    s3_client = boto3.client("s3", region_name="eu-north-1")
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expiration,
        )
        print(url)
        return url
    except NoCredentialsError:
        print("No AWS credentials found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
