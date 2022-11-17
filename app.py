from src.extract_logic import extract_and_upload_pdf
from flask import Flask, request

app = Flask(__name__)
app.config['MAX_CONTENT_PATH'] = '10000000' # 10MB incase of long pathology pdfs

@app.route('/', methods=['POST'])
def extract():
    """
    Expects:
        1 - Preprocessed, de-identified text
        2 - an email address
    :return:
    """
    if not request.is_json:
        return "Something went wrong..."
    content = request.get_json()

    return extract_and_upload_pdf(content)

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5001)
