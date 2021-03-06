"""
Test that GETting a tiddler in some form.
"""

import sys
import os
sys.path.append('.')

from wsgi_intercept import httplib2_intercept
import wsgi_intercept
import httplib2
import simplejson

from base64 import b64encode
from re import match

from fixtures import muchdata, reset_textstore, teststore

from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.user import User

authorization = b64encode('cdent:cowpig')
bad_authorization = b64encode('cdent:cdent')
no_user_authorization = b64encode('foop:foop')

text_put_body=u"""modifier: JohnSmith
created: 
modified: 200803030303
tags: tagone

Hello, I'm John Smith \xbb and I have something to sell.
"""

def setup_module(module):
    from tiddlyweb.web import serve
    # we have to have a function that returns the callable,
    # Selector just _is_ the callable
    def app_fn():
        return serve.load_app()
    #wsgi_intercept.debuglevel = 1
    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('our_test_domain', 8001, app_fn)

    module.store = teststore()
    reset_textstore()
    muchdata(module.store)

    user = User('cdent')
    user.set_password('cowpig')
    module.store.put(user)

    try:
        os.mkdir('.test_cache')
    except OSError:
        pass # we don't care if it already exists

def test_get_tiddler():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler8',
            method='GET')

    assert response['status'] == '200', 'response status should be 200'
    assert 'i am tiddler 8' in content, 'tiddler should be correct content, is %s' % content

def test_get_tiddler_revision():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler8/revisions/1',
            method='GET')

    assert response['status'] == '200', 'response status should be 200'
    assert 'i am tiddler 8' in content, 'tiddler should be correct content, is %s' % content
    assert 'revision="1"' in content

def test_get_missing_tiddler():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler27',
            method='GET')

    assert response['status'] == '404', 'response status should be 404'

def test_get_missing_tiddler_revision():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler27/revisions/99',
            method='GET')

    assert response['status'] == '404', 'response status should be 404'

def test_get_tiddler_missing_revision():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler8/revisions/99',
            method='GET')

    assert response['status'] == '404'

def test_get_tiddler_wiki():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler8.wiki',
            method='GET')

    assert response['status'] == '200', 'response status should be 200 is %s' % response['status']
    assert response['content-type'] == 'text/html; charset=UTF-8', 'response content-type should be text/html; chareset=UTF-8 is %s' % response['content-type']
    assert '<title>\ntiddler8\n</title>' in content
    assert 'i am tiddler 8' in content, 'tiddler should be correct content, is %s' % content
    assert 'server.permissions="read, write, create, delete"' in content

def test_get_tiddler_revision_wiki():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler8/revisions/1.wiki',
            method='GET')

    assert response['status'] == '200', 'response status should be 200 is %s' % response['status']
    assert response['content-type'] == 'text/html; charset=UTF-8', 'response content-type should be text/html; chareset=UTF-8 is %s' % response['content-type']
    assert 'i am tiddler 8' in content, 'tiddler should be correct content, is %s' % content
    assert 'revision="1"' in content

def test_put_tiddler_txt():
    http = httplib2.Http()
    encoded_body = text_put_body.encode('utf-8')
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/TestOne',
            method='PUT', headers={'Content-Type': 'text/plain'}, body=encoded_body)

    assert response['status'] == '204', 'response status should be 204 is %s' % response['status']
    tiddler_url = response['location']
    assert tiddler_url == 'http://our_test_domain:8001/bags/bag0/tiddlers/TestOne', \
            'response location should be http://our_test_domain:8001/bags/bag0/tiddlers/TestOne is %s' \
            % tiddler_url

    response, content = http.request(tiddler_url, headers={'Accept': 'text/plain'})
    content = content.decode('utf-8')
    contents = content.strip().rstrip().split('\n')
    texts = text_put_body.strip().rstrip().split('\n')
    assert contents[-1] == texts[-1] # text
    assert contents[-3] == texts[-3] # tags

