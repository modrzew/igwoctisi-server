# -*- coding: utf-8 *-*
import json

players = []
games = []
last_game_id = 1


class Player:
	def __init__(self, thread):
		self.thread = thread
		self.username = ''
		self.state = None
		self.current_game = None
		self.last_message_id = 65535

	def send(self, response):
		self.thread.wfile.write(json.dumps(response['header']) + '\n')
		if response['object']:
			self.thread.wfile.write(json.dumps(response['object']) + '\n')

	def get_next_message_id(self):
		self.last_message_id += 1
		return self.last_message_id


class Game:
	# States of game
	NOT_STARTED = 1

	def __init__(self):
		global last_game_id
		self.players = []
		self.id = last_game_id
		self.state = Game.NOT_STARTED
		self.name = ''
		self.map = None
		self.hosting_player = None
		last_game_id += 1


class Map:
	def __init__(self):
		# Planet: {id, name, base_units_per_turn}
		self.planets = []
		# Link: {source, target}
		self.links = []
		# System: {name, planetsId[]}
		self.systems = []
		# Starting data: [planetId]
		self.starting_data = []
