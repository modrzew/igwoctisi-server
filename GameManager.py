# -*- coding: utf-8 *-*
import Common
import Model
import Constants
import PlayerState
import threading
import time
import random
import Database
from datetime import datetime


class GameManager(threading.Thread):
	"""
	This class is used to manage a game (wow, really?)
	"""
	def __init__(self, game):
		super(GameManager, self).__init__()
		self.game = game
		self.round = 1
		self.round_commands = {}
		self.round_ready = []
		self.game_start_time = time.time()

	def run(self):
		"""
		This method runs everything, literally
		It's even called "run"
		But we call it with "GameManager.start()"
		I think it's not quite acceptable in this era that promotes equality so much, is it?
		"run" method has feelings too! It wants to be called too!
		Join now our movement at http://stoprundiscrimination.com/ and show them we're much more equal than they are!
		"""
		game = self.game
		game.state = Model.Game.IN_PROGRESS
		self.round = 1
		self.round_commands = {}
		self.round_ready = []
		self.round_fleets_to_deploy = {}

		# Do not create game entry in database if a player is autistic enough to play with themselves
		if len(game.players) > 1 and Database.USING_DATABASE:
			Database.create_game(self.game)

		for p in game.players:
			# Set 0 level tech for everyone
			game.tech[p] = {
				'offensive': 0,
				'defensive': 0,
				'economic': 0,
				'points': 0
			}
			# Set 0 for every stat for everyone
			for (k, s) in game.stats.items():
				s[p.username] = 0

		# Put everyone in place
		game.map.set_starting_positions()

		Common.console_message('Game %d started!' % game.id)

		while game.state == Model.Game.IN_PROGRESS: # As long as game is not finished!
			self.round_ready = []
			# We wait for players to be ready
			# TODO timeout
			while game.state == Model.Game.IN_PROGRESS:
				if self.has_game_ended(): # Has the game ended?
					self.game_end()
					return None
				if set(game.players).issubset(self.round_ready): # Everyone is ready!
					break # RatajException
				time.sleep(0.5)

			# Has someone lost in the previous round?
			for p in self.game.players:
				if len(p.planets) == 0:
					self.player_lost(p, True)
			# Thus, has the game ended?
			if self.has_game_ended():
				self.game_end()
				return None

			self.round_commands = {}
			round_time = Constants.ROUND_TIME
			current_map = game.map.get_current_state()
			for p in game.players:
				fleets_to_deploy = self.game.map.fleets_per_turn(p)
				self.round_fleets_to_deploy[p] = fleets_to_deploy
				object_to_send = {
					'players': [pl.username for pl in game.players],
					'map': current_map,					
					'tech': game.tech[p],					
					'fleetsToDeploy': fleets_to_deploy,
					'roundTime': round_time
				}
				p.socket.send(Common.json_message('roundStart', object_to_send, p.socket.get_next_message_id()))
			round_start_time = time.time()
			while time.time() - round_start_time < round_time and game.state == Model.Game.IN_PROGRESS:
				if self.has_game_ended(): # Has the game ended?
					self.game_end()
					return None
				if set(game.players).issubset(self.round_commands.keys()): # Everyone sent their orders
					break # RatajException
				time.sleep(0.5)
			# Assume that round has ended and we have everyone's orders
			# Zero, randomize the players!
			self.order_players()
			# First, we put them in order: deploys first, moves next
			commands = self.order_commands()
			# And now let's execute them, shall we?
			results = self.execute_commands(commands)
			# Then send the results to all players
			for p in self.game.players:
				p.socket.send(Common.json_message('roundEnd', results, p.socket.get_next_message_id()))
			# ...has someone won the game, accidentally?
			if self.has_game_ended():
				self.game_end()
				return None
			# And to the next round!
			self.round += 1

	def set_round_commands(self, player, commands):
		"""
		Sets round commands for a player
		"""
		# Check if everything can be executed
		commands_temp = {'tech': [], 'deploy': [], 'move': []}
		for c in commands:
			if not self.game.valid(player, c, True): # Invalid command
				return False

			c['sourceId'] = int(c['sourceId'])
			c['targetId'] = int(c['targetId'])
			c['fleetCount'] = int(c['fleetCount'])

			if c['type'] == 'deploy':
				commands_temp['deploy'].append(c)
			if c['type'] == 'move' or c['type'] == 'attack':
				commands_temp['move'].append(c)
			if c['type'] == 'tech':
				if not c['techType'] in [com['techType'] for com in commands_temp['tech']]: # Only 1 upgrade per turn
					commands_temp['tech'].append(c)
		# Check if player has not deployed more than they have
		if sum([c['fleetCount'] for c in commands_temp['deploy']]) > self.round_fleets_to_deploy[player]:
			return False
		self.round_commands[player] = commands_temp
		return True

	def order_players(self):
		"""
		Puts players in order (currently only random)
		"""
		p = self.game.players
		random.shuffle(p)
		self.players_order = p

	def order_commands(self):
		"""
		Puts commands in the same order self.players_order was put
		As in: 1st command for P1, 1st command for P2 (...) 2nd command for P1, 2nd command for P2 and so on
		"""
		commands = []
		# Tech
		move_while_break = False
		while not move_while_break:
			move_while_break = True # Assume that there are no orders left
			for p in self.players_order:
				if p in self.round_commands and self.round_commands[p]['tech']:
					move_while_break = False # Oh, so there are some orders
					commands.append({'player': p, 'command': self.round_commands[p]['tech'].pop(0)})
		# Deploy
		move_while_break = False
		while not move_while_break:
			move_while_break = True # Assume that there are no orders left
			for p in self.players_order:
				if p in self.round_commands and self.round_commands[p]['deploy']:
					move_while_break = False # Oh, so there are some orders
					commands.append({'player': p, 'command': self.round_commands[p]['deploy'].pop(0)})
		# Move/attack
		move_while_break = False
		while not move_while_break:
			move_while_break = True # Assume that there are no orders left
			for p in self.players_order:
				if p in self.round_commands and self.round_commands[p]['move']:
					move_while_break = False # Oh, so there are some orders
					commands.append({'player': p, 'command': self.round_commands[p]['move'].pop(0)})
		return commands

	def execute_commands(self, commands):
		"""
		Executes given commands on a world state (Map)
		"""
		results = []

		for c in commands:
			if self.has_game_ended(): # Has game already ended?
				return results
			r = self.game.execute(c['player'], c['command'])
			if r is not None: # If None, move couldn't be executed (or it was tech)
				results.append(r)

		return results

	def game_end(self):
		"""
		Ends the game
		"""
		self.game.state = Model.Game.FINISHED
		self.game.time = int(time.time() - self.game_start_time)
		for p in self.game.players:
			message = self.game_end_message()
			message['endType'] = 'gameEnd'
			p.current_game = None
			p.planets = []
			p.state = PlayerState.LoggedIn()
			p.socket.send(Common.json_message('gameEnd', message, p.socket.get_next_message_id()))
		if Database.USING_DATABASE:
			Database.save_game(self.game)
		if self.game in Model.games:
			Model.games.remove(self.game)

	def game_end_message(self):
		"""
		Prepares a gameEnd message for player (if he lost) or players (if game ended)
		"""
		places = [p.username for p in self.game.players_lost] + [p.username for p in self.game.players]
		places.reverse()
		# Put empty lists to stats
		stats = []
		for i in self.game.stats:
			tempStat = {'name': i, 'values': []}
			for p in places:
				tempStat['values'].append(self.game.stats[i][p])
			stats.append(tempStat)
		ret = {
			'places': places,
			'rounds': self.round,
			'time': int(time.time() - self.game_start_time),
			'stats': stats,
			'gameId': self.game.id
		}
		return ret

	def has_game_ended(self):
		"""
		Checks whether game has ended already
		"""
		# No players left
		if self.game.players == []:
			return True
		# Only one player remaining, in case there were others
		if len(self.game.players) == 1 and len(self.game.players_lost) > 0:
			return True

		return False

	def player_lost(self, player, send_game_end):
		"""
		Removes player from game, notifies
		"""
		player.current_game = None
		player.state = PlayerState.LoggedIn()
		player.planets = []
		self.game.players.remove(player)
		self.game.players_lost.append(player)
		del self.game.tech[player]
		for (k, p) in self.game.map.planets.items(): # Free his planets from tyranny
			if p['player'] is player:
				p['player'] = None
		t = datetime.today().strftime('%H:%M')
		if not self.has_game_ended(): # If game has ended, nobody cares about players leaving
			for p in self.game.players: # Let's notify others about player loss!
				p.socket.send(Common.json_message('gamePlayerLeft', {'username': player.username, 'time': t}, p.socket.get_next_message_id()))
		if send_game_end: # Does the player still care, or has he just... disconnected?
			message = self.game_end_message()
			message['endType'] = 'loss'
			player.socket.send(Common.json_message('gameEnd', message, player.socket.get_next_message_id()))
