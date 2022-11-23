# -*- coding: utf-8 -*-
from osv import osv
from lxml import etree
from slugify import slugify


class SomDataExtractor(osv.osv_memory):

    _name = 'som.data.extractor'

    def model_exists(self, model):
        obj = self.pool.get(model)
        if obj is None:
            raise Exception('Model {0} does not exist!'.format(model))
        return obj

    def get_semantic_id(self, cursor, uid, model_obj, res_id):
        return '{0}_{1}_{2}'.format(
                model_obj._table,
                slugify(model_obj.name_get(cursor, uid, [res_id])[0][1]),
                res_id
            )

    def extract_model(self, cursor, uid,
                      model, res_id, max_depth,
                      context=None):
        if context is None:
            context = {}
        entity_dict = {}
        depth = 1
        self.extract_model_r(cursor, uid,
                             model, res_id, depth, max_depth,
                             entity_dict, context)
        return entity_dict

    def extract_model_r(self, cursor, uid,
                        model, res_id, depth, max_depth,
                        entity_dict, context):

        if max_depth and depth > max_depth:
            return {None: {}}

        result = {}

        model_obj = self.model_exists(model)

        fields_def = model_obj.fields_get(cursor, uid)

        name_id = self.get_semantic_id(cursor, uid, model_obj, res_id)
        key = (name_id, model)
        if key in entity_dict:
            result[key] = entity_dict[key]
        else:
            extracted_data = {}
            result[key] = extracted_data
            entity_dict[key] = extracted_data
            for field, value in model_obj.read(cursor, uid, res_id).items():
                if field not in fields_def:
                    continue

                field_def = fields_def[field]
                field_type = field_def['type']

                if field_type == 'many2many':
                    pass
                elif field_type == 'one2many':
                    pass
                elif field_type == 'many2one':
                    if value:
                        inner = self.extract_model_r(cursor, uid,
                                                     field_def['relation'],
                                                     value[0],
                                                     depth+1, max_depth,
                                                     entity_dict, context)
                        if inner.keys()[0] not in [None, False]:
                            extracted_data[field] = inner.keys()[0]
                else:
                    if field_type == 'date' and value == False:
                        value = ''
                    extracted_data[field] = value
        return result

    def encode_as_xml(self, items):
        root = etree.Element("openerp")
        data = etree.SubElement(root, u'data')
        for name, item in items.items():
            record = etree.SubElement(data, u'record')
            self._parse_extracted_item(record, name, item)

        return etree.tostring(root,
                              xml_declaration=True,
                              encoding='UTF-8',
                              pretty_print=True)

    def _parse_extracted_item(self, record, name, item):
        record.set(u'id',name[0])
        record.set(u'model',name[1])

        for name,value in item.items():
            field = etree.SubElement(record, u'field')
            field.set(u'name',name)
            if type(value) == tuple:
                model = value[1].replace('.','_')
                s_id = value[0]
                field.set(u'ref',model+u'.'+s_id)
            elif type(value) not in (str,unicode):
                field.text = str(value)
            else:
                field.text = value

    def extract_model_as_xml(self, cursor, uid,
                             model, res_id, max_depth,
                             context=None):
        model_data = self.extract_model(cursor, uid,
                                        model, res_id, max_depth,
                                        context)
        return self.encode_as_xml(model_data)


SomDataExtractor()
