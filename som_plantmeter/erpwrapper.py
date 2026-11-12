# -*- coding: utf8 -*-

class ErpWrapper(object):
    """
        Base class for classes that need to access OpenERP functionality
        but has to offer methods without OpenERP bullshit params.

        Such params are passed to the constructor instead so that
        the rest of the methods can access them internally as attributes.

        Example:

            class MyClass(ErpWrapper):
                def clientsByLang(self, lang):
                    Partner=self.erp.pool.get('res.partner')
                    return Partner.search(self.cursor, self.uid, [
                        ('lang','=',lang),
                        ], context=self.context)
    """

    def __init__(self, erp, cursor, uid, context=None):
        self.erp = erp
        self.cursor = cursor
        self.uid = uid
        self.context = context


