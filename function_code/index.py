import json
import boto3
import random
import base64
import io
from PIL import Image
import os


def image_payload(prompt,cfg = 10, height= 1024, width = 1024, steps = 50, style_preset = "photographic"):
    payload = {
        "text_prompts": [
                    {"text": prompt},
                ],
        "cfg_scale": cfg,
        "height": height,
        "width": width,
        "steps": steps,
        "seed": random.randint(0,100000),
        "style_preset": style_preset,
    }
    payload = json.dumps(payload)
    return payload

def bedrock_endpoint(payload):
    model_id = "stability.stable-diffusion-xl-v1"
    bedrock = boto3.client(service_name='bedrock-runtime')
    response = bedrock.invoke_model(
        modelId = model_id,
                contentType = "application/json",
                accept = "application/json",
                body = payload    
    )
    response_body = json.loads(response.get("body").read())
    return response_body

# upload to s3 bucket
def upload_file_s3(path,file_name, bucket):
    object_name = file_name
    s3_client = boto3.client('s3')
    response = s3_client.upload_file(path, bucket, object_name)
    return response

# save base64 string as png with random name
def save_base64_png(base64_string):
    imgdata = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(imgdata))
    file_name = 'image-{num}.png'.format(num=random.randint(0,1000))
    path = '/tmp/'+file_name
    image.save(path)
    return path, file_name

def handler(event, context):
    body = json.loads(event.get('body', '{}'))
    #setting defult prompt if none provided
    prompt = body.get('prompt', 'Oil pipeline with rust')
    
    # create payload for Bedrock SDXL
    payload = image_payload(prompt)

    response = bedrock_endpoint(payload)

    path,file_name = save_base64_png(response["artifacts"][0]["base64"])

    upload_file_s3(path=path, file_name=file_name, bucket=os.environ['BUCKET'])

    return {
        'statusCode': 200,
        'body': json.dumps({
            'generated-text': file_name
        })
    }

if __name__ == '__main__':
    payload = image_payload('Oil pipeline with slight rust')
    response = bedrock_endpoint(payload)
    file_name = save_base64_png(response["artifacts"][0]["base64"])

