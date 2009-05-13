from testml.runner import Runner
from testmlbridge import TestMLBridge

def test():
    for test in (Runner(
        'test/testml/serialize_tiddler.tml',
        TestMLBridge,
    ).next()):
         yield test
