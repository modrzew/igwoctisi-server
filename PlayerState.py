# -*- coding: utf-8 *-*
import Model
import Common

# We expect request to be already validated as JSON object containing type, object and id fields

class NotLoggedIn:
	def request(self, user, request):
		# First of all, maybe they want to login
		if request['type'] == 'login':
			if 'username' in request['object'] and 'password' in request['object']:
				user.username = request['object']['username']
				user.state = LoggedIn()
				return None
			else:
				return Common.json_error('not_logged_in', request['id'])
		return Common.json_error('invalid_command', request['id'])


class LoggedIn:
	def request(self, user, request):
		# Creating new game
		if request['type'] == 'game_create':
			g = Model.Game()
			g.players.append(user)
			Model.games.append(g)
			user.state = InLobby()
			user.current_game = g
			return None


		# Listing available games
		if request['type'] == 'game_list':
			# Listing all games that have not started yet
			game_list = [{'id': g.id, 'players_count': len(g.players)} for g in Model.games if g.state == Model.Game.NOT_STARTED]
			return Common.json_message('game_list', game_list, request['id'])


		# Joining a game
		if request['type'] == 'game_join':
			game_list = [g for g in Model.games if g.id == request['object']['id']]
			if len(game_list) == 0:
				return Common.json_error('game_not_found', request['id'])
			g = game_list[0]
			# TODO check whether player can join this particular game
			if g.state == Model.Game.NOT_STARTED:
				return Common.json_error('unable_to_join', request['id'])
			g.players.append(user)
			user.current_game = g
			user.state = InLobby()

			return None



		# Do they want to chat?
		if request['type'] == 'chatMessage':
			# Object is just a string with message
			msg = request['object']
			# Broadcast message to all logged in users
			for u in Model.players:
				u.send(Common.json_message('chat_message', {'username': user.username, 'message': msg}, Common.random_id()))
			return None

		return Common.json_error('invalid_command', request['id'])


class InLobby:
	def request(self, user, request):
		pass
