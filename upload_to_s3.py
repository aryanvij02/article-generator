import boto3
import os
from botocore.exceptions import ClientError
import re
import requests
from io import BytesIO

def upload_to_S3(image_url):
    """Upload an image from a URL to an S3 bucket"""
    
    bucket = 'aryan-test-1'
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION')
    )
    
    # Extract filename from URL
    original_filename = os.path.basename(image_url)
    numbers_only = re.sub(r'\D', '', original_filename)
    filename = f"image_{numbers_only}"
    s3_key = f"blog_images/{filename}"
    
    try:
        response = requests.get(image_url)
        file_content = BytesIO(response.content)
        
        # Determine the content type
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        
        # Upload to S3 with the correct content type
        s3_client.upload_fileobj(
            file_content, 
            bucket, 
            s3_key, 
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': content_type
            }
        )
        print("Uploaded to S3 successfully")
        
        url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"
        return url, True
        
    except ClientError as e:
        print("Failed S3 upload")
        print(e)
        return None, False
    except requests.RequestException as e:
        print("Failed to download image from URL")
        print(e)
        return None, False
    
    
if __name__ == "__main__":
    url = upload_to_S3("https://oaidalleapiprodscus.blob.core.windows.net/private/org-QyqXTWh9Icnrqufmkw7lwS9L/user-6VZAVGmJUHyEcuoPGlrMoqFE/img-4L98iVk2N11qOFe81HLfWPVu.png?st=2024-09-20T02%3A36%3A17Z&se=2024-09-20T04%3A36%3A17Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=d505667d-d6c1-4a0a-bac7-5c84a87759f8&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-09-19T23%3A25%3A04Z&ske=2024-09-20T23%3A25%3A04Z&sks=b&skv=2024-08-04&sig=WTUUjoBPftwMkqTgpn5ZELXnUh7uqyDQG4XqZ0jJi6Q%3D")
    print(url)