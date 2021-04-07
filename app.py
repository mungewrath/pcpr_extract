import pickle
from flask import Flask, request
from src.utils import sents2vectors
from src.features import Features
from src.path_report import PathologyReport
app = Flask(__name__)
app.config['MAX_CONTENT_PATH'] = '10000000' # 10MB incase of long pathology pdfs
model = pickle.load(open('model.pickle', 'rb+'))


@app.route('/', methods=['POST'])
def extract():
    print("I'm here")
    if not request.is_json:
        print("Now I'm here")
        return "Something went wrong..."
    content = request.get_json()
    raw_text, tokens = content['text'], content['tokens'].split('\n')
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

    print(f"Gleason Score Prediction:\t {report.gleason_score[0]} + {report.gleason_score[1]} = {report.gleason_score[2]}\t(Risk={report.grade})")
    return {"preds": predictions}