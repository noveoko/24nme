# app.py
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap

app = Flask(__name__)
Bootstrap(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        # Here you would typically call a function to determine the probable countries of origin based on the name
        countries = ['Germany', 'Poland', 'Ireland', 'Israel']  # Placeholder
        return render_template('result.html', name=name, countries=countries)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
