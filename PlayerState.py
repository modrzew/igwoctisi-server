# -*- coding: utf-8 *-*
import Model
import Common

# We expect request to be already validated as JSON object containing type, object and id fields

class NotLoggedIn:
    def request(self, user, request):
        # First of all, maybe they want to login
        if request['type'] == 'login':
            if 'username' in request['object'] and 'password' in request['object']:
                user.username = request['object'].username
                user.logged_in = True
                user.state = LoggedIn()
                return Common.jsonOk(request['id'])
            else:
                return Common.jsonError('not_logged_in', request['id'])

        # Is the user logged in?
        if not user.logged_in:
            return Common.jsonError('not_logged_in', request['id'])


class LoggedIn:
    def request(self, user, request):
        # Do they want to chat?
        if request['type'] == 'chatMessage':
            # Object is just a string with message
            msg = request['object']
            # Broadcast message to all logged in users
            for u in Model.players:
                u.send(Common.jsonMessage('chatMessage', {'username': user.username, 'message': msg}, Common.randomId()))
            return Common.jsonOk(request['id'])

