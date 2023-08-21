# -*- coding: utf-8 -*-
from osv import osv
from www_som import exceptions
from decorator import decorator

def www_entry_point(expected_exceptions=tuple()):

    def wrapper(f, self, cursor, *args, **kwds):
        """
        Wrapps an erp method so that it can be called safely from the web.

        - Establishes a database savepoint to return at if an exception happens.
        - Translates any expected_exceptions to a error dictionary.
        - Any other exception will be also translated but with code 'Unexpected'
        - To any exception, expected or unexpected,
          it adds the backtrace as attribute of the dictionary.
        """
        def traceback_info(exception):
            import traceback
            import sys
            exc_type, exc_value, exc_tb = sys.exc_info()
            return traceback.format_exception(exc_type, exc_value, exc_tb)

        savepoint = 'change_pricelist_{}'.format(id(cursor))
        cursor.savepoint(savepoint)
        try:
            return f(self, cursor, *args, **kwds)
        except expected_exceptions as e:
            cursor.rollback(savepoint)
            return dict(
                e.to_dict(),
                trace=traceback_info(e),
            )
        except Exception as e:
            cursor.rollback(savepoint)
            return dict(
                error=str(e),
                code="Unexpected",
                trace=traceback_info(e),
            )
    return decorator(wrapper)

