"""
Text based serializers.
"""

import urllib

def recipe_as(recipe, sortkey):
    """
    Never sort a recipe, so ignore sortkey, but
    keep it there for sake of the interface.
    """
    lines = []
    for bag, filter in recipe:
        line = ''
# enable BagS in recipes
        if type(bag) != '':
            bag = bag.name
        line += '/bags/%s' % urllib.quote(bag)
        if filter:
            line += '?%s' % urllib.quote(filter)
        lines.append(line)
    return "\n".join(lines)

def bag_as(bag, sortkey):
    """
    List the tiddlers in a bag as text.

    It might be that there should be some sense of sorting
    here? For now we'll sort by name, but that buggers us for
    later.
    """
    lines = []
    for tiddler in sorted(bag.list_tiddlers(), key=sortkey):
        line = 'tiddlers/%s' % urllib.quote(tiddler.name)
        lines.append(line)
    return "\n".join(lines)

def tiddler_as(tiddler, sortkey):
    return 'name: %s\nauthor: %s\ntags: %s\n\n%s\n' \
            % (tiddler.name, tiddler.author, tags_as(tiddler.tags, sortkey), tiddler.content)

def tags_as(tags, sortkey):
    tag_string_list = []
    for tag in sorted(tags, key=sortkey):
        if ' ' in tag:
            tag = '[[%s]]' % tag
        tag_string_list.append(tag)
    return ' '.join(tag_string_list)