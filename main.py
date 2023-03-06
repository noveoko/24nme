from flask import Flask, render_template, request, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, NumberRange
import logging
import os
from dotenv import load_dotenv
from ludwig.api import LudwigModel
import pandas as pd
from functools import partial
import prediction
from subprocess import Popen
import json

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='basic.log'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')

limiter = Limiter(key_func=get_remote_address)



class PredictForm(FlaskForm):
    person_name = StringField('Person Name', validators=[DataRequired()])
    year = IntegerField('Year (birth/death/alive during)', validators=[DataRequired(), NumberRange(min=1600, max=2022)])

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("1/second")
def home() -> str:
    logging.info('Rendering index.html')
    form = PredictForm()
    if form.validate_on_submit():
        # Handle form submission here
        return redirect('/predict')
    return render_template('index.html', form=form)

@app.route('/predict', methods=['POST'])
@limiter.limit("1/second")
def predict() -> str:
    person_name: str = request.form['person_name']
    year: int = int(request.form['year'])

    # perform prediction based on person_name and year
    top_5_countries_string = prediction.predict_location(person_name, year)


    with open('last_prediction.json', 'w') as fx:
        fx.write(top_5_countries_string)

    logging.info('Rendering result.html')
    return render_template('result.html', person=person_name, year=year, geolocation=top_5_countries_string)

@limiter.limit("1/second")
@app.route('/docs')
def docs():
    return render_template('docs.html')


if __name__ == '__main__':
    process = Popen(['ludwig', 'serve', '--model_path', './model', '--port', '7546'])
    process.wait()  # Wait until Popen finishes executing
    app.run()