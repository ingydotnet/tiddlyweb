"""
Routines that integrate the basic object classes.

Things like loading up all the tiddlers in a recipe,
listing tiddlers in a bag, and filtering tiddlers.

These are kept in here to avoid a having store
and serialize objects in filters and recipes and the
like.
"""

from tiddlyweb.model.bag import Bag
from tiddlyweb.filters import parse_for_filters, recursive_filter
from tiddlyweb.serializer import TiddlerFormatError
from tiddlyweb.store import NoBagError


def get_tiddlers_from_recipe(recipe, environ=None):
    """
    Return the list of tiddlers that result
    from processing the recipe.

    This list of tiddlers is unique by title with
    tiddlers later in the recipe taking precedence
    over those earlier in the recipe.
    """

    template = _recipe_template(environ)
    store = recipe.store
    uniquifier = {}
    for bag, filter_string in recipe.get_recipe(template):
        if isinstance(bag, basestring):
            bag = Bag(name=bag)
        if store:
            bag = store.get(bag)
        for tiddler in filter_tiddlers_from_bag(bag, filter_string):
            uniquifier[tiddler.title] = tiddler
    return uniquifier.values()


def determine_tiddler_bag_from_recipe(recipe, tiddler, environ=None):
    """
    We have a recipe and a tiddler. We need to
    know the bag in which this tiddler can be found.
    This is different from determine_bag_for_tiddler().
    That one finds the bag the tiddler _could_ be in.
    This is the bag the tiddler _is_ in.

    We reverse the recipe_list, and filter each bag
    according to the rule. Then we look in the list of
    tiddlers and see if ours is in there.
    """
    store = recipe.store
    template = _recipe_template(environ)
    for bag, filter_string in reversed(recipe.get_recipe(template)):
        if isinstance(bag, basestring):
            bag = Bag(name=bag)
        if store:
            bag = store.get(bag)
        for candidate_tiddler in filter_tiddlers_from_bag(bag, filter_string):
            if tiddler.title == candidate_tiddler.title:
                return bag

    raise NoBagError('no suitable bag for %s' % tiddler.title)


def determine_bag_for_tiddler(recipe, tiddler, environ=None):
    """
    Return the bag which this tiddler would be in if we
    were to save it to the recipe rather than to a default
    bag.

    This is a matter of reversing the recipe list and seeing
    if the tiddler is a part of the bag + filter. If bag+filter
    is true, return that bag.
    """
    template = _recipe_template(environ)
    for bag, filter_string in reversed(recipe.get_recipe(template)):
        # ignore the bag and make a new bag
        tmpbag = Bag(filter_string, tmpbag=True)
        tmpbag.add_tiddler(tiddler)
        for candidate_tiddler in filter_tiddlers_from_bag(tmpbag, filter_string):
            if tiddler.title == candidate_tiddler.title:
                if isinstance(bag, basestring):
                    bag = Bag(name=bag)
                return bag

    raise NoBagError('no suitable bag for %s' % tiddler.title)


def get_tiddlers_from_bag(bag):
    """
    Return the list of tiddlers that are in a bag.
    """

    tiddlers = bag.list_tiddlers()
    loaded_tiddlers = []
    if bag.store:
        for tiddler in tiddlers:
            try:
                tiddler = bag.store.get(tiddler)
            except TiddlerFormatError:
                # XXX do more here?
                pass
            loaded_tiddlers.append(tiddler)

    return loaded_tiddlers


def filter_tiddlers_from_bag(bag, filters):
    """
    Return the list of tiddlers resulting from filtering
    bag by filter. The filter is a string that will be
    parsed to a list of filters.
    """
    store = bag.store

    # XXX isinstance considered harmful
    if isinstance(filters, basestring):
        filters, leftovers = parse_for_filters(filters)
    if store:
        return recursive_filter(filters, get_tiddlers_from_bag(bag))
    else:
        return recursive_filter(filters, bag.list_tiddlers())


def _recipe_template(environ):
    template = {}
    try:
        if environ:
            template['user'] = environ['tiddlyweb.usersign']['name']
    except KeyError:
        pass
    return template
