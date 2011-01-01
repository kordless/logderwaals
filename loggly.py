import logging, os
from logging import handlers
import xml.dom.minidom as minidom
from google.appengine.api import urlfetch 

class LogglyHTTPSHandler(handlers.MemoryHandler):
    def __init__(self, capacity, flushLevel, target, endpoint):
        handlers.MemoryHandler.__init__(self, capacity, flushLevel, target)
        self.appname = os.getcwd().split('/')[-2]
        self.version = os.getcwd().split('/')[-1]
        self.endpoint = endpoint

    def flush(self):
        rpc = urlfetch.create_rpc()
        stuff = 'source=' + self.appname + '-' + self.version
        for record in self.buffer:
            stuff += self.format(record)
            urlfetch.make_fetch_call(rpc, url=self.endpoint, payload=stuff, method=urlfetch.POST)
        self.buffer = []

class LogglyLogger():
    def __init__(self, endpoint, level):
        self.endpoint = endpoint
        self.level = level
        logger = logging.getLogger()
        lh = LogglyHTTPSHandler(100, level, None, endpoint)
        formatterStr = '''%(asctime)s level=%(levelname)s, msg="%(message)s", module=%(module)s, file="%(filename)s", lineno=%(lineno)d'''
        formatter = logging.Formatter(formatterStr)
        lh.setFormatter(formatter)
        logger.addHandler(lh)
        logger.setLevel(level)
        self.lh = lh
        
    def flush(self):
        self.lh.flush()
