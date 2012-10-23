# -*- coding: utf-8 *-*
import Model
import Common
import SocketServer
import json
import threading
import Queue
import PlayerState

requestQuery = Queue.Queue()
DEBUG_MODE = False

class RequestQueryChecker(threading.Thread):
	def run(self):
		self.is_running = True
		while self.is_running:
			try:
				request = requestQuery.get(True, 1)
				player = request[0]
				response = player.state.request(request[0], request[1])
				if response: # and not isinstance(player.state, PlayerState.Disconnected): # If we get None, we assume everything is ok and there is no need to send anything back
					player.socket.send(response)
			except Queue.Empty: # Queue is empty, so... do another loop
				pass


class RequestHandler(SocketServer.StreamRequestHandler):
	def handle(self):
		Common.console_message('%s connected' % self.request.getpeername()[0])
		self.player = Model.Player(self)
		self.player.state = PlayerState.NotLoggedIn()
		Model.players.append(self.player)
		self.last_message_id = 65535

		while True:
			data = self.rfile.readline()
			if data == '': # Socket disconnected
				self.player.state.disconnect(self.player)
				Common.console_message('%s (%s) disconnected' % (self.player.username, self.request.getpeername()[0]))
				break
			data = data.rstrip('\r\n')
			if DEBUG_MODE:
				Common.console_message('[GET] %s: %s' % (self.request.getpeername()[0], data))
			# Get the object
			try:
				data = json.loads(data.strip())
				if 'type' in data and 'id' in data and 'object' in data:
					# Here we add request to the query
					requestQuery.put((self.player, data))
				else: # Missing fields
					id = data['id'] if 'id' in data else 0
					response = Common.json_error('jsonMissingFields', id)
					self.player.socket.send(response)
			except ValueError: # Parsing failed
				response = Common.json_error('jsonParseFailed', 0)
				self.player.socket.send(response)

	def send(self, response):
		if DEBUG_MODE:
			Common.console_message('[SEND] to %s: %s' % (self.request.getpeername()[0], response))
		self.wfile.write(json.dumps(response['header']) + '\n')
		if response['object'] is not None:
			self.wfile.write(json.dumps(response['object']) + '\n')

	def get_next_message_id(self):
		self.last_message_id += 1
		return self.last_message_id

	def finish(self):
		Model.players.remove(self.player)


class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass
