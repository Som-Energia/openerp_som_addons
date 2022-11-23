# -*- coding: utf-8 -*-
import base64
import unittest

from destral import testing
from destral.transaction import Transaction
from expects import expect, raise_error
from osv.orm import except_orm
from addons import get_module_resource
import time
from tools.misc import cache
import mock
from .. import som_data_extractor


class FakeErpModel(object):
    def __init__(self, fields_def, field_values, model):
        self.model = model
        self.fields_def = fields_def
        self.field_values = field_values
    
    def fields_get(self, cursor, uid):
        return self.fields_def[self.model]

    def read(self, cursor, uid, res_id):
        return self.field_values[self.model]

class TestSomDataExtractor(testing.OOTestCase):

    def model(self, model_name):
        return self.openerp.pool.get(model_name)

    def setUp(self):
        self.txn = Transaction().start(self.database)
        self.cursor = self.txn.cursor
        self.uid = self.txn.user
        self.maxDiff = None

    def tearDown(self):
        self.txn.stop()

    @mock.patch.object(som_data_extractor.SomDataExtractor, "model_exists")
    @mock.patch.object(som_data_extractor.SomDataExtractor, "get_semantic_id")
    def test__export_simple_estructure(self, mock_get_semantic_id, mock_model_exists):
        def model_exist_mock(model):
            fields_def = {
                "fakeerpmodel": {
                    "camp_1": {'type': "char"},
                    "camp_2": {"type": "char"}
                }
            }
            field_values = {
                "fakeerpmodel": {
                    "camp_1": "a",
                    "camp_2": "b"
                }
            }
            return FakeErpModel(fields_def, field_values, model)

        mock_model_exists.side_effect = model_exist_mock
        mock_get_semantic_id.return_value = "fake-semantic-id"

        e_model = 'fakeerpmodel'
        e_id = 1
        recursion_depth = 200

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.extract_model(self.cursor, self.uid,
                                                    e_model, e_id,
                                                    recursion_depth)

        expected_result = {('fake-semantic-id', 'fakeerpmodel'): {'camp_1':"a", "camp_2":"b"}}
        self.assertDictEqual(result, expected_result)

    @mock.patch.object(som_data_extractor.SomDataExtractor, "model_exists")
    @mock.patch.object(som_data_extractor.SomDataExtractor, "get_semantic_id")
    def test__export_one_child_one_depth(self, mock_get_semantic_id, mock_model_exists):
        def model_exist_mock(model):
            fields_def = {
                "model1": {
                    "camp_1": {'type': "char"},
                    "subobjecte": {"type": "many2one", "relation": "model2"}
                },
                "model2": {
                    "subcamp1": {"type": "char"},
                    "subcamp2": {"type": "char"}
                }
            }
            field_values = {
                "model1": {
                    "camp_1": "a",
                    "subobjecte": (1, "model2")
                },
                "model2": {
                    "subcamp1": "b",
                    "subcamp2": "c"
                }
            }
            return FakeErpModel(fields_def, field_values, model)

        mock_model_exists.side_effect = model_exist_mock
        mock_get_semantic_id.return_value = "fake-semantic-id"

        e_model = 'model1'
        e_id = 1
        recursion_depth = 200

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.extract_model(self.cursor, self.uid,
                                                    e_model, e_id,
                                                    recursion_depth)
        expected_result = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a', 'subobjecte': ('fake-semantic-id', 'model2')
            },
            ('fake-semantic-id', 'model2'): {
                'subcamp2': 'c', 'subcamp1': 'b'
            }
        }

        self.assertDictEqual(result, expected_result)

    @mock.patch.object(som_data_extractor.SomDataExtractor, "model_exists")
    @mock.patch.object(som_data_extractor.SomDataExtractor, "get_semantic_id")
    def test__export_two_different_children_one_depth(self, mock_get_semantic_id, mock_model_exists):
        def model_exist_mock(model):
            fields_def = {
                "model1": {
                    "camp_1": {'type': "char"},
                    "subobjecte_1": {"type": "many2one", "relation": "model2"},
                    "subobjecte_2": {"type": "many2one", "relation": "model3"}
                },
                "model2": {
                    "subcamp1_1": {"type": "char"},
                    "subcamp1_2": {"type": "char"}
                },
                "model3": {
                    "subcamp2_1": {"type": "char"},
                    "subcamp2_2": {"type": "char"}
                }
            }
            field_values = {
                "model1": {
                    "camp_1": "a",
                    "subobjecte_1": (1, "model2"),
                    "subobjecte_2": (1, "model3")
                },
                "model2": {
                    "subcamp1_1": "b",
                    "subcamp1_2": "c"
                },
                "model3": {
                    "subcamp2_1": "d",
                    "subcamp2_2": "e"
                }
            }
            return FakeErpModel(fields_def, field_values, model)

        mock_model_exists.side_effect = model_exist_mock
        mock_get_semantic_id.return_value = "fake-semantic-id"

        e_model = 'model1'
        e_id = 1
        recursion_depth = 200

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.extract_model(self.cursor, self.uid,
                                                    e_model, e_id,
                                                    recursion_depth)
        expected_result = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a', 'subobjecte_1': ('fake-semantic-id', 'model2'), 'subobjecte_2': ('fake-semantic-id', 'model3')
            },
            ('fake-semantic-id', 'model2'): {
                'subcamp1_1': 'b', 'subcamp1_2': 'c'
            },
            ('fake-semantic-id', 'model3'): {
                'subcamp2_1': 'd', 'subcamp2_2': 'e'
            }
        }

        self.assertDictEqual(result, expected_result)

    @mock.patch.object(som_data_extractor.SomDataExtractor, "model_exists")
    @mock.patch.object(som_data_extractor.SomDataExtractor, "get_semantic_id")
    def test__export_two_same_children_one_depth(self, mock_get_semantic_id, mock_model_exists):
        def model_exist_mock(model):
            fields_def = {
                "model1": {
                    "camp_1": {'type': "char"},
                    "subobjecte_1": {"type": "many2one", "relation": "model2"},
                    "subobjecte_2": {"type": "many2one", "relation": "model2"}
                },
                "model2": {
                    "subcamp1_1": {"type": "char"},
                    "subcamp1_2": {"type": "char"}
                }
            }
            field_values = {
                "model1": {
                    "camp_1": "a",
                    "subobjecte_1": (1, "model2"),
                    "subobjecte_2": (1, "model2")
                },
                "model2": {
                    "subcamp1_1": "b",
                    "subcamp1_2": "c"
                }
            }
            return FakeErpModel(fields_def, field_values, model)

        mock_model_exists.side_effect = model_exist_mock
        mock_get_semantic_id.return_value = "fake-semantic-id"

        e_model = 'model1'
        e_id = 1
        recursion_depth = 200

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.extract_model(self.cursor, self.uid,
                                                    e_model, e_id,
                                                    recursion_depth)
        expected_result = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a', 'subobjecte_1': ('fake-semantic-id', 'model2'), 'subobjecte_2': ('fake-semantic-id', 'model2')
            },
            ('fake-semantic-id', 'model2'): {
                'subcamp1_1': 'b', 'subcamp1_2': 'c'
            }
        }

        self.assertDictEqual(result, expected_result)

    @mock.patch.object(som_data_extractor.SomDataExtractor, "model_exists")
    @mock.patch.object(som_data_extractor.SomDataExtractor, "get_semantic_id")
    def test__export_one_children_two_depth(self, mock_get_semantic_id, mock_model_exists):
        def model_exist_mock(model):
            fields_def = {
                "model1": {
                    "camp_1": {'type': "char"},
                    "subobjecte_1": {"type": "many2one", "relation": "model2"}
                },
                "model2": {
                    "subcamp1_1": {"type": "char"},
                    "subcamp1_2": {"type": "char"},
                    "subobjecte_2": {"type": "many2one", "relation": "model3"}
                },
                "model3": {
                    "subcamp2_1": {"type": "char"},
                    "subcamp2_2": {"type": "char"}
                }
            }
            field_values = {
                "model1": {
                    "camp_1": "a",
                    "subobjecte_1": (1, "model2"),
                },
                "model2": {
                    "subcamp1_1": "b",
                    "subcamp1_2": "c",
                    "subobjecte_2": (1, "model3")
                },
                "model3": {
                    "subcamp2_1": "d",
                    "subcamp2_2": "e"
                }

            }
            return FakeErpModel(fields_def, field_values, model)

        mock_model_exists.side_effect = model_exist_mock
        mock_get_semantic_id.return_value = "fake-semantic-id"

        e_model = 'model1'
        e_id = 1
        recursion_depth = 200

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.extract_model(self.cursor, self.uid,
                                                    e_model, e_id,
                                                    recursion_depth)
        expected_result = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a', 'subobjecte_1': ('fake-semantic-id', 'model2')
            },
            ('fake-semantic-id', 'model2'): {
                'subcamp1_1': 'b', 'subcamp1_2': 'c', 'subobjecte_2': ('fake-semantic-id', 'model3')
            },
            ('fake-semantic-id', 'model3'): {
                'subcamp2_1': 'd', 'subcamp2_2': 'e'
            }
        }

        self.assertDictEqual(result, expected_result)

    @mock.patch.object(som_data_extractor.SomDataExtractor, "model_exists")
    @mock.patch.object(som_data_extractor.SomDataExtractor, "get_semantic_id")
    def test__export_two_children_two_depth(self, mock_get_semantic_id, mock_model_exists):
        def model_exist_mock(model):
            fields_def = {
                "model1": {
                    "camp_1": {'type': "char"},
                    "subobjecte_1": {"type": "many2one", "relation": "model2"},
                    "subobjecte_2": {"type": "many2one", "relation": "model3"}
                },
                "model2": {
                    "subcamp1_1": {"type": "char"},
                    "subcamp1_2": {"type": "char"},
                    "subobjecte_2": {"type": "many2one", "relation": "model3"}
                },
                "model3": {
                    "subcamp2_1": {"type": "char"},
                    "subcamp2_2": {"type": "char"}
                }
            }
            field_values = {
                "model1": {
                    "camp_1": "a",
                    "subobjecte_1": (1, "model2"),
                    "subobjecte_2": (1, "model3")
                },
                "model2": {
                    "subcamp1_1": "b",
                    "subcamp1_2": "c",
                    "subobjecte_2": (1, "model3")
                },
                "model3": {
                    "subcamp2_1": "d",
                    "subcamp2_2": "e"
                }

            }
            return FakeErpModel(fields_def, field_values, model)

        mock_model_exists.side_effect = model_exist_mock
        mock_get_semantic_id.return_value = "fake-semantic-id"

        e_model = 'model1'
        e_id = 1
        recursion_depth = 200

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.extract_model(self.cursor, self.uid,
                                                    e_model, e_id,
                                                    recursion_depth)
        expected_result = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a', 'subobjecte_1': ('fake-semantic-id', 'model2'), 'subobjecte_2': ('fake-semantic-id', 'model3')
            },
            ('fake-semantic-id', 'model2'): {
                'subcamp1_1': 'b', 'subcamp1_2': 'c', 'subobjecte_2': ('fake-semantic-id', 'model3')
            },
            ('fake-semantic-id', 'model3'): {
                'subcamp2_1': 'd', 'subcamp2_2': 'e'
            }
        }

        self.assertDictEqual(result, expected_result)

    @mock.patch.object(som_data_extractor.SomDataExtractor, "model_exists")
    @mock.patch.object(som_data_extractor.SomDataExtractor, "get_semantic_id")
    def test__export_two_different_children_one_depth_limit(self, mock_get_semantic_id, mock_model_exists):
        def model_exist_mock(model):
            fields_def = {
                "model1": {
                    "camp_1": {'type': "char"},
                    "subobjecte_1": {"type": "many2one", "relation": "model2"},
                    "subobjecte_2": {"type": "many2one", "relation": "model3"}
                },
                "model2": {
                    "subcamp1_1": {"type": "char"},
                    "subcamp1_2": {"type": "char"}
                },
                "model3": {
                    "subcamp2_1": {"type": "char"},
                    "subcamp2_2": {"type": "char"}
                }
            }
            field_values = {
                "model1": {
                    "camp_1": "a",
                    "subobjecte_1": (1, "model2"),
                    "subobjecte_2": (1, "model3")
                },
                "model2": {
                    "subcamp1_1": "b",
                    "subcamp1_2": "c"
                },
                "model3": {
                    "subcamp2_1": "d",
                    "subcamp2_2": "e"
                }
            }
            return FakeErpModel(fields_def, field_values, model)

        mock_model_exists.side_effect = model_exist_mock
        mock_get_semantic_id.return_value = "fake-semantic-id"

        e_model = 'model1'
        e_id = 1
        recursion_depth = 1

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.extract_model(self.cursor, self.uid,
                                                    e_model, e_id,
                                                    recursion_depth)
        expected_result = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a'
            }
        }

        self.assertDictEqual(result, expected_result)

    def test__encode_simple_estructure(self):
        items = {('fake-semantic-id', 'fakeerpmodel'): {'camp_1':"a", "camp_2":"b"}}

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.encode_as_xml(items)

        expected_result = "<?xml version='1.0' encoding='UTF-8'?>\n"\
        '<openerp>\n'\
        '  <data>\n'\
        '    <record id="fake-semantic-id" model="fakeerpmodel">\n'\
        '      <field name="camp_1">a</field>\n'\
        '      <field name="camp_2">b</field>\n'\
        '    </record>\n'\
        '  </data>\n'\
        '</openerp>\n'
        
        self.assertEqual(result, expected_result)

    def test__encode_one_child_one_depth(self):
        items = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a', 'subobjecte': ('fake-semantic-id', 'model2')
            },
            ('fake-semantic-id', 'model2'): {
                'subcamp2': 'c', 'subcamp1': 'b'
            }
        }

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.encode_as_xml(items)

        expected_result = "<?xml version='1.0' encoding='UTF-8'?>\n"\
        '<openerp>\n'\
        '  <data>\n'\
        '    <record id="fake-semantic-id" model="model2">\n'\
        '      <field name="subcamp2">c</field>\n'\
        '      <field name="subcamp1">b</field>\n'\
        '    </record>\n'\
        '    <record id="fake-semantic-id" model="model1">\n'\
        '      <field name="camp_1">a</field>\n'\
        '      <field name="subobjecte" ref="model2.fake-semantic-id"/>\n'\
        '    </record>\n'\
        '  </data>\n'\
        '</openerp>\n'

        self.assertEqual(result, expected_result)

    def test__encode_two_children_two_depth(self):
        items = {
            ('fake-semantic-id', 'model1'): {
                'camp_1': 'a', 'subobjecte_1': ('fake-semantic-id', 'model2'), 'subobjecte_2': ('fake-semantic-id', 'model3')
            },
            ('fake-semantic-id', 'model2'): {
                'subcamp1_1': 'b', 'subcamp1_2': 'c', 'subobjecte_2': ('fake-semantic-id', 'model3')
            },
            ('fake-semantic-id', 'model3'): {
                'subcamp2_1': 'd', 'subcamp2_2': 'e'
            }
        }

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.encode_as_xml(items)

        expected_result = "<?xml version='1.0' encoding='UTF-8'?>\n"\
        '<openerp>\n'\
        '  <data>\n'\
        '    <record id="fake-semantic-id" model="model2">\n'\
        '      <field name="subcamp1_1">b</field>\n'\
        '      <field name="subcamp1_2">c</field>\n'\
        '      <field name="subobjecte_2" ref="model3.fake-semantic-id"/>\n'\
        '    </record>\n'\
        '    <record id="fake-semantic-id" model="model1">\n'\
        '      <field name="camp_1">a</field>\n'\
        '      <field name="subobjecte_1" ref="model2.fake-semantic-id"/>\n'\
        '      <field name="subobjecte_2" ref="model3.fake-semantic-id"/>\n'\
        '    </record>\n'\
        '    <record id="fake-semantic-id" model="model3">\n'\
        '      <field name="subcamp2_2">e</field>\n'\
        '      <field name="subcamp2_1">d</field>\n'\
        '    </record>\n'\
        '  </data>\n'\
        '</openerp>\n'

        self.assertEqual(result, expected_result)

    def test__encode_simple_estructure_with_boolean(self):
        items = {('fake-semantic-id', 'fakeerpmodel'): {'camp_1':"a", "camp_2":"b", "camp_3":True, "camp_4":False}}

        data_extractor = self.model('som.data.extractor')
        result = data_extractor.encode_as_xml(items)

        expected_result = "<?xml version='1.0' encoding='UTF-8'?>\n"\
        '<openerp>\n'\
        '  <data>\n'\
        '    <record id="fake-semantic-id" model="fakeerpmodel">\n'\
        '      <field name="camp_1">a</field>\n'\
        '      <field name="camp_2">b</field>\n'\
        '      <field name="camp_3">True</field>\n'\
        '      <field name="camp_4">False</field>\n'\
        '    </record>\n'\
        '  </data>\n'\
        '</openerp>\n'

        self.assertEqual(result, expected_result)
