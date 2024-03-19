from mongodb_backend import osv_mongodb
from osv import fields
from giscedata_telemesura.telemesura import TIMEZONE
from datetime import datetime, timedelta
import pytz


class TmProfile(osv_mongodb.osv_mongodb):

    _name = "tm.profile"
    _inherit = "tm.profile"

    @staticmethod
    def parse_to_utc(timestamp, season):
        date_ = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        if season == "W":
            dst = False
        else:
            dst = True
        utc_date_ = TIMEZONE.localize(date_, is_dst=dst).astimezone(pytz.utc)
        return utc_date_.strftime("%Y-%m-%d %H:%M:%S")

    def create(self, cursor, uid, vals, context=None):

        if vals.get("timestamp", False):
            utc_ts = self.parse_to_utc(vals["timestamp"], vals["season"])
            utc_ts_minus_one = datetime.strptime(utc_ts, "%Y-%m-%d %H:%M:%S") - timedelta(hours=1)
            vals["utc_timestamp"] = utc_ts
            vals["utc_gkwh_timestamp"] = utc_ts_minus_one.strftime("%Y-%m-%d %H:%M:%S")
        res = super(TmProfile, self).create(cursor, uid, vals, context)
        return res

    def write(self, cursor, uid, ids, vals, context=None):
        # Ensure integrity between timestamp and utc_timestamp in case anyone
        # changes timestamp value. Ignore if they change utc_timestamp
        vals.pop("utc_timestamp", None)
        vals.pop("utc_gkwh_timestamp", None)
        if vals.get("timestamp", False):
            utc_ts = self.parse_to_utc(vals["timestamp"], vals["season"])
            utc_ts_minus_one = datetime.strptime(utc_ts, "%Y-%m-%d %H:%M:%S") - timedelta(hours=1)
            vals["utc_timestamp"] = utc_ts
            vals["utc_gkwh_timestamp"] = utc_ts_minus_one.strftime("%Y-%m-%d %H:%M:%S")
        res = super(TmProfile, self).write(cursor, uid, ids, vals, context)
        return res

    _columns = {
        "utc_timestamp": fields.datetime("UTC Timestamp"),
        "utc_gkwh_timestamp": fields.datetime("UTC-1h Timestamp"),
    }


TmProfile()
