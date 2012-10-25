# -*- coding: utf-8 *-*
import Common
import Model
import threading
import time
import random


class GameManager(threading.Thread):
	def __init__(self, game):
		super(GameManager, self).__init__()
		self.game = game

	def run(self):
		game = self.game
		game.state = Model.Game.IN_PROGRESS
		self.round = 1
		self.round_commands = {}

		game.map.set_starting_positions()

		Common.console_message('Game %d started!' % game.id)

		while game.state == Model.Game.IN_PROGRESS:
			self.round_commands = {}
			round_time = 300
			current_map = game.map.get_current_state()
			for p in game.players:
				object_to_send = {
					'players': [pl.username for pl in game.players],
					'map': current_map,
					'tech': [],
					'fleetsToDeploy': self.game.map.fleets_per_turn(p),
					'roundTime': round_time
				}
				# TODO stos rzeczy do wysłania i oczekiwanie na odpowiedź
				p.socket.send(Common.json_message('roundStart', object_to_send, p.socket.get_next_message_id()))
			while round_time > 0 and game.state == Model.Game.IN_PROGRESS:
				#Common.console_message('Game %d, round %d: %d seconds left' % (game.id, self.round, round_time))
				if len(self.round_commands) == len(game.players): # Everyone sent their orders
					break
				round_time -= 1
				time.sleep(1)
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

			# To the next round!
			self.round += 1

	def set_round_commands(self, player, commands):
		"""
		Set round commands for a player
		"""
		# Check if everything can be executed
		commands_temp = {'deploy': [], 'move': []}
		for c in commands:
			if not self.game.valid(player, c): # Invalid command
				return False

			c['sourceId'] = int(c['sourceId'])
			c['targetId'] = int(c['targetId'])
			c['fleetCount'] = int(c['fleetCount'])

			if c['type'] == 'deploy':
				commands_temp['deploy'].append(c)
			if c['type'] == 'move':
				commands_temp['move'].append(c)
		self.round_commands[player] = commands_temp
		return True

	def order_players(self):
		"""
		Put players in order (currently random)
		"""
		# TODO co jeśli gracz z listy poniżej jeszcze nie wysłał swoich ruchów
		p = self.game.players
		random.shuffle(p)
		self.players_order = p

	def order_commands(self):
		"""
		Put commands in the same order self.players_order was put
		As in: 1st command for P1, 1st command for P2 (...) 2nd command for P1, 2nd command for P2 and so on
		"""
		commands = []
		# Deploy
		move_while_break = False
		while not move_while_break:
			move_while_break = True # Assume that there are no orders left
			for p in self.players_order:
				if self.round_commands[p]['deploy']:
					move_while_break = False # Oh, so there are some orders
					commands.append({'player': p, 'command': self.round_commands[p]['deploy'].pop()})
		# Move/attack
		move_while_break = False
		while not move_while_break:
			move_while_break = True # Assume that there are no orders left
			for p in self.players_order:
				if self.round_commands[p]['move']:
					move_while_break = False # Oh, so there are some orders
					commands.append({'player': p, 'command': self.round_commands[p]['move'].pop()})
		return commands

	def execute_commands(self, commands):
		"""
		Execute given commands on a world state (Map)
		"""
		results = []

		for c in commands:
			r = self.game.execute(c['player'], c['command'])
			results.append(r)

		return results