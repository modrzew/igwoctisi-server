# -*- coding: utf-8 *-*

players = []
games = []
lastGameId = 1


class Player:
	def __init__(self, thread):
		self.thread = thread
		self.username = ''
		self.state = None
		self.currentGame = None

	def send(self, jsonObject):
		self.thread.wfile.write(jsonObject)


class Game:
	# States of game
	NOT_STARTED = 1

	def __init__(self):
		global lastGameId
		self.players = []
		self.id = lastGameId
		self.state = Game.NOT_STARTED
		lastGameId += 1
