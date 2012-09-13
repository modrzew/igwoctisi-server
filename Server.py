# -*- coding: utf-8 *-*
import Model
import Communication
import Game
import Logic
import Common
import sys


if __name__ == "__main__":
	# Define the server address
	if len(sys.argv) == 3:
		HOST, PORT = str(sys.argv[1]), int(sys.argv[2])
	else:
		HOST, PORT = "localhost", 23456

	# Create server object
	server = Communication.Server((HOST, PORT), Communication.RequestHandler)
	ip, port = server.server_address
	Common.consoleMessage('Server started!')

	# Run requestQueryChecker
	requestQueryChecker = Communication.RequestQueryChecker()
	requestQueryChecker.isRunning = True
	requestQueryChecker.start()

	# And serve... forever!
	try:
		server.serve_forever()
	except KeyboardInterrupt: # When Ctrl+C is hit
		Common.consoleMessage('Shutting down server.')
		requestQueryChecker.isRunning = False
