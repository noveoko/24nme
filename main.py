from flask import Flask, render_template
import logging

logging.info('Starting the application')
# your code here

app = Flask(__name__)

@app.route('/')
def home():
    logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.info('Finished running the application')
    return render_template('index.html')

    

if __name__ == '__main__':
    app.run()

