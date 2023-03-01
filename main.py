from flask import Flask, render_template, request
import logging
from predict import random_country
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

@limiter.limit("1/second", override_defaults=False)
@app.route('/', methods=['GET', 'POST'])
def home() -> str:
    logging.info('Rendering index.html')
    return render_template('index.html')

@limiter.limit("1/second", override_defaults=False)
@app.route('/predict', methods=['POST'])
def predict() -> str:
    person_name: str = request.form['person_name']
    year: int = int(request.form['year'])

    # perform prediction based on person_name and year
    prediction: str = random_country()

    logging.info('Rendering result.html')
    return render_template('result.html', person=person_name, year=year, geolocation=prediction)


if __name__ == '__main__':
    app.run()