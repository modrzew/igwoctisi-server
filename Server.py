# -*- coding: utf-8 *-*
import Model
import Communication
import Game
import Logic
import Common


if __name__ == "__main__":
	# Define the server address
	HOST, PORT = "localhost", 23456

	# Create server object
	server = Communication.Server((HOST, PORT), Communication.RequestHandler)
	ip, port = server.server_address
	Common.consoleMessage('Server started!')

	# Run requestQueryChecker
	requestQueryChecker = Communication.RequestQueryChecker()
	requestQueryChecker.isRunning = True
	requestQueryChecker.start()

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		Common.consoleMessage('Shutting down server.')
		requestQueryChecker.isRunning = False
