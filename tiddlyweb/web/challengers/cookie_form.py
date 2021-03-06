"""
Present or validate a form for getting a username
and password.
"""

import Cookie
import logging

from tiddlyweb.web.challengers import ChallengerInterface
from tiddlyweb.web.util import server_host_url
from tiddlyweb.model.user import User
from tiddlyweb.store import NoUserError
from sha import sha


class Challenger(ChallengerInterface):
    """
    A simple challenger that asks the user, by form, for their
    username and password and validates it against the user
    database. If it is good, a cookie is sent to the client which
    is later used by the simple_cookie credentials extractor.
    """

    def challenge_get(self, environ, start_response):
        """
        Respond to a GET request by sending a form.
        """
        redirect = environ['tiddlyweb.query'].get('tiddlyweb_redirect', ['/'])[0]
        return self._send_cookie_form(environ, start_response, redirect)

    def challenge_post(self, environ, start_response):
        """
        Respond to a POST by processing data sent from a form.
        The form should include a username and password. If it
        does not, send the form aagain. If it does, validate
        the data.
        """
        query = environ['tiddlyweb.query']
        redirect = query.get('tiddlyweb_redirect', ['/'])[0]

        try:
            user = query['user'][0]
            password = query['password'][0]
            return self._validate_and_redirect(environ, start_response, user, password, redirect)
        except KeyError:
            return self._send_cookie_form(environ, start_response, redirect, '401 Unauthorized')

    def _send_cookie_form(self, environ, start_response, redirect, status='200 OK', message=''):
        """
        Send a simple form to the client asking for a username
        and password.
        """
        start_response(status, [('Content-Type', 'text/html')])
        environ['tiddlyweb.title'] = 'Cookie Based Login'
        return [
"""
<pre>
%s
<form action="" method="POST">
User: <input name="user" size="40" />
Password <input type="password" name="password" size="40" />
<input type="hidden" name="tiddlyweb_redirect" value="%s" />
<input type="submit" value="submit" />
</form>
</pre>
""" % (message, redirect)]

    def _validate_and_redirect(self, environ, start_response, username, password, redirect):
        """
        Check a username and password. If valid, send a cookie
        to the client. If it is not, send the form again.
        """
        status = '401 Unauthorized'
        try:
            store = environ['tiddlyweb.store']
            secret = environ['tiddlyweb.config']['secret']
            user = User(username)
            user = store.get(user)
            if user.check_password(password):
                uri = '%s%s' % (server_host_url(environ), redirect)
                cookie = Cookie.SimpleCookie()
                secret_string = sha('%s%s' % (user.usersign, secret)).hexdigest()
                cookie['tiddlyweb_user'] = '%s:%s' % (user.usersign, secret_string)
                cookie['tiddlyweb_user']['path'] = self._cookie_path(environ)
                logging.debug('303 to %s' % uri)
                start_response('303 Other',
                        [('Set-Cookie', cookie.output(header='')),
                            ('Location', uri)])
                return [uri]
        except KeyError:
            pass
        except NoUserError:
            pass
        return self._send_cookie_form(environ, start_response, redirect, status, 'User or Password no good')
