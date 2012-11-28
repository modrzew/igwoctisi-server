# -*- coding: utf-8 *-*
from sqlalchemy import *
from sqlalchemy.sql import select
import math

ENGINE = None
CONNECTION = None
USING_DATABASE = False
META = None
CONFIG = None

class Schema:
	pass

def connect():
	global CONFIG, ENGINE, CONNECTION, USING_DATABASE, META

	try:
		import Config
	except ImportError:
		raise Exception('Config module not found')

	CONFIG = Config.DATABASE
	ENGINE = create_engine('mysql://%s:%s@%s/%s' % (CONFIG['username'], CONFIG['password'], CONFIG['host'], CONFIG['database']), pool_recycle=3600*24)
	CONNECTION = ENGINE.connect()
	META = MetaData()
	USING_DATABASE = True

	Schema.users = Table('users', META, autoload=True, autoload_with=ENGINE)
	Schema.games = Table('games', META, autoload=True, autoload_with=ENGINE)
	Schema.places = Table('places', META, autoload=True, autoload_with=ENGINE)

def login(username, password):
	global CONNECTION
	s = select(['id']).where(and_(Schema.users.c.username == username, Schema.users.c.password == password)).select_from(Schema.users)
	rs = CONNECTION.execute(s)
	row = rs.fetchone()
	if row is None:
		return -1
	else:
		return row['id']

def create_game(game):
	global CONNECTION
	values = {
		'name': game.name,
	}
	ins = insert(Schema.games, values=values)
	result = CONNECTION.execute(ins)
	game.id = result.inserted_primary_key[0]


def save_game(game):
	global CONNECTION
	values = {
		'time': game.time
	}
	where = {
		'id': game.id
	}
	CONNECTION.execute(
		update(Schema.games)
		.where(Schema.games.c.id==game.id)
		.values(values)
	)
	places = game.players_lost + game.players
	places.reverse()
	for p in places:
		place = places.index(p) + 1
		places_length = len(places)
		if place <= math.ceil(places_length/2.0):
			points = int(round(game.map.points * math.pow(0.5, place)))
		else:
			points = int(round(-game.map.points * math.pow(0.5, (places_length - place + 1))))
		values = {
			'game_id': game.id,
			'user_id': p.id,
			'place': place,
			'points': int(round(points))
		}
		ins = insert(Schema.places, values)
		CONNECTION.execute(ins)
		# Update user points
		CONNECTION.execute(
			update(Schema.users)
			.where(Schema.users.c.id==p.id)
			.values({Schema.users.c.points:Schema.users.c.points+points})
		)
