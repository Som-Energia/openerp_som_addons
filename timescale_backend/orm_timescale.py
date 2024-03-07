from osv import orm, fields
from osv.orm import except_orm
import netsvc
import re
import pymongo
import gridfs
from bson.objectid import ObjectId
from datetime import datetime
from numbers import Number
from tools.translate import _
import tools
from sql_db import Cursor

class orm_timescale(orm.Timescale):

    _protected = ['read', 'write', 'create', 'default_get', 'perm_read',
                  'unlink', 'fields_get', 'fields_view_get', 'search',
                  'name_get', 'distinct_field_get', 'name_search', 'copy',
                  'import_data', 'search_count', 'exists']
    _inherit_fields = {}

    def ts_cursor(self):
        return Cursor(self._pool, self.dbname, prefix='ts_')

    def q(self, cursor, uid):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).q(ts_cursor, uid)

    def _parent_store_compute(self, cr):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._parent_store_compute(ts_cursor, uid)

    def _update_store(self, cr, f, k):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._update_store(ts_cursor, f, k)

    def _check_removed_columns(self, cr, log=False):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._check_removed_columns(ts_cursor, log)

    def _auto_init(self, cr, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._auto_init(ts_cursor, context)

    def __init__(self, cr):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).__init__(ts_cursor)

    def default_get(self, cr, uid, fields_list, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).default_get(ts_cursor, uid, fields_list, context)

    def check_perm(self, cr, user, perm, raise_exception=False, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).default_get(ts_cursor, user, perm, raise_exception, context)

    def fields_get(self, cr, user, fields=None, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).fields_get(ts_cursor, user, fields, context)

    def sorted_read(self, cursor, user, ids, fields=None, context=None, load='_classic_read'):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).sorted_read(ts_cursor, user, ids, fields, context, load)

    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).read(ts_cursor, user, ids, fields, context, load='_classic_read')

    def _read_flat(self, cr, user, ids, fields_to_read, context=None, load='_classic_read'):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._read_flat(ts_cursor, user, ids, fields_to_read, context, load)

    def perm_read(self, cr, user, ids, context=None, details=True):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).perm_read(ts_cursor, user, ids, context, details)

    def _check_concurrency(self, cr, ids, context):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).perm_read(ts_cursor, ids, context)

    def unlink(self, cr, uid, ids, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).perm_read(ts_cursor, uid, ids, context)

    def write(self, cr, user, ids, vals, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).write(ts_cursor, user, ids, vals, context)

    def create(self, cr, user, vals, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self).create(ts_cursor, user, vals, context)

    def _store_get_values(self, cr, user, vals, context):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_get_values(ts_cursor, user, vals, context)

    def _store_set_values(self, cr, uid, ids, fields, context):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, uid, ids, fields, context)

    def _where_calc(self, cr, user, args, active_test=True, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, user, args, active_test, context)

    def estimate_count(self, cr):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor)

    def search(self, cr, user, args, offset=0, limit=None, order=None,
               context=None, count=False):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, user, args, offset, limit, order, context, count)

    def search_reader(self, cr, user, args, fields=[], offset=0, limit=None, order=None, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, user, args, fields, offset, limit, order, context)

    def distinct_field_get(self, cr, uid, field, value, args=None, offset=0, limit=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, uid, field, value, args, offset, limit)

    def name_get(self, cr, user, ids, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, user, ids, context)

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, user, name, args, operator, context, limit)

    def copy_data(self, cr, uid, id, default=None, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, uid, id, default, context)

    def copy_translations(self, cr, uid, old_id, new_id, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, uid, old_id, new_id, context)

    def copy(self, cr, uid, id, default=None, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, uid, id, default, context)

    def exists(self, cr, uid, id, context=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, uid, id, context)

    def check_recursion(self, cr, uid, ids, parent=None):
        ts_cursor = self.ts_cursor()
        super(orm_timescale, self)._store_set_values(ts_cursor, uid, ids, parent)

