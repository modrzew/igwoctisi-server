# -*- coding: utf-8 *-*

users = []
games = []

class User:
	def __init__(self, thread):
		self.thread = thread
		self.logged_in = False
		self.username = ''

	def send(self, jsonObject):
		self.thread.wfile.write(jsonObject)

class Game:
	def __init__(self):
		pass