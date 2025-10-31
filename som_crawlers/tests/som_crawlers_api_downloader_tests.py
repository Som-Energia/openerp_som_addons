# -*- coding: utf-8 -*-
from destral import testing
from som_crawlers.api_downloaders import get_instance_from_api_module
from som_crawlers.api_downloaders.iberdrola import is_empty_zip


class SomCrawlersApiDownloaderTests(testing.OOTestCaseWithCursor):

    def setUp(self):
        super(SomCrawlersApiDownloaderTests, self).setUp()
        self.pool = self.openerp.pool
        self.cr = self.cursor

    def test_get_instance_from_api_module(self):
        data_obj = self.pool.get("ir.model.data")
        config_obj = self.pool.get("som.crawlers.config")

        iberdrola_conf_id = data_obj.get_object_reference(
            self.cr, self.uid, "som_crawlers", "iberdrola_conf"
        )[1]
        iberdrola_conf = config_obj.browse(self.cr, self.uid, iberdrola_conf_id)

        instance = get_instance_from_api_module(iberdrola_conf, "iberdrola")
        self.assertEqual(instance.name, "iberdrola")

        instance = get_instance_from_api_module(iberdrola_conf, "iberdrola", process="c2")
        self.assertEqual(instance.name, "iberdrola_c2")

    def test_is_empty_zip(self):
        with self.assertRaises(Exception):
            is_empty_zip(b"")

        empty_zip_bytes = (
            b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        self.assertTrue(is_empty_zip(empty_zip_bytes))

        zip_with_files_bytes = (
            b"PK\x03\x04\x14\x00\x08\x00\x08\x00\xb4{0[\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00M\x00\x00\x00GRCW_I-DE Redes El\x82ctricas Inteligentes, S.A.U._SOM ENERGIA SCCL_"
            b"C2_111_0.xml\x95R]k\xc20\x14\xfd+\xd2w\xd7\xa4Xu\x12#\xaeV\xf0a[\xb1\xdb\xc3\x1ecz"
            b"\xd1\x8c4W\x9a(c\xbf~\xa9\xb8Z\xbf`\x0b\x81\xdc\xdcs\xee\xb9\x87\x9b\xb0\xc9W\xa9;"
            b"{\xa8\xacB3\x0e\xe8\x03\t:`$\x16\xca\xac\xc7\xc1\"\x7f\xed\x0e\x87\xf1c\x97\x06\x13"
            b"\xce\x9e\xc1X\xf1\tS\t[\'\xa4\xe7\'\xa2\\), \xc1\x12*\xa9\x84V\xdf\xa2\xc0*\xf7\x01"
            b"\x18\x07\x1d/m\xec8\xd88\xb7\x1d\x85\xa1F)\xf4\x06\xad\x0bA\xc3Z\xad\x94V\x85(\x02"
            b"\xce\x12\xb1\x02\t\x95\xf0\x91\xef\xbb\xc6e\x9a\xa6\xe5\xb6\x02+\xd2RY\xf4\x00!\x11e"
            b"\xe1=\xf4\xaal\x06\xd6)\x83\x9c\x0c\xfa\xd1u\xd9/z,\x9b\x81\xce*\x94`\x91\'\r\xbb"
            b"\x95lh\x99\xf07JO\x94C\xa2\x81s\xd4J*\xb7+xD\xa28&\xb4\xdf\xeb\xd1\x96\xe0\tg9\xc8"
            b"\x9d\x1f\xb2\x1fX;M\xbc\xf4m\x84\xcdAn\xc4y\x83.\x19ti\xfcF\xe9\x88\x0cG\xb4\xcf\xc2"
            b"\x0b\x0eK\xde\xb3\x9c\xa7y=:R/\xda\xf3\x9b\x0e>\x96d\xeeM\xd5\xa0?\x9a\xc9_>\xea\x9d"
            b"\'=Z\x99J\xa7\xf6\x07vV\xc1^Y\'Z\x9e\x8eVnp\xd8\xc2\x14Oh0\xc7Z\x99\xbf\xb0\xf0<\xc1"
            b"\xc2?\xdb\x08\xff\xfb\x19\xf9\x0fPK\x07\x08\x11\xc9\xfd\xcaK\x01\x00\x00\xea\x02\x00"
            b"\x00PK\x01\x02\x14\x00\x14\x00\x08\x00\x08\x00\xb4{0[\x11\xc9\xfd\xcaK\x01\x00\x00"
            b"\xea\x02\x00\x00M\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"GRCW_I-DE Redes El\x82ctricas Inteligentes, S.A.U._SOM ENERGIA SCCL_C2_111_0.xmlPK"
            b"\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00{\x00\x00\x00\xc6\x01\x00\x00\x00\x00"
        )
        self.assertFalse(is_empty_zip(zip_with_files_bytes))
