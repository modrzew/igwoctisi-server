# -*- coding: utf-8 *-*
import Model
import Common

def request(user, request):
	# We expect request to be already validated as JSON object containing type, object and id fields

	# First of all, maybe they want to login
	if request['type'] == 'login':
		if 'username' in request['object'] and 'password' in request['object']:
			user.username = request['object']
			user.logged_in = True
			return Common.jsonOk(request['id'])
		else:
			return Common.jsonError('not_logged_in', request['id'])

	# Is the user logged in?
	if user.logged_in == False:
		return Common.jsonError('not_logged_in', request['id'])

	# Do they want to chat?
	if request['type'] == 'chatMessage':
		# Object is just a string with message
		msg = request['object']
		# Broadcast message to all logged in users
		for u in Model.users:
			u.send(Common.jsonMessage('chatMessage', {'username': user.username, 'message': msg}, Common.randomId()))
		return Common.jsonOk(request['id'])