def test_put_tiddler_txt_no_modified():
    """
    Putting a tiddler with no modifier should make a default.
    """
    http = httplib2.Http()
    encoded_body = text_put_body.encode('utf-8')
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/TestOne',
            method='PUT', headers={'Content-Type': 'text/plain'}, body='modifier: ArthurDent\n\nTowels')

    assert response['status'] == '204', 'response status should be 204 is %s' % response['status']
    tiddler_url = response['location']
    assert tiddler_url == 'http://our_test_domain:8001/bags/bag0/tiddlers/TestOne', \
            'response location should be http://our_test_domain:8001/bags/bag0/tiddlers/TestOne is %s' \
            % tiddler_url

    response, content = http.request(tiddler_url, headers={'Accept': 'text/plain'})
    content = content.decode('utf-8')
    assert 'modified: 2' in content

def test_put_tiddler_json():
    http = httplib2.Http()

    json = simplejson.dumps(dict(text='i fight for the users', tags=['tagone','tagtwo'], modifier='', modified='200805230303', created='200803030303'))

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/TestTwo',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)

    assert response['status'] == '204', 'response status should be 204 is %s' % response['status']
    tiddler_url = response['location']
    assert tiddler_url == 'http://our_test_domain:8001/bags/bag0/tiddlers/TestTwo', \
            'response location should be http://our_test_domain:8001/bags/bag0/tiddlers/TestTwo is %s' \
            % tiddler_url

    response, content = http.request(tiddler_url, headers={'Accept': 'application/json'})
    info = simplejson.loads(content)
    assert response['last-modified'] == 'Fri, 23 May 2008 03:03:00 GMT'
    assert info['title'] == 'TestTwo'
    assert info['text'] == 'i fight for the users'

def test_put_tiddler_json_with_slash():
    http = httplib2.Http()

    json = simplejson.dumps(dict(text='i fight for the users', tags=['tagone','tagtwo'], modifier='', modified='200805230303', created='200803030303'))

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test%2FSlash',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)

    assert response['status'] == '204', 'response status should be 204 is %s' % response['status']
    assert response['location'] == 'http://our_test_domain:8001/bags/bag0/tiddlers/Test%2FSlash'


def test_put_tiddler_json_bad_path():
    """
    / in tiddler title is an unresolved source of some confusion.
    """
    http = httplib2.Http()

    json = simplejson.dumps(dict(text='i fight for the users 2', tags=['tagone','tagtwo'], modifier='', modified='200803030303', created='200803030303'))

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/..%2F..%2F..%2F..%2FTestThree',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)

    assert response['status'] == '404', 'response status should be 404 is %s' % response['status']

def test_put_tiddler_json_no_bag():
    """
    / in tiddler title is an unresolved source of some confusion.
    """
    http = httplib2.Http()

    json = simplejson.dumps(dict(text='i fight for the users 2', tags=['tagone','tagtwo'], modifier='', modified='200803030303', created='200803030303'))

    response, content = http.request('http://our_test_domain:8001/bags/nobagheremaam/tiddlers/SomeKindOTiddler',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)

    assert response['status'] == '409'
    assert 'There is no bag named: nobagheremaam' in content

def test_get_tiddler_via_recipe():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8.json',
            method='GET')

    assert response['status'] == '200'
    tiddler_info = simplejson.loads(content)
    assert tiddler_info['bag'] == 'bag28'

def test_get_tiddler_etag_recipe():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8.json',
            method='GET')

    assert response['status'] == '200'
    assert response['etag'] == 'bag28/tiddler8/1'
    tiddler_info = simplejson.loads(content)
    assert tiddler_info['bag'] == 'bag28'

def test_get_tiddler_etag_bag():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag28/tiddlers/tiddler8.json',
            method='GET')

    assert response['status'] == '200'
    assert response['etag'] == 'bag28/tiddler8/1'
    tiddler_info = simplejson.loads(content)
    assert tiddler_info['bag'] == 'bag28'

