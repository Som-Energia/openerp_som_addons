from destral import testing
from osv import osv
import unittest

from datetime import datetime, timedelta

class ConfiguracioTests(unittest.TestCase):

    def setUp(self):
        self.pool = self.openerp.pool
        self.Configuracio = self.pool.get('class.configuracio')
    
    def tearDown(self):
        pass

    def test_canviarContrasenya_