import boto3
from django.conf import settings

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_avatar_to_r2(s3_client, avatar_file, current_avatar_url, file_path):
    if current_avatar_url and settings.R2_PUBLIC_URL and current_avatar_url.startswith(settings.R2_PUBLIC_URL):
        old_file_path = current_avatar_url.replace(f"{settings.R2_PUBLIC_URL.rstrip('/')}/", "")
        try:
            s3_client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=old_file_path,
            )
        except Exception as delete_error:
            print(f"Could not delete old avatar from R2: {delete_error}")

    s3_client.upload_fileobj(
        avatar_file,
        settings.AWS_STORAGE_BUCKET_NAME,
        file_path,
        ExtraArgs={"ContentType": avatar_file.content_type},
    )

    return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{file_path}"