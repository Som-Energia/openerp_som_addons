#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

dbconfig = None
try:
    import dbconfig
except ImportError:
    pass
import datetime
from yamlns import namespace as ns
import erppeek_wst
from generationkwh.testutils import assertNsEqual


@unittest.skipIf(not dbconfig, "depends on ERP")
class MailMockup_Test(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None
        self.b2bdatapath="b2bdata"
        self.personalData = ns(dbconfig.personaldata)
        self.erp = erppeek_wst.ClientWST(**dbconfig.erppeek)
        self.erp.begin()
        self.MailMockup = self.erp.GenerationkwhMailmockup

    def tearDown(self):
        self.erp.rollback()
        self.erp.close()

    assertNsEqual=assertNsEqual

    #TODO: move this in a utils class (copy pasted from Investment_Amortization_Test
    def assertLogEquals(self, log, expected):                                                             
        for x in log.splitlines():
            self.assertRegexpMatches(x,
                u'\\[\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}.\\d+ [^]]+\\] .*',
                u"Linia de log con formato no estandard"
            )

        logContent = ''.join(
                x.split('] ')[1]+'\n'
                for x in log.splitlines()
                if u'] ' in x
                )
        self.assertMultiLineEqual(logContent, expected)

    def test_isActive_whenNotActivatedYet(self):
        self.MailMockup.deactivate()
        self.assertFalse(self.MailMockup.isActive())

    def test_isActive_activated(self):
        self.MailMockup.activate()
        self.assertTrue(self.MailMockup.isActive())
        self.MailMockup.deactivate()
        self.assertFalse(self.MailMockup.isActive())

    def test_log(self):
        self.MailMockup.activate()
        self.MailMockup.send_mail(ns(attribute='value').dump())
        self.assertNsEqual(self.MailMockup.log(), """
            logs:
            - attribute: value
            """)
        self.MailMockup.deactivate()

    def test_log_calledTwice(self):
        self.MailMockup.activate()
        self.MailMockup.send_mail(ns(attribute='value1').dump())
        self.MailMockup.send_mail(ns(otherattrib='value2').dump())
        self.assertNsEqual(self.MailMockup.log(), """
            logs:
            - attribute: value1
            - otherattrib: value2
            """)
        self.MailMockup.deactivate()

    def test_log_ciclesGetSeparated(self):
        self.MailMockup.activate()
        self.MailMockup.send_mail(ns(attribute='value1').dump())
        self.MailMockup.activate()
        self.MailMockup.send_mail(ns(otherattrib='value2').dump())
        self.assertNsEqual(self.MailMockup.log(), """
            logs:
            - otherattrib: value2
            """)
        self.MailMockup.deactivate()


		




unittest.TestCase.__str__ = unittest.TestCase.id


if __name__=='__main__':
    unittest.main()

# vim: et ts=4 sw=4
