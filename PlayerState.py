# -*- coding: utf-8 *-*
import Model
import Common
import Database
from datetime import datetime
import random

# Each class (state) must have request(player, request) method and disconnect(player) method
# We expect request to be already validated as JSON object containing type, object and id fields

class Disconnected:
	def request(self, player, request):
		return None

	def disconnect(self, player):
		player.state = Disconnected()


class NotLoggedIn:
	def request(self, player, request):
		# Logging in
		if request['type'] == 'login':
			if 'username' not in request['object'] or 'password' not in request['object']:
				return Common.json_error('invalidParameters', request['id'])
			if request['object']['username'] in [p.username for p in Model.players]:
				return Common.json_error('loginFailed', request['id'])
			player_id = 0
			if Database.USING_DATABASE:
				player_id = Database.login(request['object']['username'], request['object']['password'])
				if player_id == -1:
					return Common.json_error('loginFailed', request['id'])
			player.id = player_id
			player.username = request['object']['username']
			player.state = LoggedIn()
			Common.console_message('%s logged in as %s (%d)' % (player.socket.request.getpeername()[0], player.username, player.id))
			return Common.json_ok(request['id'])

		return Common.json_error('invalidCommand', request['id'])

	def disconnect(self, player):
		player.state = Disconnected()


class LoggedIn:
	def request(self, player, request):
		# Logging out
		if request['type'] == 'logout':
			player.state = NotLoggedIn()
			return Common.json_ok(request['id'])


		# Creating new game
		if request['type'] == 'gameCreate':
			if 'name' not in request['object'] or 'map' not in request['object']:
				return Common.json_error('invalidParameters', request['id'])
			g = Model.Game()
			map = Model.Map()
			if not map.set(g, request['object']['map']):
				return Common.json_error('gameCreateFailed', request['id'])
			g.name = request['object']['name']
			g.map = map
			g.players.append(player)
			g.hosting_player = player
			Model.games.append(g)
			player.state = InLobby()
			player.current_game = g
			Common.console_message('%s created game "%s" (#%d)' % (player.username, g.name, g.id))
			return Common.json_ok(request['id'])


		# Listing available games
		if request['type'] == 'gameList':
			# Listing all games that have not started yet
			game_list = [{'lobbyId': g.id, 'name': g.name, 'playersCount': len(g.players)} for g in Model.games if g.state == Model.Game.NOT_STARTED]
			Common.console_message('%s listed for available games (%d found)' % (player.username, len(game_list)))
			return Common.json_message('gameList', game_list, request['id'])


		# Joining a game
		if request['type'] == 'gameJoin':
			if 'lobbyId' not in request['object']:
				return Common.json_error('invalidParameters', request['id'])
			game_list = [g for g in Model.games if g.id == request['object']['lobbyId'] and g.state == Model.Game.NOT_STARTED]
			if not game_list: # Game not found
				return Common.json_error('gameInvalidId', request['id'])
			g = game_list[0]
			if len(g.players) >= g.max_players: # Game full
				return Common.json_error('gameFull', request['id'])
			g.players.append(player)
			player.current_game = g
			player.state = InLobby()
			# Notify all players in lobby about fresh blood
			t = datetime.today().strftime('%H:%M')
			Common.console_message('%s joined the game "%s" (#%d)' % (player.username, g.name, g.id))
			for p in [p for p in g.players if p is not player]:
				p.socket.send(Common.json_message('gamePlayerJoined', {'username': player.username, 'time': t}, p.socket.get_next_message_id()))
			return Common.json_message('gameInfo', {'name': g.name, 'players': [p.username for p in g.players]}, request['id'])

		return Common.json_error('invalidCommand', request['id'])

	def disconnect(self, player):
		player.state = Disconnected()


