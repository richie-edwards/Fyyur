#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, distinct
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from flask.json import jsonify
from sqlalchemy.exc import SQLAlchemyError
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# Migration
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    shows = db.relationship('Show', backref='Venue', lazy=True, cascade='all, delete-orphan')
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(800))
    website = db.Column(db.String(120))
    UniqueConstraint('name', 'city', 'state', 'address', name='unique_name_city_state_address')
    
    @property 
    def upcoming_shows(self):
      upcoming_shows = [show for show in self.shows if show.start_time > datetime.now()] #datetime.strptime(show.start_time, '%Y-%m-%d %H:%M:%S') > now]
      return upcoming_shows
    
    @property
    def num_upcoming_shows(self):
      return len(self.upcoming_shows)
    
    @property
    def past_shows(self):
      past_shows = [show for show in self.shows if show.start_time < datetime.now()]
      return past_shows
    
    @property
    def num_past_shows(self):
      return len(self.past_shows)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=True)
    shows = db.relationship('Show', backref='Artist', lazy=True)
    
    @property
    def upcoming_shows(self):
      upcoming_shows = [show for show in self.shows if show.start_time > datetime.now()]
      return upcoming_shows
      
    @property
    def num_upcoming_shows(self):      
      return len(self.upcoming_shows)
        
    @property
    def past_shows(self):
      past_shows = [show for show in self.shows if show.start_time < datetime.now()]
      
      return past_shows
      
    @property
    def num_past_shows(self):
      return len(self.past_shows)
    
    
class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  print (type(value))
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html', data=Artist.query.all())


#  Venues
#  ----------------------------------------

# Venue View
@app.route('/venues')
def venues():
  data = []
  unique_city_state = Venue.query.with_entities(Venue.city, Venue.state).distinct().all()  
  for city_state in unique_city_state:
    city = city_state[0]
    state = city_state[1]
    venues = Venue.query.filter_by(city=city, state=state).all()   
    shows = venues[0].upcoming_shows
    data.append({
      "city": city,
      "state": state,
      "venues": venues
      })

  return render_template('pages/venues.html', areas=data)

# Venue Search
@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%'))
  data = []
  for venue in venues:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": venue.num_upcoming_shows
    })
  count = len(data)
  response = {
    "count": count,
    "data": data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

# Venue View Specific
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if venue:
    data={
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": True if venue.seeking_talent in (True, 't', 'True') else False,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link if venue.image_link else "",
      "past_shows_count": venue.num_past_shows,
      "upcoming_shows_count": venue.num_upcoming_shows,
    }
  
  past_shows = []
  for show in venue.past_shows:
    artist = Artist.query.get(show.artist_id)
    past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show.start_time)
    })
    
  upcoming_shows = []
  for show in venue.upcoming_shows:
    artist = Artist.query.get(show.artist_id)
    upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": str(show.start_time)
    })

  data["past_shows"] = past_shows
  data["upcoming_shows"] = upcoming_shows
  #data = list(filter(lambda d: d['id'] == venue_id, venues))[0]
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue GET
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

#  Create Venue POST
@app.route('/venues/create', methods=['POST'])
def create_venue_submission():  
  venue = Venue()
  for field in request.form:
    if field == 'genres':
      setattr(venue, field, request.form.getlist(field))
    elif field == 'seeking_talent':
      setattr(venue, field, True if request.form.get(field) in ('y', True, 't', 'True') else False)
    else:
      setattr(venue, field, request.form.get(field))  
  
  try:
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')  
    
  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    flash('An error occurred. Show could not be listed. \n' + error)
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
    return render_template('pages/home.html')
  
  finally:
    db.session.close()
  
  return redirect(url_for('venues'))

# Update Venue (GET)
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):  
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

# Update Venue (POST)
@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)  
  for field in request.form:
    if field == 'genres':
      setattr(venue, field, request.form.getlist(field))
    elif field == 'seeking_talent':
      setattr(venue, field, True if request.form.get(field) in ('y', True, 't', 'True') else False)
    else:
      setattr(venue, field, request.form.get(field))  
  try:
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    flash('An error occurred. Show could not be listed. \n' + error)
    db.session.rollback()
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
    return render_template('pages/home.html')

  finally:
    db.session.close()
 
  return redirect(url_for('show_venue', venue_id=venue_id))

# Delete Venue
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  venue = Venue.query.get(venue_id)
  try:
    # venue.delete()
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted!')

  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')
    db.session.rollback()
    return None

  finally:
    db.session.close()
  
  return None #render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=artists)

# Artists Search (POST)
@app.route('/artists/search', methods=['POST'])
def search_artists():  
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%'+search_term+'%')).all()
  data = []
  artist_count = len(artists)
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": artist.num_upcoming_shows
    })

  response={
    "count": artist_count,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

# Artists View Specific
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  artist = Artist.query.get(artist_id)
  past_shows = []
  for show in artist.past_shows:    
    venue = Venue.query.get(show.venue_id)
    past_shows.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time
    })
  upcoming_shows = []
  for show in artist.upcoming_shows:
    venue = Venue.query.get(show.venue_id)
    upcoming_shows.append({
        "venue_id": venue.id,
        "venue_name": venue.name,
        "venue_image_link": venue.image_link,
        "start_time": show.start_time
    })
  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "seeking_venue": True if artist.seeking_venue in ('y', True, 't', 'True') else False,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link, #"https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
      "facebook_link": artist.facebook_link,
      "website_link": artist.website_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": artist.num_past_shows,
      "upcoming_shows_count": artist.num_upcoming_shows
  }
  
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

# Artists Edit (GET)
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

# Artists Edit (POST)
@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  for field in request.form:
    if field == 'genres':
      setattr(artist, field, request.form.getlist(field))
    elif field == 'seeking_venue':
      setattr(artist, field, True if request.form.get(field) in ('y', True, 't', 'True') else False)
    else:
      setattr(artist, field, request.form.get(field))  
  
  try:
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    
  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
    db.session.rollback()
    db.session.close()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

# Artists Create (GET)
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

# Artists Create (POST)
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  artist = Artist()
  for field in request.form:
    if field == 'genres':
      setattr(artist, field, request.form.getlist(field))
    elif field == 'seeking_venue':
      setattr(artist, field, True if request.form.get(field) in ('y', True, 't', 'True') else False)
    else:
      setattr(artist, field, request.form.get(field))  
  
  try:    
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
    #return render_template('pages/home.html')
  finally:
    db.session.close()
  
  return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  query = Show.query.join(
    Venue, (Venue.id == Show.venue_id)
  ).join(
      Artist, (Artist.id == Show.artist_id)
    ).with_entities(Show.venue_id, Venue.name.label('venue_name'), Show.artist_id, Artist.name.label('artist_name'), Artist.image_link, Show.start_time)
  
  data=[]
  for x in query:
    data.append({
      "venue_id": x.venue_id,
      "venue_name": x.venue_name,
      "artist_id": x.artist_id,
      "artist_name": x.artist_name,
      "artist_image_link": x.image_link,
      "start_time": x.start_time
    })
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  form.artist_id.query = Artist.query
  form.venue_id.choices = [(v.id, v.name + ' ({}, {})'.format(v.city, v.state)) for v in Venue.query]
  return render_template('forms/new_show.html', form=form)

# Show Create
@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  show = Show(
    start_time = request.form.get('start_time'),
    venue_id = request.form.get('venue_id'),
    artist_id = request.form.get('artist_id')
  )
  
  try:
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    
  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    flash(error + '\nAn error occurred. Show could not be listed.')
    db.session.rollback()
    db.session.close()
  
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
