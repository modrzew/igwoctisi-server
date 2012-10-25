# -*- coding: utf-8 *-*
import Communication
import Common
import sys
import time
import os, os.path
import Database


if __name__ == "__main__":
	Communication.DEBUG_MODE = False
	# Define the server address
	if len(sys.argv) >= 3:
		HOST, PORT = str(sys.argv[1]), int(sys.argv[2])
		if len(sys.argv) == 4:
			Communication.DEBUG_MODE = (sys.argv[3] == 'debug')
	else:
		HOST, PORT = "localhost", 23456

	# Turn on logging if debug mode
	if Communication.DEBUG_MODE:
		filename = 'logs/%d.txt' % time.time()
		Common.console_message('Saving log to %s' % filename)
		if not os.path.exists('logs'):
			os.mkdir('logs')
		Common.LOG_FILE = open(filename, 'w')

	# Create server object
	server = Communication.Server((HOST, PORT), Communication.RequestHandler)
	ip, port = server.server_address
	Common.console_message('Server started!')
	if Communication.DEBUG_MODE:
		Common.console_message('Debug mode is ON')

	# Run requestQueryChecker
	requestQueryChecker = Communication.RequestQueryChecker()
	requestQueryChecker.start()

	# And serve... forever!
	try:
		server.serve_forever()
	except KeyboardInterrupt: # When Ctrl+C is hit
		Common.console_message('Shutting down server.')
		requestQueryChecker.is_running = False

	if Communication.DEBUG_MODE:
		Common.LOG_FILE.close()