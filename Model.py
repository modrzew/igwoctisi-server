# -*- coding: utf-8 *-*

players = []
games = []
last_game_id = 1


class Player:
	def __init__(self, thread):
		self.thread = thread
		self.username = ''
		self.state = None
		self.current_game = None
		self.last_message_id = 0

	def send(self, response):
		self.thread.wfile.write(response['header'] + '\n')
		if response['message']:
			self.thread.wfile.write(response['message'] + '\n')

	def get_next_message_id(self):
		self.last_message_id += 1
		return self.last_message_id


class Game:
	# States of game
	NOT_STARTED = 1

	def __init__(self):
		global last_game_id
		self.players = []
		self.id = last_game_id
		self.state = Game.NOT_STARTED
		self.name = ''
		self.map = None
		last_game_id += 1
