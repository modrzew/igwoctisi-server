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
				if response: # If we get None, we assume everything is ok and there is no need to send anything back
					player.send(response)
			except Queue.Empty: # Queue is empty, so... do another loop
				pass


class RequestHandler(SocketServer.StreamRequestHandler):
	def handle(self):
		Common.console_message('Socket ' + str(self.request.getpeername()) + ' connected')
		self.player = Model.Player(self)
		self.player.state = PlayerState.NotLoggedIn()
		Model.players.append(self.player)

		while True:
			# TODO poprawić to, co namek zjebał (ja chcę dostawać jeden obiekt i chuj)
			# Get the header
			header = self.rfile.readline()
			if header == '': # Socket disconnected
				Common.console_message('Socket ' + str(self.request.getsockname()) + ' disconnected')
				break
			header = header.rstrip('\r\n')
			# Get the object
			object = self.rfile.readline()
			try:
				data = json.loads(header.strip())
				data['object'] = json.loads(object)
				if 'type' in data and 'id' in data and 'object' in data:
					# Here we add request to the query
					requestQuery.put((self.player, data))
				else: # Missing fields
					id = data['id'] if 'id' in data else 0
					response = Common.json_error('jsonMissingFields', id)
					self.player.send(response)
			except ValueError: # Parsing failed
				response = Common.json_error('jsonParseFailed', 0)
				self.player.send(response)


	def finish(self):
		pass


class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass
