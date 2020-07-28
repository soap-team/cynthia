import time, os, json
from flask import Flask, jsonify
from celery import Celery
from datetime import timedelta
from scoring_handler import ScoringHandler
import logging

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
celery = make_celery(app)

# load config and scorer
dir_path = os.path.dirname(os.path.realpath(__file__))
with open(dir_path + '/config.json', 'r') as f:
    config = json.load(f)
logging.getLogger('mwapi').setLevel(logging.ERROR) # silence 1.19 warnings
scoring_handler = ScoringHandler(config)

@celery.task()
def score(wiki, rev_id, model):
    return scoring_handler.perform_scoring('https://' + wiki, str(rev_id), model, time.time())

@app.route('/scores/', methods=["GET"])
def main():
    return 'Usage: /scores/<wiki>/<int:rev_id>/<model>'

@app.route('/scores/<wiki>/<int:rev_id>/<model>', methods=["GET"])
def score_revision(wiki, rev_id, model):
    print()
    result = score.delay(wiki, rev_id, model)
    return jsonify(result.wait())