def test_get_tiddler_cached():
    [os.unlink('.test_cache/%s' % x) for x in os.listdir('.test_cache')]
    http = httplib2.Http('.test_cache')
    response, content = http.request('http://our_test_domain:8001/bags/bag28/tiddlers/tiddler8.json',
            method='GET')
    assert response['status'] == '200'
    assert response['etag'] == 'bag28/tiddler8/1'
    assert not response.fromcache
    response, content = http.request('http://our_test_domain:8001/bags/bag28/tiddlers/tiddler8.json',
            method='GET')
    assert response['status'] == '304'
    assert response['etag'] == 'bag28/tiddler8/1'
    assert response.fromcache

def test_put_tiddler_cache_fakey():
    [os.unlink('.test_cache/%s' % x) for x in os.listdir('.test_cache')]
    http_caching = httplib2.Http('.test_cache')
    http = httplib2.Http()

    json = simplejson.dumps(dict(text='i fight for the users 2', tags=['tagone','tagtwo'], modifier='', modified='200803030303', created='200803030303'))

    response, content = http_caching.request('http://our_test_domain:8001/recipes/long/tiddlers/CashForCache',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)
    assert response['status'] == '204'
    assert response['etag'] == 'bag1/CashForCache/1'

    response, content = http_caching.request('http://our_test_domain:8001/recipes/long/tiddlers/CashForCache',
            method='GET', headers={'Accept': 'application/json'})
    assert response['status'] == '200'
    assert response['etag'] == 'bag1/CashForCache/1'

    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/CashForCache',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)
    assert response['status'] == '204'
    assert response['etag'] == 'bag1/CashForCache/2'

    response, content = http_caching.request('http://our_test_domain:8001/recipes/long/tiddlers/CashForCache',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)
    assert response['status'] == '412'

def test_put_tiddler_via_recipe():
    http = httplib2.Http()
    json = simplejson.dumps(dict(text='i fight for the users 2', tags=['tagone','tagtwo'], modifier='', modified='200803030303', created='200803030303'))

    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/FantasticVoyage',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)

    assert response['status'] == '204'
    assert response['etag'] == 'bag1/FantasticVoyage/1'
    url = response['location']

    reponse, content = http.request(url, method='GET', headers={'Accept': 'application/json'})
    tiddler_dict = simplejson.loads(content)
    assert tiddler_dict['bag'] == 'bag1'
    assert response['etag'] == 'bag1/FantasticVoyage/1'

def test_slash_in_etag():
    http = httplib2.Http()

    json = simplejson.dumps(dict(text='i fight for the users', tags=['tagone','tagtwo'], modifier='', modified='200805230303', created='200803030303'))

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test%2FTwo',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test%2FTwo',
            method='PUT', headers={'Content-Type': 'application/json', 'If-Match': 'bag0/Test%2FTwo/1'}, body=json)
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test%2FTwo',
            method='PUT', headers={'Content-Type': 'application/json', 'If-Match': 'bag0/Test/Two/2'}, body=json)
    assert response['status'] == '412'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test%2FTwo',
            method='PUT', headers={'Content-Type': 'application/json', 'If-Match': 'bag0/Test%2FTwo/2'}, body=json)
    assert response['status'] == '204'

def test_paren_in_etag():
    http = httplib2.Http()

    json = simplejson.dumps(dict(text='i fight for the users', tags=['tagone','tagtwo'], modifier='', modified='200805230303', created='200803030303'))

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test(Two)',
            method='PUT', headers={'Content-Type': 'application/json'}, body=json)
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test(Two)',
            method='PUT', headers={'Content-Type': 'application/json', 'If-Match': 'bag0/Test(Two)/1'}, body=json)
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test(Two)',
            method='PUT', headers={'Content-Type': 'application/json', 'If-Match': 'bag0/Test%28Two%29/2'}, body=json)
    assert response['status'] == '412'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/Test(Two)',
            method='PUT', headers={'Content-Type': 'application/json', 'If-Match': 'bag0/Test(Two)/2'}, body=json)
    assert response['status'] == '204'

