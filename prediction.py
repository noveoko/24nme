from subprocess import Popen
import requests

def predict_location(name, year):
    url = 'http://0.0.0.0:7546/predict'
    data = {
        'name': name,
        'year': year,
    }
    response = requests.post(url, data=data)
    return response.json()
