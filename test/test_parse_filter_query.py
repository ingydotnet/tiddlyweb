"""
Experimental diddling around to make sure that
a CGI query string will become what we think it should.

This test file is a playground for the moment.
"""

from tiddlyweb.web.query import parse_for_filters
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.filters import recursive_filter

def test_parsing():
    """
    Incomplete testing of parsing the filter string
    as part of the query string parsing, leaving the rest
    of the query string intact.
    """
    string = 'slag=absolute;foo=;select=tag:systemConfig;select=tag:blog;fat=1;sort=-modified;limit=0,10;select=title:monkey'

    filters, leftovers = parse_for_filters(string)

    assert len(filters) == 5
    assert leftovers == 'slag=absolute;foo=;fat=1'

    tiddlers = [Tiddler('a'), Tiddler('monkey')]
    tiddlers[1].tags = ['systemConfig', 'blog']
    tiddlers = recursive_filter(filters, tiddlers)
    
    assert len(tiddlers) == 1
    assert tiddlers[0].title == 'monkey'
