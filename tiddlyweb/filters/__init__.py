"""
Overarching handler for TiddlyWeb filters.

This is the second iteration of filters for TiddlyWeb.
The first version was based on TiddlyWiki filters but
this was found to be not entirely well suited to the
HTTP situation in which TiddlyWeb finds itself, nor
was it particularly easy to extend in a way that was
simple, clear and powerful.

This new style hopes to be some of those things.

Filters are parsed from a string that is formatted
as a CGI query string with parameters and arguments.
The parameter is a filter type. Each filter is processed
in sequence: the first processing all the tiddlers
handed to it, the next taking only those that result
from the first.

Filters can be extended by adding more parsers to
FILTER_PARSERS. Parsers for existing filter types
may be extended as well (see the documentation for
each type).
"""

import cgi

from tiddlyweb.filters.select import select_by_attribute, select_relative_attribute, select_parse
from tiddlyweb.filters.sort import sort_by_attribute, sort_parse
from tiddlyweb.filters.limit import limit, limit_parse


class FilterError(Exception):
    """
    An exception to throw when an attempt is made to
    filter on an unavailable attribute.
    """
    pass


FILTER_PARSERS = {
        'select': select_parse,
        'sort':   sort_parse,
        'limit':  limit_parse,
        }


def parse_for_filters(query_string):
    """
    Take a string that looks like a CGI query
    string and parse if for filters. Return
    a tuple of a list of filter functions and
    a string of whatever was in the query string that
    did not result in a filter.
    """
    if ';' in query_string:
        strings = query_string.split(';')
    else:
        strings = query_string.split('&')

    filters = []
    leftovers = [] 
    for string in strings:
        query = cgi.parse_qs(string)
        try:
            key, value = query.items()[0]

            try:
                argument = unicode(value[0], 'UTF-8')
            except TypeError:
                argument = value[0]

            func = FILTER_PARSERS[key](argument)
            filters.append(func)
        except(KeyError, IndexError):
            leftovers.append(string)

    leftovers = ';'.join(leftovers)
    return filters, leftovers


def recursive_filter(filters, tiddlers):
    """
    Recursively process the list of filters found
    by parse_for_filters against the given list
    of tiddlers.

    Each next filter processes only those tiddlers
    that were results of the previous filter.
    """
    if len(filters) == 0:
        return tiddlers
    filter = filters.pop(0)
    try:
        return recursive_filter(filters, filter(tiddlers))
    except AttributeError, exc:
        raise FilterError('malformed filter: %s' % exc)
