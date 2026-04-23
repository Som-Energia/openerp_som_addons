# -*- coding: utf-8 -*-

import unittest

class GenerationkWhInvoiceLineOwner_test(unittest.TestCase):

    def setUp(self):
        self.maxDiff=None
        import erppeek_wst
        import dbconfig
        self.c = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.c.begin()
        self.LineOwner = self.c.GenerationkwhInvoiceLineOwner
        self.GisceFacturaLine = self.c.GiscedataFacturacioFacturaLinia
        self.clearData()
        self.contract, self.contract2 = self.c.GiscedataPolissa.search([], limit=2)
        self.member = 1 # has 25 shares at the first investment wave
        self.partner = 2
        self.member2 = 469
        self.partner2 = 550

    def tearDown(self):
        self.c.rollback()
        self.c.close()

    def clearData(self):
        self.c.GenerationkwhAssignment.dropAll()
        self.c.GenerationkwhInvestment.dropAll()

    def test__getPriceWithoutGeneration__allOk(self):
        line = self.GisceFacturaLine.read(20972988)
        self.assertEqual(line['price_unit_multi'], 0.114)
        priceNoGen = float(self.LineOwner.getPriceWithoutGeneration(line)['price_unit'])
        self.assertEqual(priceNoGen , 0.13)

    def test__getPriceWithoutGeneration__refundInvoice(self):
        line = self.GisceFacturaLine.read(10486898)
        self.assertEqual(line['price_unit_multi'], 0.115)
        priceNoGen = float(self.LineOwner.getPriceWithoutGeneration(line)['price_unit'])
        self.assertEqual(priceNoGen , 0.124)

    def test__getProfit__allOk(self):
        line = self.GisceFacturaLine.read(20972988)
        profit = self.LineOwner.getProfit(line)
        self.assertEqual(profit , 4.32)

    def test__getProfit__refundInvoice(self):
        line = self.GisceFacturaLine.read(10486898)
        profit = self.LineOwner.getProfit(line)
        self.assertEqual(profit , -0.61)

if __name__ == '__main__':
    unittest.main()

# vim: et ts=4 sw=4
