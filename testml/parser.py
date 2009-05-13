class Parser(object):
    def open(self, file):
        self.testml_path = file
        handle = open(file, 'r')
        self.stream = handle.read()

    def parse(self):
        return

