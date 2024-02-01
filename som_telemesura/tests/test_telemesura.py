import unittest
from destral import testing
from destral.transaction import Transaction
from datetime import datetime
from som_telemesura.telemesura import TmProfile


class BaseTests(testing.OOTestCase):
    def test_parse_to_utc_october(self):
        result = []
        expected_october = [
            "2017-10-28 22:00:00",
            "2017-10-28 23:00:00",
            "2017-10-29 00:00:00",
            "2017-10-29 01:00:00",
            "2017-10-29 02:00:00",
        ]
        for hour in [(0, "S"), (1, "S"), (2, "S"), (2, "W"), (3, "W")]:
            date_ = "2017-10-29 0{}:00:00".format(hour[0])
            utc_date_ = TmProfile.parse_to_utc(date_, hour[1])
            result.append(utc_date_)
        self.assertEqual(result, expected_october)

    def test_parse_to_utc_march(self):
        result = []
        expected_march = [
            "2018-03-24 23:00:00",
            "2018-03-25 00:00:00",
            "2018-03-25 01:00:00",
            "2018-03-25 02:00:00",
            "2018-03-25 03:00:00",
        ]
        for hour in [(0, "W"), (1, "W"), (3, "S"), (4, "S"), (5, "S")]:
            date_ = "2018-03-25 0{}:00:00".format(hour[0])
            utc_date_ = TmProfile.parse_to_utc(date_, hour[1])
            result.append(utc_date_)
        self.assertEqual(result, expected_march)

    def test_create_new_tm_profile(self):
        profile_obj = self.openerp.pool.get("tm.profile")
        vals = {
            "name": "456456456",
            "timestamp": "2018-01-01 01:00:00",
            "season": "W",
        }
        with Transaction().start(self.database) as txn:
            cursor = txn.cursor
            uid = txn.user
            new_id = profile_obj.create(cursor, uid, vals)
            created = profile_obj.read(
                cursor, uid, new_id, ["timestamp", "utc_timestamp", "utc_gkwh_timestamp"]
            )
            self.assertEqual(created["timestamp"], "2018-01-01 01:00:00")
            self.assertEqual(created["utc_timestamp"], "2018-01-01 00:00:00")
            self.assertEqual(created["utc_gkwh_timestamp"], "2017-12-31 23:00:00")
