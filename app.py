import pickle, os
from src.generate_pcpr import main as generate_pdf
from flask import Flask, request
from src.utils import sents2vectors
from src.features import Features
from src.path_report import PathologyReport
from src.send_mail import send_mail
from src.model_wrapper import clearPathModel
app = Flask(__name__)
app.config['MAX_CONTENT_PATH'] = '10000000' # 10MB incase of long pathology pdfs
model = clearPathModel(pickle.load(open('model.pickle', 'rb+')))

def get_credentials():
    credentials = open('credentials.txt', 'r').read().strip().split()
    return credentials



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
    raw_text, tokens, email = content['text'], content['tokens'].split('\n'), content['email'].strip()
    # we need to make sentence vectors to pass into model
    vecs = sents2vectors(tokens)
    sentence_features = [Features(vecs[sentence_index]).get_feats() for sentence_index in vecs]
    # predict attributes from features
    predictions = model.predict(sentence_features)

    report = PathologyReport(None, vecs, raw_text=raw_text)
    report.predictions = predictions
    report.realize_predictions()
    report.populate_regions()
    report.region_resolution()
    report.stratify()
    info = {'primary': str(report.gleason_score[0]),
            'secondary': str(report.gleason_score[1]),
            'total': str(report.gleason_score[2]),
            'risk': str(report.grade),
            'positive_cores': str(report.pos_cores),
            'total_cores': report.total_cores}


    filename = generate_pdf(info, email)
    send_mail(get_credentials(), email, filename)
    os.remove('tmp/' + filename)  # delete file permanently
    return {"data": info, "file": filename}


if __name__=='__main__':
    app.run(host='0.0.0.0', port=5001)
