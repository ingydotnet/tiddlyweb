from testml.bridge import Bridge
import yaml

from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.serializer import Serializer

class TestMLBridge(Bridge):

    def setup(self):
        data = yaml.load(self.value)
        self.stash['tiddlers'] = {}
        for title in data:
                tiddler = Tiddler(title)
                tiddler.modfied = data.get('modified', '')
                tiddler.tags = data.get('tags', [])
                tiddler.text = data.get('text', '')
                tiddler.modifier = data.get('modifier', '')
                self.stash['tiddlers'][title] = tiddler

    def serialize(self, type):
        tiddler = self.stash['tiddlers'][self.value]
        serializer = Serialize(type)
        serializer.object = tiddler
        return serializer.to_string()
