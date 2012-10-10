# -*- coding: utf-8 *-*
import Model
import Common
from datetime import datetime

# We expect request to be already validated as JSON object containing type, object and id fields

class NotLoggedIn:
	def request(self, player, request):
		# Logging in
		if request['type'] == 'login':
			if 'username' in request['object'] and 'password' in request['object']:
				player.username = request['object']['username']
				player.state = LoggedIn()
				return Common.json_ok(request['id'])
			else:
				return Common.json_error('login_failed', request['id'])
		return Common.json_error('invalid_command', request['id'])


class LoggedIn:
	def request(self, player, request):
		# Logging out
		if request['type'] == 'logout':
			player.state = NotLoggedIn()
			return Common.json_ok(request['id'])


		# Creating new game
		if request['type'] == 'game_create':
			g = Model.Game()
			g.name = request['object']['name']
			g.players.append(player)
			Model.games.append(g)
			player.state = InLobby()
			player.current_game = g
			return None


		# Listing available games
		if request['type'] == 'game_list':
			# Listing all games that have not started yet
			game_list = [{'lobbyId': g.id, 'playersCount': len(g.players)} for g in Model.games if g.state == Model.Game.NOT_STARTED]
			if not game_list:
				return Common.json_error('game_list_empty', request['id'])
			return Common.json_message('game_list', game_list, request['id'])


		# Joining a game
		if request['type'] == 'game_join':
			game_list = [g for g in Model.games if g.id == request['object']['lobbyId'] and g.state == Model.Game.NOT_STARTED]
			if not game_list:
				return Common.json_error('game_invalid_id', request['id'])
			g = game_list[0]
			# TODO error when game full
			#if len(g.players) >= g.max_players:
			#	return Common.json_error('game_full', request['id'])
			g.players.append(player)
			player.current_game = g
			player.state = InLobby()
			# Notice all players in lobby that about fresh blood
			t = datetime.today().strftime('%H:%M')
			for p in [p for p in g.players if p is not player]:
				p.send(Common.json_message('game_player_joined', {'username': p.username, 'time': t}, p.get_next_message_id()))
			return Common.json_message('game_info', {'name': g.name, 'players': [p.username for p in g.players]})

		return Common.json_error('invalid_command', request['id'])


class InLobby:
	def request(self, player, request):
		# Chatting
		if request['type'] == 'chat':
			# Object is just a string with message
			msg = request['object']['message']
			# Broadcast message to all users in lobby
			t = datetime.today().strftime('%H:%M')
			for p in player.current_game.players:
				p.send(Common.json_message('chat', {'username': player.username, 'message': msg, 'time': t}, p.get_next_message_id()))
			return None
