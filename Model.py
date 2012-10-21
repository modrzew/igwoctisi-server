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
