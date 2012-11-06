# -*- coding: utf-8 *-*
from GameManager import GameManager
import Common
import random
import math

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
		self.players_lost = []
		self.id = last_game_id
		self.state = Game.NOT_STARTED
		self.name = ''
		self.map = None
		self.tech = {}
		self.stats = {
			'techGained': {},
			'techSpent': {},
			'planetsConquered': {},
			'planetsLost': {},
			'systemsConquered': {},
			'systemsLost': {},
			'fleetsDeployed': {},
			'fleetsDestroyed': {},
			'fleetsLost': {},
			'moveCount': {}
		}
		self.max_players = 0
		self.hosting_player = None
		self.manager = GameManager(self)
		last_game_id += 1

	def valid(self, player, command, is_precheck):
		"""
		Checks if command is valid for player.
		command: type, sourceId, targetId, unitCount
		is_precheck: checking only if commands are valid, to send "gameInvalidCommand" to player
		"""
		from_id = command['sourceId']
		to_id = command['targetId']
		count = command['fleetCount']

		# Checking the basics
		if to_id not in self.map.planets: # Wrong id
			return False
		to_planet = self.map.planets[to_id]

		# Move
		if command['type'] == 'move':
			if from_id not in self.map.planets: # Wrong id
				return False
			from_planet = self.map.planets[from_id]
			if from_planet['player'] is not player: # Player doesn't own this planet
				return False
			if to_planet['id'] not in from_planet['links']: # Planets must be linked
				return False
			if not is_precheck:
				if from_planet['fleets'] <= count: # At least one fleet must always stay behind
					return False

		# Attack
		if command['type'] == 'attack':
			if from_id not in self.map.planets: # Wrong id
				return False
			from_planet = self.map.planets[from_id]
			if from_planet['player'] is not player: # Player doesn't own this planet
				return False
			if to_planet['id'] not in from_planet['links']: # Planets must be linked
				return False
			if not is_precheck:
				if from_planet['fleets'] <= count: # At least one fleet must always stay behind
					return False

		# Deploy
		if command['type'] == 'deploy': # Deploy
			if to_planet['player'] is not player: # Player doesn't own that planet
				return False

		# Tech
		if command['type'] == 'tech': # Tech
			if 'techType' not in command:
				return False
			if 'techType' != 'offensive' and'techType' != 'defensive' and'techType' != 'economic':
				return False
			if not is_precheck:
				pass
				# TODO sprawdzanie, czy jest odpowiednia liczba punktow na zakup technologii

		return True

	def execute(self, player, command):
		if self.valid(player, command, False):
			ret = {'player': player.username, 'type': command['type']}
			if command['type'] == 'deploy':
				self.map.deploy(command['targetId'], command['fleetCount'])
				ret.update({
					'targetId': command['targetId'],
					'fleetCount': command['fleetCount']
				})

			# Maybe, in the course of time, target planed changed its owner
			# So it may no longer be an attack, but just a move
			if command['type'] == 'move' or command['type'] == 'attack':
				if self.map.planets[command['sourceId']]['player'] is self.map.planets[command['targetId']]['player']:
					updated_command_type = 'move'
				else:
					updated_command_type = 'attack'

				if updated_command_type == 'move':
					self.map.move(command['sourceId'], command['targetId'], command['fleetCount'])
					ret.update({
						'sourceId': command['sourceId'],
						'targetId': command['targetId'],
						'fleetCount': command['fleetCount'],
						'type': 'move'
					})

				if updated_command_type == 'attack': # Attack
					result = self.map.attack(command['sourceId'], command['targetId'], command['fleetCount'])
					ret.update({
						'sourceId': command['sourceId'],
						'targetId': command['targetId'],
						'fleetCount': command['fleetCount'],
						'type': 'attack'
					})
					ret.update(result)

			if command['type'] == 'tech': # Tech
				self.tech[player][command['techType']] += 1
				# TODO odejmowanie punktów za technologię
				return None # We return nothing, so nobody can see what others upgraded

			return ret
		else:
			return None

	def add_tech_points(self, player, points):
		self.tech[player]['points'] += int(points)
		if points > 0:
			self.update_stat(player, 'techGained', points)
		elif points < 0:
			self.update_stat(player, 'techLost', points)

	def update_stat(self, player, name, value):
		self.stats[name][player.username] += value

