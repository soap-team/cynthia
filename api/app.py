import time, os, json
from flask import Flask, jsonify
from flask_cors import CORS, cross_origin
from celery import Celery
from datetime import timedelta
from scoring_handler import ScoringHandler
import logging
from flask.logging import default_handler

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

celery = make_celery(app)

# load config and scorer
dir_path = os.path.dirname(os.path.realpath(__file__))
with open(dir_path + '/config.json', 'r') as f:
    config = json.load(f)
logging.getLogger('mwapi').setLevel(logging.ERROR) # silence 1.19 warnings
scoring_handler = ScoringHandler(config)

# Log into scores.log
handler = logging.handlers.WatchedFileHandler('scores.log')
formatter = logging.Formatter("[%(asctime)s] %(message)s")
handler.setFormatter(formatter)
app.logger.setLevel(logging.INFO)
app.logger.info(app.import_name)
default_handler.setLevel(logging.ERROR)
app.logger.addHandler(handler)

@celery.task(serializer='json', name='process-next-task')
def score(wiki, rev_id, model, **kwargs):
    try:
        return scoring_handler.perform_scoring('https://' + wiki, str(rev_id), model, time.time())
    except Exception as e:
        app.logger.info('ERROR:' + wiki + ':' + str(rev_id) + ':' + model + ':' + str(repr(e)))
        raise score.retry(args=[wiki, rev_id, model], exc=e, countdown=2, max_retries=3, kwargs=kwargs) # retry after 2 seconds

@app.route('/scores/', methods=["GET"])
@cross_origin()
def main():
    return 'Usage: /scores/&lt;wiki&gt;/&lt;int:rev_id&gt;/&lt;model&gt;'

@app.route('/scores/<wiki>/<lang>/<int:rev_id>/<model>', methods=["GET"])
@cross_origin()
def score_lang_revision(wiki, lang, rev_id, model):
    response = jsonify({
        'error': 'Only English wikis are supported',
        'probability': -1
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route('/scores/<wiki>/<int:rev_id>/<model>', methods=["GET"])
@cross_origin()
def score_revision(wiki, rev_id, model):
    try:
        result = score.delay(wiki, rev_id, model)
        raw_response = result.wait()
        response = jsonify(raw_response)
        if raw_response['probability'] >= 0.5:
            app.logger.info(',' + wiki + ',' + str(rev_id) + ',' + model + ',' + str(raw_response['probability']))
        # else:
            # app.logger.info(',untracked,,' + model + ',' + str(raw_response['probability']))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        response = jsonify({
            'error': 'General issue: ' + str(repr(e)),
            'probability': -1
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
