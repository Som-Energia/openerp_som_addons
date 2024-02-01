# -*- coding: utf-8 -*-
from osv import osv
from som_polissa.exceptions import exceptions
from decorator import decorator


def www_entry_point(expected_exceptions=tuple()):
    """
    Wrapps an erp method so that it can be called safely from the web.

    - Establishes a database savepoint to return at if an exception happens.
    - Translates any expected_exceptions to a error dictionary.
    - Any other exception will be also translated but with code 'Unexpected'
    - To any exception, expected or unexpected,
      it adds the backtrace as attribute of the dictionary.

    Usage:
    ```
    @www_entry_point(
        expected_exceptions=(
            MyException,
            MyOtherException,
        )
    )
    def my_erp_method(self, cursor ...):
        ...
        if error: raise MyException(args)
        ...
        return dict(
            ok=True,
            data=...,
        )
    ```

    Expected errors should have the to_dict method that will return
    relevant data to identify the causes of the error.
    """

    def wrapper(f, self, cursor, *args, **kwds):
        def traceback_info(exception):
            import traceback
            import sys

            exc_type, exc_value, exc_tb = sys.exc_info()
            return traceback.format_exception(exc_type, exc_value, exc_tb)

        savepoint = "change_pricelist_{}".format(id(cursor))
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
