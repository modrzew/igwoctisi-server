# -*- coding: utf-8 *-*

players = []
games = []

class Player:
	def __init__(self, thread):
		self.thread = thread
		self.logged_in = False
		self.username = ''
		self.state = None

	def send(self, jsonObject):
		self.thread.wfile.write(jsonObject + '\n')

class Game:
	def __init__(self):
		pass
