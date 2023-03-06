import sqlite3
import requests

# Initialize SQLite database
conn = sqlite3.connect('cache.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS predictions (name TEXT, year TEXT, location TEXT)')

def predict_location(name, year):
    name, year = [str(a) for a in [name,year]]
    # Check if input has been run before
    c.execute('SELECT location FROM predictions WHERE name = ? AND year = ?', (name, year))
    result = c.fetchone()
    if result is not None:
        return result[0]
    
    # If input has not been run before, make prediction and store result in cache
    url = 'http://localhost:7546/predict'
    data = {
        'name': name,
        'year': year,
    }
    response = requests.post(url, data=data)
    location = response.json()
    
    top_5_best_matches = str(get_top_locations(location))

    try:
        #update cache

        c.execute('INSERT INTO predictions VALUES (?, ?, ?)', (name, year, top_5_best_matches))
        conn.commit()
    except sqlite3.InterfaceError as ae:
        print(ae, top_5_best_matches)
    return top_5_best_matches



def get_top_locations(data):
    # Get the list of probabilities
    probabilities = data['location_probabilities']
    
    # Get the list of location names
    locations = data['location_predictions'].split(',')
    
    # Create a dictionary of location names and probabilities
    location_prob_dict = dict(zip(locations, probabilities))
    
    # Sort the dictionary by probability and get the top 5 locations
    top_locations = sorted(location_prob_dict, key=lambda k: location_prob_dict[k], reverse=True)[:5]
    
    return top_locations