class Map:
	def set(self, game, map):
		# Map is a JSON object passed directly from client
		self.raw_map = map

		if not self.valid(self.raw_map):
			return False

		self.game = game

		self.name = map['name']
		# Planet - id: {name, base_units_per_turn}
		self.planets = {}
		for planet in map['planets']:
			p = {'name': planet['name'], 'id': int(planet['id']), 'baseUnitsPerTurn': int(planet['baseUnitsPerTurn']),
				 'links': [], 'planetary_system': None, 'player': None, 'fleets': int(planet['baseUnitsPerTurn'])}
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
		self.game.max_players = len(self.starting_data)

		return True

	def valid(self, raw_map):
		if 'planets' not in raw_map:
			return False
		if 'links' not in raw_map:
			return False
		if 'planetarySystems' not in raw_map:
			return False
		if 'playerStartingData' not in raw_map:
			return False
		return True

	def deploy(self, planet_id, count):
		"""
		Deploys fleets on a planet.
		planetId must correspond to planet ID in self.planets.
		"""
		self.planets[planet_id]['fleets'] += count
		self.game.update_stat(self.planets[planet_id]['player'], 'fleetsDeployed', count)

	def move(self, from_id, to_id, count):
		"""
		Moves fleets from one planet to another.
		from_id and to_id must correspond to planet IDs in self.planets.
		Planets must belong to the same player, and there must be a link between them.
		Fleet count on the source planet must be greater than count parameter (as 1 fleet must always stay behind).
		"""
		self.planets[from_id]['fleets'] -= count
		self.planets[to_id]['fleets'] += count
		self.game.update_stat(self.planets[from_id]['player'], 'moveCount', 1)

	def attack(self, from_id, to_id, count):
		"""
		Moves fleets from one planet to another, with intention of attacking.
		from_id and to_id must correspond to planet IDs in self.planets.
		Planets must belong to the same player, and there must be a link between them.
		Fleet count on the source planet must be greater than count parameter (as 1 fleet must always stay behind).
		"""

		ret = {}

		# Chances to destroy one fleet
		atk_chance = 0.6
		def_chance = 0.7

		from_planet = self.planets[from_id]
		to_planet = self.planets[to_id]

		atk_fleets = count
		def_fleets = to_planet['fleets']

		attacker = from_planet['player']
		defender = to_planet['player']

		# "Ideal" battle without luck factor
		atk_destroyed_ideal = atk_chance * atk_fleets
		def_destroyed_ideal = def_chance * def_fleets
		# "Real" battle with luck factor
		atk_destroyed_real = 0
		for i in range(atk_fleets):
			rnd = random.random()
			if rnd <= atk_chance:
				atk_destroyed_real += 1
		def_destroyed_real = 0
		for i in range(def_fleets):
			rnd = random.random()
			if rnd <= def_chance:
				def_destroyed_real += 1
		# Average + weightening
		atk_destroyed = Common.weighted_round((atk_destroyed_real + atk_destroyed_ideal) / 2.0)
		def_destroyed = Common.weighted_round((def_destroyed_real + def_destroyed_ideal) / 2.0)

		atk_won = atk_fleets > def_destroyed and def_fleets <= atk_destroyed
		if atk_won: # Attacker won!
			ret['sourceLeft'] = from_planet['fleets'] - atk_fleets
			from_planet['fleets'] -= atk_fleets
			ret['targetLeft'] = atk_fleets - def_destroyed
			to_planet['fleets'] = atk_fleets - def_destroyed
			ret['attackerLosses'] = def_destroyed
			ret['defenderLosses'] = def_fleets
			ret['targetOwnerChanged'] = True
			ret['targetOwner'] = attacker.username
			self.game.update_stat(attacker, 'planetsConquered', 1)
			# Should we give attacker some tech points?
			if defender is None: # Planet is owned by nobody
				self.game.add_tech_points(attacker, to_planet['baseUnitsPerTurn'] * 3)
			else: # Planet is owned by somebody, so they have lost it!
				self.game.update_stat(defender, 'planetsLost', 1)
			to_planet['player'] = attacker
		else: # Defender won!
			ret['targetOwnerChanged'] = False
			if atk_fleets <= def_destroyed and def_fleets <= atk_destroyed: # Both sides left with 0
				ret['attackerLosses'] = atk_fleets
				ret['defenderLosses'] = def_fleets - 1
				ret['sourceLeft'] = from_planet['fleets'] - atk_fleets
				ret['targetLeft'] = 1
				from_planet['fleets'] -= atk_fleets
				to_planet['fleets'] = 1
			else:
				ret['attackerLosses'] = def_destroyed if atk_fleets > def_destroyed else atk_fleets
				ret['defenderLosses'] = atk_destroyed if def_fleets > atk_destroyed else def_fleets
				ret['sourceLeft'] = from_planet['fleets'] - def_destroyed
				ret['targetLeft'] = to_planet['fleets'] - atk_destroyed
				from_planet['fleets'] -= def_destroyed
				to_planet['fleets'] -= atk_destroyed

		self.game.update_stat(attacker, 'moveCount', 1)
		self.game.update_stat(attacker, 'fleetsDestroyed', ret['defenderLosses'])
		self.game.update_stat(attacker, 'fleetsLost', ret['attackerLosses'])
		if defender is not None:
			self.game.update_stat(defender, 'fleetsDestroyed', ret['attackerLosses'])
			self.game.update_stat(defender, 'fleetsLost', ret['defenderLosses'])

		return ret

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
			self.planets[planet]['fleets'] = 0
			planets_temp.remove(planet)

	def fleets_per_turn(self, player):
		fleets = 0
		player_planets = []
		for (key, p) in self.planets.items():
			if p['player'] is player:
				fleets += p['baseUnitsPerTurn']
				player_planets.append(key)
		for (key, ps) in self.planetary_systems.items():
			if set(ps['planets']).issubset(player_planets):
				fleets += ps['fleet_bonus']
				tech_points = 0
				for index in ps['planets']:
					tech_points += self.planets[index]['baseUnitsPerTurn']
				self.game.add_tech_points(player, int(math.ceil(tech_points / 5.0)))
		return fleets
