# -*- coding: utf-8 *-*
import Model
import Common
import SocketServer
import json
import threading
import Queue
import PlayerState
import time

requestQuery = Queue.Queue()

class RequestQueryChecker(threading.Thread):
	def run(self):
		while self.isRunning:
			try:
				request = requestQuery.get(True, 1)
				player = request[0]
				response = player.state.request(request[0], request[1])
				# If we get None, we assume everything is ok and there is no need to send anything back
				if response:
					player.send(response)
			except Queue.Empty: # Queue is empty, so... do another loop
				pass


class RequestHandler(SocketServer.StreamRequestHandler):
	def handle(self):
		Common.console_message('Socket ' + str(self.request.getsockname()) + ' connected')
		self.player = Model.Player(self)
		self.player.state = PlayerState.NotLoggedIn()
		Model.players.append(self.player)

		while True:
			data = self.rfile.readline()
			if data == '': # Socket disconnected
				Common.console_message('Socket ' + str(self.request.getsockname()) + ' disconnected')
				break
			data = data.rstrip('\r\n')
			try:
				data = json.loads(data.strip())
				if 'type' in data and 'id' in data and 'object' in data:
					# Here we add request to the query
					requestQuery.put((self.player, data))
				else:
					id = data['id'] if 'id' in data else 0
					response = Common.json_error('jsonMissingFields', id)
					self.player.send(response)
			except ValueError:
				response = Common.json_error('jsonParseFailed', 0)
				self.player.send(response)


	def finish(self):
		pass


class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass
