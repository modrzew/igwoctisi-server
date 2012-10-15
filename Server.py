# -*- coding: utf-8 *-*
import Communication
import Common
import sys

if __name__ == "__main__":
	Communication.DEBUG_MODE = False
	# Define the server address
	if len(sys.argv) >= 3:
		HOST, PORT = str(sys.argv[1]), int(sys.argv[2])
		if len(sys.argv) == 4:
			Communication.DEBUG_MODE = (sys.argv[3] == 'debug')
	else:
		HOST, PORT = "localhost", 23456

	# Create server object
	server = Communication.Server((HOST, PORT), Communication.RequestHandler)
	ip, port = server.server_address
	Common.console_message('Server started!')
	if Communication.DEBUG_MODE:
		Common.console_message('Debug mode is ON')

	# Run requestQueryChecker
	requestQueryChecker = Communication.RequestQueryChecker()
	requestQueryChecker.isRunning = True
	requestQueryChecker.start()

	# And serve... forever!
	try:
		server.serve_forever()
	except KeyboardInterrupt: # When Ctrl+C is hit
		Common.console_message('Shutting down server.')
		requestQueryChecker.isRunning = False