class InLobby:
	# What to do when one player leaves/disconnects (notify everyone, or kick them)
	def player_leave(self, player):
		g = player.current_game
		if g.hosting_player is player: # If host leaves, kick everyone out of the game
			for p in [p for p in g.players if p is not player]:
				p.socket.send(Common.json_message('gameKick', None, p.socket.get_next_message_id()))
				p.current_game = None
				p.state = LoggedIn()
			Model.games.remove(g)
			del g
		else:
			g.players.remove(player)
			# Notify all players in lobby about their loss
			t = datetime.today().strftime('%H:%M')
			for p in g.players:
				p.socket.send(Common.json_message('gamePlayerLeft', {'username': player.username, 'time': t}, p.socket.get_next_message_id()))
			player.current_game = None

	def request(self, player, request):
		# Chatting
		if request['type'] == 'chat':
			if 'message' not in request['object']:
				return Common.json_error('invalidParameters', request['id'])
			# Object is just a string with message
			msg = request['object']['message']
			# Broadcast message to all users in lobby
			t = datetime.today().strftime('%H:%M')
			Common.console_message('In "%s" (#%d), %s chatted: %s' % (player.current_game.name, player.current_game.id, player.username, msg))
			for p in player.current_game.players:
				p.socket.send(Common.json_message('chat', {'username': player.username, 'message': msg, 'time': t}, p.socket.get_next_message_id()))
			return None


		# Leaving the game
		if request['type'] == 'gameLeave':
			Common.console_message('%s left the game "%s" (#%d)' % (player.username, player.current_game.name, player.current_game.id))
			self.player_leave(player)
			player.state = LoggedIn()
			return None


		# Kicking player out of the lobby
		if request['type'] == 'gamePlayerKick':
			if 'username' not in request['object']:
				return Common.json_error('invalidParameters', request['id'])
			g = player.current_game
			if g.hosting_player is not player: # Is kicking player the host?
				return Common.json_error('gameKickFailed', request['id'])
			if player.username == request['object']['username']: # You can't kick yourself, can you?
				return Common.json_error('gameKickFailed', request['id'])
			p = [p for p in g.players if p.username == request['object']['username']]
			if not p: # Player not found in game
				return Common.json_error('gameKickFailed', request['id'])
			p = p[0]
			Common.console_message('%s was kicked out of the game "%s" (#%d)' % (p.username, g.name, g.id))
			# Notify the others about sudden leave, and the one kicked about... well, being kicked
			player.socket.send(Common.json_ok(request['id']))
			t = datetime.today().strftime('%H:%M')
			for p2 in g.players:
				if p2 is p:
					p2.socket.send(Common.json_message('gameKick', None, p2.socket.get_next_message_id()))
				else:
					p2.socket.send(Common.json_message('gamePlayerKicked', {'username': p.username, 'time': t}, p2.socket.get_next_message_id()))
			p.current_game = None
			g.players.remove(p)
			p.state = LoggedIn()
			return None


		# Starting the game
		if request['type'] == 'gameStart':
			g = player.current_game
			if g.hosting_player is not player: # Is kicking player the host?
				return Common.json_error('gameStartFailed', request['id'])
			for p in g.players:
				if p is player:
					p.socket.send(Common.json_message('gameStarted', None, request['id']))
				else:
					p.socket.send(Common.json_message('gameStart', {'map': g.map.raw_map}, p.socket.get_next_message_id()))
				p.state = InGame()
			# Run Game thread
			g.manager.start()
			return None

		return Common.json_error('invalidCommand', request['id'])

	def disconnect(self, player):
		self.player_leave(player)
		player.state = Disconnected()


class InGame:
	def request(self, player, request):
		# Leaving the game
		if request['type'] == 'gameLeave':
			Common.console_message('%s left the game "%s" (#%d)' % (player.username, player.current_game.name, player.current_game.id))
			player.current_game.manager.player_lost(player, True)
			player.state = LoggedIn()
			return None

		# Signaling "I am ready!"
		if request['type'] == 'ready':
			gm = player.current_game.manager
			if player in gm.round_ready:
				error_code = ['fuckYou', 'WOT', '(o,o) WAT.']
				return Common.json_error(random.choice(error_code), request['id'])
			gm.round_ready.append(player)
			return Common.json_ok(request['id'])

		# Sending moves list
		if request['type'] == 'commands':
			gm = player.current_game.manager
			if player in gm.round_commands:
				return Common.json_error('commandsAlreadySent', request['id'])
			if not gm.set_round_commands(player, request['object']):
				return Common.json_error('gameInvalidCommand', request['id'])
			return Common.json_ok(request['id'])

		# Chatting
		if request['type'] == 'chat':
			if 'message' not in request['object']:
				return Common.json_error('invalidParameters', request['id'])
			msg = request['object']['message']
			# Broadcast message to all users in game
			t = datetime.today().strftime('%H:%M')
			Common.console_message('In "%s" (#%d), %s chatted: %s' % (player.current_game.name, player.current_game.id, player.username, msg))
			for p in player.current_game.players:
				p.socket.send(Common.json_message('chat', {'username': player.username, 'message': msg, 'time': t}, p.socket.get_next_message_id()))
			return None

		return Common.json_error('invalidCommand', request['id'])

	def disconnect(self, player):
		player.current_game.manager.player_lost(player, False)
		player.state = Disconnected()
