# -*- coding: utf-8 *-*
import Model
import Common
import Game
import SocketServer
import json
import time
import threading
import Queue

requestQuery = Queue.Queue()

class RequestQueryChecker(threading.Thread):
	def run(self):
		while self.isRunning:
			try:
				request = requestQuery.get(True, 1)
				user = request[0]
				response = Game.request(request[1])
				user.send(response)
			except Queue.Empty: # Queue is empty, so... do another loop
				pass


class RequestHandler(SocketServer.StreamRequestHandler):
	def handle(self):
		Common.consoleMessage('Socket ' + str(self.request.getsockname()) + ' connected')
		self.user = Model.User(self)
		Model.users.append(self.user)

		while True:
			data = self.rfile.readline()
			if data == '': # Socket disconnected
				Common.consoleMessage('Socket ' + str(self.request.getsockname()) + ' disconnected')
				break
			try:
				data = json.loads(data.strip())
				if 'type' in data and 'id' in data and 'object' in data:
					# Here we add request to the query
					requestQuery.put((self.user, data))
				else:
					id = data['id'] if 'id' in data else ''
					self.wfile.write(Common.jsonError('json_missing_fields', id))
			except ValueError:
				self.wfile.write(Common.jsonError('json_parse_failed', ''))


	def finish(self):
		pass


class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass
