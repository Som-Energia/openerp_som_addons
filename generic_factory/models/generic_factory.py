# -*- coding: utf-8 -*-
from osv import osv
from faker import Faker
fake = Faker()


class GenericFactory(osv.osv):
    _name = "generic.factory"
    _description = "Generic Factory to create records for testing"

    def create(self, cursor, uid, model_name, overrides, depth=0):
        model = self.pool.get(model_name)
        vals = {}
        for name, field in model._columns.items():
            if field.required and name not in overrides:
                vals[name] = self._fake_value_for_field(cursor, uid, field, depth)
        # Afegeix/trepitja amb els valors que passen per paràmetre
        vals.update(overrides)

        record = model.create(cursor, uid, vals)
        return record

    def _fake_value_for_field(self, cursor, uid, field, depth):
        """Genera valors falsos segons el tipus de camp"""
        depth += 1
        if depth > 10:
            return False
        t = field._type
        if t in ('char', 'text', 'html'):
            return fake.word()
        elif t == 'integer':
            return fake.random_int(1, 1000)
        elif t == 'float':
            return fake.pyfloat(left_digits=2, right_digits=2, positive=True)
        elif t == 'boolean':
            return fake.boolean()
        elif t == 'date':
            return fake.date_this_decade()
        elif t == 'datetime':
            return fake.date_time_this_decade()
        elif t == 'selection':
            return field.selection and field.selection[0][0]
        elif t == 'many2one':
            try:
                comodel = field.relation
            except AttributeError:
                comodel = field._obj
            return self.create(cursor, uid, comodel, {}, depth)
        elif t in ('one2many', 'many2many'):
            return [(6, 0, [])]
        else:
            return False


GenericFactory()
