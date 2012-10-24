# -*- coding: utf-8 *-*
from GameManager import GameManager
import random

players = []
games = []
last_game_id = 1


class Player:
	def __init__(self, socket):
		self.socket = socket
		self.username = ''
		self.state = None
		self.current_game = None


class Game:
	# States of game
	NOT_STARTED = 1
	IN_PROGRESS = 2
	FINISHED = 3

	def __init__(self):
		global last_game_id
		self.players = []
		self.id = last_game_id
		self.state = Game.NOT_STARTED
		self.name = ''
		self.map = None
		self.hosting_player = None
		self.manager = GameManager(self)
		last_game_id += 1

	def valid(self, player, command):
		"""
		Checks if command is valid for player.
		command: type, sourceId, targetId, unitCount
		"""
		from_id = command['sourceId']
		to_id = command['targetId']
		count = command['fleetCount']

		# Checking the basics
		if to_id not in self.map.planets: # Wrong id
			return False
		to_planet = self.map.planets[to_id]

		# Move/Attack
		if command['type'] == 'move':
			if from_id not in self.map.planets: # Wrong id
				return False
			from_planet = self.map.planets[from_id]
			if from_planet['player'] is not player: # Player doesn't own this planet
				return False
			if to_planet not in from_planet['links']: # Planets must be linked
				return False
			if from_planet['fleets'] <= count: # At least one fleet must always stay behind
				return False

		# Deploy
		if command['type'] == 'deploy': # Deploy
			if to_planet['player'] is not player: # Player doesn't own this planet
				return False

		# Tech
		if command['type'] == 'tech': # Tech
			return False

		return True

	def execute(self, player, command):
		if self.valid(player, command):
			ret = {'player': player.username, 'type': command['type']}
			if command['type'] == 'deploy':
				self.map.deploy(command['targetId'], command['fleetCount'])
				ret.update({
					'targetId': command['targetId'],
					'fleetCount': command['fleetCount']
				})

			if command['type'] == 'move':
				if self.map.planets[command['sourceId']].player is self.map.planets[command['targetId']].player: # Move
					self.map.move(command['sourceId'], command['targetId'], command['fleetCount'])
					ret.update({
						'sourceId': command['sourceId'],
						'targetId': command['targetId'],
						'fleetCount': command['fleetCount']
					})
				else: # Attack
					pass

			return ret

class Map:
	def __init__(self, game, map):
		# TODO walidacja
		self.game = game
		# Map is a JSON object passed directly from client
		self.raw_map = map

		self.name = map['name']
		# Planet - id: {name, base_units_per_turn}
		self.planets = {}
		for planet in map['planets']:
			p = {'name': planet['name'], 'id': int(planet['id']), 'baseUnitsPerTurn': int(planet['baseUnitsPerTurn']),
				 'links': [], 'planetary_system': None, 'player': None, 'fleets': 0}
			self.planets[planet['id']] = p
		# Links
		for link in map['links']:
			self.planets[link['sourcePlanet']]['links'].append(link['targetPlanet'])
			self.planets[link['targetPlanet']]['links'].append(link['sourcePlanet'])
		# System: {name, planetsId[]}
		self.planetary_systems = {}
		for ps in map['planetarySystems']:
			planetary_system = {'id': ps['id'], 'fleet_bonus': int(ps['fleetBonusPerTurn']), 'name': ps['name'],
								'planets': [int(id) for id in ps['planets']]}
			self.planetary_systems[ps['id']] = planetary_system
			for planet_id in planetary_system['planets']:
				self.planets[planet_id]['planetary_system'] = ps['id']
		# Starting data: [planetId]
		self.starting_data = [sd['planetId'] for sd in map['playerStartingData']]

	def deploy(self, planet_id, count):
		"""
		Deploys fleets on a planet.
		planetId must correspond to planet ID in self.planets.
		"""
		self.planets[planet_id]['fleets'] += count

	def move(self, from_id, to_id, count):
		"""
		Moves fleets from one planet to another.
		from_id and to_id must correspond to planet IDs in self.planets.
		Planets must belong to the same player, and there must be a link between them.
		Fleet count on the source planet must be greater than count parameter (as 1 fleet must always stay behind).
		"""
		self.planets[from_id]['fleets'] -= count
		self.planets[to_id]['fleets'] += count

	def attack(self, from_id, to_id, count):
		"""
		Moves fleets from one planet to another, with intention of attacking.
		from_id and to_id must correspond to planet IDs in self.planets.
		Planets must belong to the same player, and there must be a link between them.
		Fleet count on the source planet must be greater than count parameter (as 1 fleet must always stay behind).
		"""
		pass

	def get_current_state(self):
		ret = []
		for (key, p) in self.planets.items():
			ret.append({
				'planetId': p['id'],
				'playerIndex': self.game.players.index(p['player']) if p['player'] in self.game.players else -1,
				'fleets': p['fleets']
			})
		return ret

	def set_starting_positions(self):
		planets_temp = self.starting_data
		for p in self.game.players:
			planet = random.choice(planets_temp)
			self.planets[planet]['player'] = p
			planets_temp.remove(planet)
