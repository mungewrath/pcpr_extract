import json
import boto3
import sys
import io
from src.extract_logic import extract_and_upload_pdf

def lambda_handler(event, context):
    content = {}

    s3 = boto3.client('s3')
    
    textract_data_stream = io.BytesIO()
    s3.download_fileobj(event['Bucket'], event['TextractResults'], textract_data_stream)
    textract_data_stream.seek(0)
    content['textractAnalysis'] = json.load(textract_data_stream)

    comprehend_data_stream = io.BytesIO()
    s3.download_fileobj(event['Bucket'], event['ComprehendResults'], comprehend_data_stream)
    comprehend_data_stream.seek(0)
    content['comprehendMedicalEntities'] = json.load(comprehend_data_stream)

    print("Textract:")
    print(content['textractAnalysis'])

    print("Comprehend:")
    print(content['comprehendMedicalEntities'])

    result = extract_and_upload_pdf(content)

    return {
        'statusCode': 200,
        'body': result
    }

if __name__ == '__main__':
    print("hello")
    lambda_handler(sys.argv[1], sys.argv[2])