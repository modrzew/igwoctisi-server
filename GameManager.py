# -*- coding: utf-8 *-*
import Common
import Model
import threading
import time


class GameManager(threading.Thread):
	def __init__(self, game):
		super(GameManager, self).__init__()
		self.game = game

	def run(self):
		game = self.game
		game.state = Model.Game.IN_PROGRESS
		self.round = 1
		self.round_commands = {}

		Common.console_message('Game %d started!' % game.id)

		while game.state == Model.Game.IN_PROGRESS:
			round_time = 30
			for p in game.players:
				object_to_send = {
					'players': [pl.username for pl in game.players],
					'map': [],
					'tech': [],
					'fleetsToDeploy': 6,
					'roundTime': round_time
				}
				# TODO stos rzeczy do wysłania i oczekiwanie na odpowiedź
				p.socket.send(Common.json_message('roundStart', object_to_send, p.socket.get_next_message_id()))
			while round_time > 0 and game.state == Model.Game.IN_PROGRESS:
				Common.console_message('Game %d, round %d: %d seconds left' % (game.id, self.round, round_time))
				if len(self.round_commands) == len(game.players): # Everyone sent their orders
					break
				round_time -= 1
				time.sleep(1)
			# Assume that round has ended

			self.round += 1

	def set_round_commands(self, player, commands):
		# Check if everything can be executed
		for c in commands:
			if not self.game.valid(player, c):
				return False
		# If so, set it as player's commands
		self.round_commands[player] = commands
