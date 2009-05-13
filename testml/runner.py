from testml.parser import Parser

class Runner(object):
    def __init__(self, document, bridge):
        self.document = document
        self.bridge = bridge

    def next(self):
        self.parser = Parser()
        self.parser.open(self.document)
        document = self.parser.parse()
        for args in ([1,1], [2,2], [3,3], [4,4]):
            yield 'running %s' % args, self.run, args

    def run(self, args):
        assert args[0] == args[1]
