# -*- coding: utf-8 *-*
from GameManager import GameManager
import Common
import Constants
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
		self.planets = []


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
		self.stats = Constants.STATS_TEMPLATE
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
			if 'techType' not in command: # Invalid command
				return False
			if command['techType'] != 'offensive' and command['techType'] != 'defensive' \
				and command['techType'] != 'economic': # Invalid tech
				return False
			# Player doesn't have enough tech points
			if self.tech[player]['points'] < Constants.TECH_COST[self.tech[player][command['techType']]]:
				return False

		return True

	def execute(self, player, command):
		"""
		Executes a command, validating it beforehand
		"""
		if self.valid(player, command, False):
			ret = {'player': player.username, 'type': command['type']}
			if command['type'] == 'deploy': # Deploy
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

				# Is it move?
				if updated_command_type == 'move':
					self.map.move(command['sourceId'], command['targetId'], command['fleetCount'])
					ret.update({
						'sourceId': command['sourceId'],
						'targetId': command['targetId'],
						'fleetCount': command['fleetCount'],
						'type': 'move'
					})

				# Or is it attack?
				if updated_command_type == 'attack':
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
				self.add_tech_points(player, -Constants.TECH_COST[self.tech[player][command['techType']]])
				return None # We return nothing, so nobody can see what others upgraded

			return ret
		else:
			return None

	def add_tech_points(self, player, points):
		"""
		Modifies player's tech points
		Points may be negative
		"""
		self.tech[player]['points'] += int(points)
		if points > 0:
			self.update_stat(player, 'techGained', points)
		elif points < 0:
			self.update_stat(player, 'techLost', points)

	def update_stat(self, player, name, value):
		"""
		Updates player's particular stat value
		Value may be negative
		"""
		self.stats[name][player.username] += value

class Map:
	def set(self, game, map):
		"""
		Sets a world to play in
		map is a JSON object passed directly from client, to be broadcasted to other players
		"""
		self.raw_map = map

		if not self.valid(self.raw_map):
			return False

		self.game = game

		self.name = map['name']
		# Planet
		self.planets = {}
		for planet in map['planets']:
			p = {'name': planet['name'], 'id': int(planet['id']), 'baseUnitsPerTurn': int(planet['baseUnitsPerTurn']),
				 'links': [], 'planetary_system': None, 'player': None, 'fleets': int(planet['baseUnitsPerTurn'])}
			self.planets[planet['id']] = p
		# Conquered planets (containing planet IDs) - for giving tech point bonus for conquering for first time
		self.planets_conquered = []
		# Links between planets
		for link in map['links']:
			self.planets[link['sourcePlanet']]['links'].append(link['targetPlanet'])
			self.planets[link['targetPlanet']]['links'].append(link['sourcePlanet'])
		# Planetary systems
		self.planetary_systems = {}
		for ps in map['planetarySystems']:
			planetary_system = {'id': ps['id'], 'fleet_bonus': int(ps['fleetBonusPerTurn']), 'name': ps['name'],
								'planets': [int(id) for id in ps['planets']]}
			self.planetary_systems[ps['id']] = planetary_system
			for planet_id in planetary_system['planets']:
				self.planets[planet_id]['planetary_system'] = ps['id']
		# Starting data (containing planet IDs)
		self.starting_data = [sd['planetId'] for sd in map['playerStartingData']]
		self.game.max_players = len(self.starting_data)

		return True

	def valid(self, raw_map):
		"""
		Checks whether map sent by the host is valid
		"""
		# TODO stub
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
		# TODO walidacja - co jeśli chce przydzielić więcej niż może
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
		atk_chance = Constants.DESTROY_CHANCE['attacker']
		def_chance = Constants.DESTROY_CHANCE['defender']

		from_planet = self.planets[from_id]
		to_planet = self.planets[to_id]

		atk_fleets = count
		def_fleets = to_planet['fleets']

		attacker = from_planet['player']
		defender = to_planet['player']

		# Upgrades
		atk_chance += Constants.UPGRADE_BONUS['offensive'] * self.game.tech[attacker]['offensive']
		def_chance += Constants.UPGRADE_BONUS['defensive'] * self.game.tech[attacker]['defensive']

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
			if defender is None and to_planet['id'] not in self.planets_conquered: # Planet is owned by nobody
				self.planets_conquered.append(to_planet['id'])
				self.game.add_tech_points(attacker, to_planet['baseUnitsPerTurn'] * Constants.TECH_POINTS_PLANET_MULTIPLIER)
			else: # Planet is owned by somebody, so they have lost it!
				self.game.update_stat(defender, 'planetsLost', 1)
			self.set_planet_owner(to_id, attacker)
			# Has the defender... lost the game?
			if defender is not None and defender.planets is []:
				self.game.manager.player_lost(defender, True)
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
				ret['sourceLeft'] = from_planet['fleets'] - (def_destroyed if atk_fleets > def_destroyed else atk_fleets)
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
		"""
		Returns current world state - all planets, their owners and their fleets
		"""
		ret = []
		for (key, p) in self.planets.items():
			ret.append({
				'planetId': p['id'],
				'player': p['player'].username if p['player'] in self.game.players else None,
				'fleets': p['fleets']
			})
		return ret

	def set_starting_positions(self):
		"""
		Puts players on random starting planets
		"""
		planets_temp = self.starting_data
		for p in self.game.players:
			planet = random.choice(planets_temp)
			self.set_planet_owner(planet, p)
			self.planets[planet]['fleets'] = 0
			self.planets_conquered.append(planet)
			planets_temp.remove(planet)

	def fleets_per_turn(self, player):
		"""
		Returns fleet count that player is able to deploy
		Also add bonus tech points for planetary systems
		"""
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
				self.game.add_tech_points(player, int(math.ceil(tech_points * Constants.TECH_POINTS_SYSTEM_MULTIPLIER)))
		fleets = int(math.ceil(fleets * (1 + Constants.UPGRADE_BONUS['economic'] * self.game.tech[player]['economic'])))
		return fleets

	def set_planet_owner(self, planet_id, player):
		"""
		Sets owner of planet to player
		"""
		if self.planets[planet_id]['player']:
			self.planets[planet_id]['player'].planets.remove(self.planets[planet_id])
		self.planets[planet_id]['player'] = player
		player.planets.append(self.planets[planet_id])