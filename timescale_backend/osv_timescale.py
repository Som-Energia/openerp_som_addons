import copy

from osv.osv import module_class_list, module_list, class_pool
import orm_timescale


class osv_timescale(orm_timescale.orm_timescale):

    def __new__(cls):
        module = str(cls)[6:]
        module = module[:len(module) - 1]
        module = module.split('.')[0][2:]
        if not hasattr(cls, '_module'):
            cls._module = module
        module_class_list.setdefault(cls._module, []).append(cls)
        class_pool[cls._name] = cls
        if module not in module_list:
            module_list.append(cls._module)
        return None

    def createInstance(cls, pool, module, cr):
        parent_name = hasattr(cls, '_inherit') and cls._inherit
        if parent_name:
            parent_class = pool.get(parent_name).__class__
            assert pool.get(parent_name), \
                "parent class %s does not exist in module %s !" % (
                    parent_name, module
                )
            nattr = {}
            for s in ('_columns', '_defaults'):
                pool_obj = pool.get(parent_name)
                if not hasattr(pool_obj, s):
                    continue
                new = copy.copy(getattr(pool_obj, s))
                if hasattr(new, 'update'):
                    new.update(cls.__dict__.get(s, {}))
                else:
                    new.extend(cls.__dict__.get(s, []))
                nattr[s] = new
            name = hasattr(cls, '_name') and cls._name or cls._inherit
            if cls in parent_class.mro():
                cls = parent_class
            else:
                cls = type(name, (cls, parent_class), nattr)
        obj = object.__new__(cls)
        obj.__init__(pool, cr)
        return obj
    createInstance = classmethod(createInstance)

    def __init__(self, pool, cr):
        pool.add(self._name, self)
        self.pool = pool
        orm_timescale.orm_timescale.__init__(self, cr)