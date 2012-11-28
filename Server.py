# -*- coding: utf-8 *-*
import Communication
import Database
import Common
import Model
import sys
import time
import os


if __name__ == "__main__":
	# Define the default server address
	HOST, PORT = "localhost", 23456
	# Get the command line parameters
	for i, a in enumerate(sys.argv):
		if i > 0: # First entry is filename
			if a[0:2] == '--':
				if a == '--debug':
					Communication.DEBUG_MODE = True
				if a == '--database':
					Database.connect()
				if a == '--logging': # Turn on logging
					filename = 'logs/%d.txt' % time.time()
					Common.console_message('Saving log to %s' % filename)
					if not os.path.exists('logs'):
						os.mkdir('logs')
					Common.LOG_FILE = open(filename, 'w')
			else:
				if i == len(sys.argv) - 2: # Host
					HOST = str(a)
				if i == len(sys.argv) - 1:
					PORT = int(a)

	# Create server object
	server = Communication.Server((HOST, PORT), Communication.RequestHandler)
	server.allow_reuse_address = True
	ip, port = server.server_address
	Common.console_message('Server started on %s at %d!' % (HOST, PORT))
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
		server.shutdown()
		for p in Model.players:
			#server.shutdown_request(p.socket)
			del p
		for g in Model.games:
			g.manager.game_end()
			del g

	if Common.LOG_FILE:
		Common.LOG_FILE.close()