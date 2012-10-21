# -*- coding: utf-8 *-*
import json
import Communication
import Common
import threading
import time
from GameManager import GameManager

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
		Checks if order is valid for player.
		order: type, sourceId, targetId, unitCount
		"""
		from_id = int(command['sourceId'])
		to_id = int(command['toId'])
		count = int(command['unitCount'])

		# Checking the basics
		if from_id not in self.planets: # Wrong id
			return False
		from_planet = self.planets[from_id]
		if from_planet['player'] is not player: # Player doesn't own this planet
			return False

		# Move/Attack
		if command['type'] == 'move':
			if to_id not in self.planets: # Wrong id
				return False
			to_planet = self.planets[to_id]
			if to_planet not in from_planet['links']: # Planets must be linked
				return False
			if from_planet['fleets'] <= count: # At least one fleet must always stay behind
				return False

		# Deploy
		if command['type'] == 'deploy': # Deploy
			pass

		# Tech
		if command['type'] == 'tech': # Tech
			return False

		return True

class Map:
	def __init__(self, map):
		# TODO walidacja
		# Map is a JSON object passed directly from client
		self.raw_map = map

		self.name = map['name']
		# Planet - id: {name, base_units_per_turn}
		self.planets = {}
		for planet in map['planets']:
			p = {'name': planet['name'], 'baseUnitsPerTurn': int(planet['id']), 'links': [], 'planetary_system': None,
				 'player': None, 'fleets': 0}
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