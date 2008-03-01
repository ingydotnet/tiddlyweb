"""
Data structures required for our testing.
"""

import sys
sys.path.append('.')
from tiddlyweb.bag import Bag
from tiddlyweb.tiddler import Tiddler

tiddlers = [
        Tiddler(
            name='TiddlerOne',
            content='c tiddler one content',
            tags=['tagone', 'tagtwo']
        ),
        Tiddler(
            name='TiddlerTwo',
            content='b tiddler two content',
        ),
        Tiddler(
            name='TiddlerThree',
            content='a tiddler three content',
            tags=['tagone', 'tagthree']
        )
]

bagone = Bag(name='bagone')
bagone.add_tiddler(tiddlers[0])
bagtwo = Bag(name='bagtwo')
bagtwo.add_tiddler(tiddlers[1])
bagthree = Bag(name='bagthree')
bagthree.add_tiddler(tiddlers[2])
bagfour = Bag(name='bagfour')
bagfour.add_tiddler(tiddlers[0])
bagfour.add_tiddler(tiddlers[1])
bagfour.add_tiddler(tiddlers[2])

recipe_list = [
         [bagone, 'TiddlerOne'],
         [bagtwo, 'TiddlerTwo'],
         [bagthree, '[tag[tagone]] [tag[tagthree]]']
         ]
