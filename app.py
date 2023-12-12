from flask import Flask, render_template, request, redirect
from config import ApiConfig
from db import db
import requests
from datetime import datetime
import pytz

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

api_config = ApiConfig()

db.init_app(app)


# Song model
class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.String(100), nullable=False)
    track_name = db.Column(db.String(100), nullable=False)
    search_count = db.Column(db.Integer, default=0)
    search_time = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_lyrics', methods=['POST'])
def generate_lyrics():
    artist_name = request.form.get('artist_name')
    track_name = request.form.get('track_name')

    if not artist_name or not track_name:
        return render_template('index.html', error='Please provide both artist and track names.')

    song = Song.query.filter_by(artist_name=artist_name, track_name=track_name).first()

    if not song:
        lyrics = get_lyrics(artist_name, track_name)
        song = Song(artist_name=artist_name, track_name=track_name)
        db.session.add(song)
    else:
        lyrics = get_lyrics(artist_name, track_name)

    if song:
        song.search_count = (song.search_count or 0) + 1
        song.search_time = datetime.utcnow().replace(tzinfo=pytz.timezone("UTC")).astimezone(pytz.timezone("EST"))
        db.session.commit()

    return render_template('index.html', artist=song.artist_name, track=song.track_name, lyrics=lyrics)

@app.route('/table_data')
def table_data():
    with app.app_context():
        all_songs = Song.query.all()
        return render_template('table_data.html', songs=all_songs)

def get_lyrics(artist_name, track_name):
    params = {
        'q_artist': artist_name,
        'q_track': track_name,
        'apikey': ApiConfig.MUSIXMATCH_API_KEY
    }

    response = requests.get(ApiConfig.BASE_URL + 'matcher.lyrics.get', params=params)
    data = response.json()

    if 'lyrics' in data['message']['body']:
        return data['message']['body']['lyrics']['lyrics_body']
    else:
        return 'Lyrics not found.'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
