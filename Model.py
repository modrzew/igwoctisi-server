# -*- coding: utf-8 *-*
import json
import Communication
import Common
import threading
import time

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
		if Communication.DEBUG_MODE:
			Common.console_message('[SEND] to %s: %s' % (self.thread.request.getpeername()[0], response))
		self.thread.wfile.write(json.dumps(response['header']) + '\n')
		if response['object']:
			self.thread.wfile.write(json.dumps(response['object']) + '\n')

	def get_next_message_id(self):
		self.last_message_id += 1
		return self.last_message_id


class Game(threading.Thread):
	# States of game
	NOT_STARTED = 1
	IN_PROGRESS = 2

	def __init__(self):
		super(Game, self).__init__()
		global last_game_id
		self.players = []
		self.id = last_game_id
		self.state = Game.NOT_STARTED
		self.name = ''
		self.map = None
		self.hosting_player = None
		last_game_id += 1

	def run(self):
		self.state = Game.IN_PROGRESS
		self.round = 1
		self.round_orders = {}

		Common.console_message('Game %d started!' % self.id)

		while self.state == Game.IN_PROGRESS:
			for p in self.players:
				object_to_send = {
					'players': [pl.username for pl in self.players],
					'map': [],
					'tech': [],
					'fleetsToDeploy': 6,
					'roundTime': 300
				}
				# TODO stos rzeczy do wysłania i oczekiwanie na odpowiedź
				p.send(Common.json_message('roundStart', object_to_send, p.get_next_message_id()))
			round_time = 300
			while round_time > 0:
				Common.console_message('Game %d, round %d: %d seconds left' % (self.id, self.round, round_time))
				if len(self.round_orders) == len(self.players): # Everyone sent their orders
					break
				round_time -= 1
				time.sleep(1)
			# Assume that round has ended

			self.round += 1


class Map:
	def __init__(self, map):
		# TODO walidacja
		# Map is a JSON object passed directly from client
		self.raw_map = map

		self.name = map['name']
		# Planet - id: {name, base_units_per_turn}
		self.planets = {}
		for planet in map['planets']:
			p = {'name': planet['name'], 'baseUnitsPerTurn': int(planet['id']), 'links': [], 'planetary_system': None}
			self.planets[planet['id']] = p
		# Links
		for link in map['links']:
			self.planets[link['sourcePlanet']]['links'].append(link['targetPlanet'])
			self.planets[link['targetPlanet']]['links'].append(link['sourcePlanet'])
		# System: {name, planetsId[]}
		self.planetary_systems = {}
		psId = 1 # TODO change to ps['id'] later
		for ps in map['planetarySystems']:
			planetary_system = {'fleet_bonus': int(ps['fleetBonusPerTurn']), 'name': ps['name'], 'planets': [int(id) for id in ps['planets']]}
			self.planetary_systems[psId] = planetary_system
			psId += 1
			for planet_id in planetary_system['planets']:
				self.planets[planet_id]['planetary_system'] = psId
		# Starting data: [planetId]
		self.starting_data = [sd['planetId'] for sd in map['playerStartingData']]