def test_get_tiddler_text_created():
    """
    Make sure the tiddler comes back to us as we expect.
    In the process confirm that Accept header processing is working
    as expect, by wanting xml (which we don't do), more than text/plain,
    which we do.
    """
    http = httplib2.Http()
    tiddler_url = 'http://our_test_domain:8001/bags/bag0/tiddlers/TestOne'
    response, content = http.request(tiddler_url, headers={'Accept': 'text/xml; q=1, text/plain'})

    content = content.decode('utf-8')
    contents = content.strip().rstrip().split('\n')
    texts = text_put_body.strip().rstrip().split('\n')
    assert contents[-1] == u'Towels' # text
    assert contents[-3] == u'tags: ' # tags
    assert match('created: \d{12}', contents[1])

def test_get_tiddler_html_slash():
    """
    Create a tiddler with a tiddly link with a slash in it and make
    sure it is escape properly.
    """
    tiddler = Tiddler('slashed', 'bag0')
    tiddler.text = '[[test/tiddler]] and [[foo/bar|http://example.com/hassle]] and [[bar/baz|/happy/hour]]'
    store.put(tiddler)

    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/slashed', 
            headers={'Accept:': 'text/html'})
    assert response['status'] == '200'
    assert 'test%2Ftiddler" >test/tiddler' in content
    assert 'href="http://example.com/hassle"' in content
    assert 'href="/happy/hour"' in content


def test_tiddler_bag_constraints():
    encoded_body = text_put_body.encode('utf-8')
    http = httplib2.Http()
    _put_policy('unreadable', dict(policy=dict(manage=['cdent'],read=['NONE'],write=['NONE'],create=['NONE'])))

    # try to create a tiddler and fail
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % authorization},
            body=encoded_body)
    assert response['status'] == '403'
    assert 'may not create' in content

    # create and succeed
    _put_policy('unreadable', dict(policy=dict(manage=['cdent'],read=['NONE'],write=['NONE'],create=['cdent'])))
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % authorization},
            body=encoded_body)
    assert response['status'] == '204'

    # fail when bad auth format
    _put_policy('unreadable', dict(policy=dict(manage=['cdent'],read=['NONE'],write=['NONE'],create=['cdent'])))
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': '%s' % authorization},
            body=encoded_body)
    assert response['status'] == '403'

    # fail when bad auth info
    _put_policy('unreadable', dict(policy=dict(manage=['cdent'],read=['NONE'],write=['NONE'],create=['cdent'])))
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % bad_authorization},
            body=encoded_body)
    assert response['status'] == '403'

    # fail when bad user info
    _put_policy('unreadable', dict(policy=dict(manage=['cdent'],read=['NONE'],write=['NONE'],create=['cdent'])))
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % no_user_authorization},
            body=encoded_body)
    assert response['status'] == '403'

    # write and fail
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % authorization},
            body=encoded_body)
    assert response['status'] == '403'
    assert 'may not write' in content

    # write and succeed
    _put_policy('unreadable', dict(policy=dict(manage=['cdent'],read=['NONE'],write=['cdent'],create=['NONE'])))
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % authorization},
            body=encoded_body)
    assert response['status'] == '204'

    # read and fail
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne',
            method='GET', headers={'Accept': 'text/plain', 'Authorization': 'Basic %s' % authorization})
    assert response['status'] == '403'
    assert 'may not read' in content

    # update the policy so we can read and GET the thing
    _put_policy('unreadable', dict(policy=dict(manage=['cdent'],read=['cdent'],write=['NONE'],delete=['NONE'])))
    response, content = http.request('http://our_test_domain:8001/bags/unreadable/tiddlers/WroteOne.wiki',
            method='GET', headers={'Accept': 'text/plain', 'Authorization': 'Basic %s' % authorization})
    assert response['status'] == '200'
    assert 'John Smith' in content
    assert 'server.permissions="read, create"' in content

