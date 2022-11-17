# import pickle, os
from src.generate_pcpr import main as generate_pdf
# from src.utils import sents2vectors
# from src.features import Features
# from src.path_report import PathologyReport
# from src.send_mail import send_mail
# from src.model_wrapper import clearPathModel
import boto3
# model = clearPathModel(pickle.load(open('model.pickle', 'rb+')))

def get_credentials():
    credentials = open('credentials.txt', 'r').read().strip().split()
    return credentials


def extract_and_upload_pdf(content):
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

    report = parse_report_values(content['textractAnalysis'], content['comprehendMedicalEntities'])

    info = {'primary': str(report.gleason_score[0]),
            'secondary': str(report.gleason_score[1]),
            'total': str(report.gleason_score[2]),
            'risk': str(report.grade),
            'positive_cores': str(report.pos_cores),
            'total_cores': report.total_cores}

    email = 'matthew.unrath@parivedasolutions.com'

    filename, file_contents = generate_pdf(info, email)
    # send_mail(get_credentials(), email, filename)
    # os.remove('tmp/' + filename)  # delete file permanently

    s3 = boto3.client('s3')
    # with open("tmp/{}".format(filename), "rb") as f:
    s3.upload_fileobj(file_contents, "mungewrath-pcpr-poc", "output/pcpr/{}".format(filename))

    return {"data": info, "file": filename}

def parse_report_values(textract, comprehendMedical):
    class ReportValues:
        pass

    values = ReportValues()

    queries = [b for b in textract['Blocks'] if b['BlockType'] == 'QUERY']
    query_results = [b for b in textract['Blocks'] if b['BlockType'] == 'QUERY_RESULT']

    gleason_query = next(q for q in queries if q['Query']['Alias'] == 'GleasonScore')
    gleason_score_raw = next(r for r in query_results if r['Id'] == gleason_query['Relationships'][0]['Ids'][0])
    gleason_components = gleason_score_raw['Text'].split('=')[0]
    g1 = gleason_components.split('+')[0]
    g2 = gleason_components.split('+')[1]

    values.gleason_score = [g1, g2, int(g1) + int(g2)]
    values.grade = '1' # TODO hardcoded
    values.pos_cores = '55' # TODO hardcoded
    values.total_cores = '55' # TODO hardcoded
    return values