# import pickle, os
from io import BytesIO
import os
from src.generate_pcpr import main as generate_pdf
# from src.utils import sents2vectors
# from src.features import Features
# from src.path_report import PathologyReport
# from src.send_mail import send_mail
# from src.model_wrapper import clearPathModel
import boto3
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileMerger, PdfFileReader

def get_credentials():
    credentials = open('credentials.txt', 'r').read().strip().split()
    return credentials


def extract_and_upload_pdf(original_file_path, content):
    # Old model prediction
    # raw_text, tokens, email = content['text'], content['tokens'].split('\n'), content['email'].strip()
    # # we need to make sentence vectors to pass into model
    # vecs = sents2vectors(tokens)
    # sentence_features = [Features(vecs[sentence_index]).get_feats() for sentence_index in vecs]
    # # predict attributes from features
    # predictions = model.predict(sentence_features)
    #
    # report = PathologyReport(None, vecs, raw_text=raw_text)
    # report.predictions = predictions
    # report.realize_predictions()
    # report.populate_regions()
    # report.region_resolution()
    # report.stratify()

    bucket_name = "mungewrath-pcpr-poc"

    report = parse_report_values(content['textractAnalysis'], content['comprehendMedicalEntities'])

    info = {'primary': str(report.gleason_score[0]),
            'secondary': str(report.gleason_score[1]),
            'total': str(report.gleason_score[2]),
            'risk': str(report.grade),
            'positive_cores': str(report.pos_cores),
            'total_cores': report.total_cores,
            'cancer_dx': report.cancer_dx }

    email = 'matthew.unrath@parivedasolutions.com'

    filename, file_contents = generate_pdf(info, email)
    # send_mail(get_credentials(), email, filename)
    # os.remove('tmp/' + filename)  # delete file permanently

    s3 = boto3.client('s3')

    if is_pdf(original_file_path):
        output = PdfFileMerger()

        original_file_contents = BytesIO()
        s3.download_fileobj(bucket_name, original_file_path, original_file_contents)

        original_pdf = PdfFileReader(original_file_contents)
        new_pdf = PdfFileReader(file_contents)

        for pdf in [original_pdf, new_pdf]:
            output.append(pdf)

        file_contents = BytesIO()

        output.write(file_contents)
        output.close()
        file_contents.seek(0)

    # with open("tmp/{}".format(filename), "rb") as f:
    s3.upload_fileobj(file_contents, bucket_name, "output/pcpr/{}".format(filename))

    return {"data": info, "file": filename}

def is_pdf(file_path):
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext == ".pdf"

def parse_report_values(textract, comprehendMedical):
    class ReportValues:
        pass

    values = ReportValues()

    queries = [b for b in textract['Blocks'] if b['BlockType'] == 'QUERY']
    query_results = [b for b in textract['Blocks'] if b['BlockType'] == 'QUERY_RESULT']

    gleason_query = next(q for q in queries if q['Query']['Alias'] == 'GleasonScore')
    gleason_score_raw = next(r for r in query_results if r['Id'] == gleason_query['Relationships'][0]['Ids'][0])
    gleason_components = gleason_score_raw['Text'].split('=')[0]
    g1 = int(gleason_components.split('+')[0])
    g2 = int(gleason_components.split('+')[1])

    cancer_query = next(q for q in queries if q['Query']['Alias'] == 'CancerType')
    cancer_dx = next(r for r in query_results if r['Id'] == cancer_query['Relationships'][0]['Ids'][0])['Text']

    values.gleason_score = [g1, g2, g1 + g2]
    values.grade = calculate_grade(g1, g2, g1 + g2)
    values.pos_cores = '55' # TODO hardcoded
    values.total_cores = '55' # TODO hardcoded
    values.cancer_dx = cancer_dx
    return values

def calculate_grade(primary, secondary, total, simple=True):
        """
        Simple stratification is from the PCPR, not most recent prostate cancer schema
        """
        if simple:
            if total <= 6:
                return 1
            elif total > 7:
                return 3
            else:
                return 2
        if total == 0:
            if primary + secondary == 0:
                return 0
            else:
                total = primary + secondary

        # calculate grade
        if total <= 6:
            return 1
        elif total == 7:
            if primary == 3 and secondary == 4:
                return 2
            elif primary == 4 and secondary == 3:
                return 3
            else:
                # return worst case
                debug = True
                return 3
        elif total == 8:
            return 4
        elif total >= 9:
            return 5
        return None