def test_get_tiddler_via_recipe_with_perms():

    _put_policy('bag28', dict(policy=dict(manage=['cdent'],read=['NONE'],write=['NONE'])))
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8.json',
            method='GET')
    assert response['status'] == '403'
    assert 'may not read' in content

    _put_policy('bag28', dict(policy=dict(manage=['cdent'],read=['cdent'],write=['NONE'])))
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8.json',
            headers=dict(Authorization='Basic %s' % authorization), method='GET')
    assert response['status'] == '200'

    tiddler_info = simplejson.loads(content)
    assert tiddler_info['bag'] == 'bag28'

    encoded_body = text_put_body.encode('utf-8')
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % authorization},
            body=encoded_body)
    assert response['status'] == '403'
    assert 'may not write' in content

    _put_policy('bag28', dict(policy=dict(manage=['cdent'],read=['cdent'],write=['nancy'])))
    encoded_body = text_put_body.encode('utf-8')
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='PUT', headers={'Content-Type': 'text/plain', 'Authorization': 'Basic %s' % authorization},
            body=encoded_body)
    assert response['status'] == '403'

    _put_policy('bag28', dict(policy=dict(manage=['cdent'],read=['cdent'],write=['cdent'])))
    encoded_body = text_put_body.encode('utf-8')
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='PUT', headers={'Content-Type': 'text/plain'},
            body=encoded_body)
    # when we PUT without permission there's no good way to handle auth
    # so we just forbid.
    assert response['status'] == '403'

def test_delete_tiddler_in_recipe():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='DELETE')
    assert response['status'] == '204'

# there are multiple tiddler8s in the recipe
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='DELETE')
    assert response['status'] == '204'
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='DELETE')
    assert response['status'] == '204'
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='DELETE')
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/tiddler8',
            method='DELETE')
    assert response['status'] == '404'

def test_delete_tiddler_in_bag():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/TestOne',
            method='DELETE')
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/TestOne',
            method='DELETE')
    assert response['status'] == '404'


def test_delete_tiddler_etag():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag5/tiddlers/tiddler0',
            method='DELETE', headers={'If-Match': 'bag5/tiddler0/9'})
    assert response['status'] == '412'

    response, content = http.request('http://our_test_domain:8001/bags/bag5/tiddlers/tiddler0',
            method='DELETE', headers={'If-Match': 'bag5/tiddler0/1'})
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/bags/bag5/tiddlers/tiddler0',
            method='DELETE')
    assert response['status'] == '404'


def test_delete_tiddler_in_bag_perms():
    _put_policy('bag0', dict(policy=dict(manage=['cdent'],read=['cdent'],write=['cdent'],delete=['cdent'])))
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler0',
            method='DELETE')
    assert response['status'] == '403'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler0',
            method='DELETE', headers={'Authorization': 'Basic %s' % authorization})
    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/bags/bag0/tiddlers/tiddler0',
            method='DELETE', headers={'Authorization': 'Basic %s' % authorization})
    assert response['status'] == '404'

def test_tiddler_no_recipe():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/recipes/short/tiddlers/tiddler8',
            method='GET')
    assert response['status'] == '404'

def test_binary_tiddler():
    image = file('test/peermore.png', 'rb')
    content = image.read()

    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/peermorepng',
            method='PUT', headers={'Content-Type': 'image/png'},
            body=content)

    assert response['status'] == '204'

    response, content = http.request('http://our_test_domain:8001/recipes/long/tiddlers/peermorepng',
            method='GET')
    assert response['status'] == '200'
    assert response['content-type'] == 'image/png'

def _put_policy(bag_name, policy_dict):
    json = simplejson.dumps(policy_dict)

    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/bags/%s' % bag_name,
            method='PUT', headers={'Content-Type': 'application/json', 'Authorization': 'Basic %s' % authorization},
            body=json)
    assert response['status'] == '204'
