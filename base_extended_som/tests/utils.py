import mock
import contextlib


@contextlib.contextmanager
def avoid_creating_subcursors(cursor):
    orig_commit = cursor.commit
    orig_close = cursor.close
    orig_rollback = cursor.rollback

    def forbidden_rollback(*a, **kw):
        raise AssertionError("Rollback called: failing test")

    cursor.commit = lambda: None
    cursor.close = lambda: None
    cursor.rollback = forbidden_rollback

    with mock.patch('pooler.get_db') as get_db_mock:
        get_db_mock.return_value.cursor.return_value = cursor
        yield

    cursor.commit = orig_commit
    cursor.close = orig_close
    cursor.rollback = orig_rollback
