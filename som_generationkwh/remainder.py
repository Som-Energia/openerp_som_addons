# -*- coding: utf-8 -*-

from osv import osv, fields
from .erpwrapper import ErpWrapper

from generationkwh.isodates import isodate

class RemainderProvider(ErpWrapper):

    def lastRemainders(self):
        Remainder=self.erp.pool.get('generationkwh.remainder')
        return Remainder.lastRemainders(self.cursor,self.uid, context=self.context)


    def updateRemainders(self,remainders):
        Remainder=self.erp.pool.get('generationkwh.remainder')
        Remainder.updateRemainders(self.cursor,self.uid,remainders, context=self.context)

    def init(self, nSharesToInit):
        """
            Creates a initial remainder with 0Wh for the many nSharesToInit
            received at the same date than the first remainder for 1-shares.
            If there is no remainder with nshares = 1 then...
        """
        Remainder=self.erp.pool.get('generationkwh.remainder')
        Remainder.newRemaindersToTrack(self.cursor,self.uid, nSharesToInit, context=self.context)

    def filled(self):       
        Remainder=self.erp.pool.get('generationkwh.remainder')
        return Remainder.filled(self.cursor,self.uid,context=self.context)


class GenerationkWhRemainder(osv.osv):
    """
    Remainders, in Wh, after dividing the aggregated
    production of the plants into a hourly curve of
    available kWh for a member with a given number of
    shares.
    """

    _name = "generationkwh.remainder"
    _columns = dict(
        n_shares=fields.integer(
            required=True,
            help="Number of shares"
        ),
        target_day=fields.date(
            required=True,
            help="Day after the last day computed. The one to carry the remainder on."
        ),
        remainder_wh=fields.integer(
            required=True,
            help="Remainder in Wh"
        )
    )

    _sql_constraints = [(
        'unique_n_shares_target_day', 'unique(n_shares,target_day)',
            'Only one remainder of last date computed and number of shares '
            'is allowed'
        )]

    def lastRemainders(self, cr, uid, context=None):
        "Returns the latest remainder for each number of shares."""

        cr.execute("""
            SELECT r.n_shares,r.target_day,r.remainder_wh
                FROM generationkwh_remainder AS r
                LEFT JOIN generationkwh_remainder AS r2
                    ON r.n_shares=r2.n_shares
                    AND r.target_day < r2.target_day
                WHERE r2.target_day IS NULL
                ORDER BY r.n_shares
            """)
        result = [
            (
                n_shares,
                isodate(target_day),
                remainder_wh,
            ) for n_shares, target_day, remainder_wh in cr.fetchall()
        ]
        return result

    def updateRemainders(self, cr, uid, remainders, context=None):
        for n,pointsDate,remainder in remainders:
            same_date_n_id=self.search(cr, uid, [
                ('n_shares','=',n),
                ('target_day','=', pointsDate),
            ], context=context)
            if same_date_n_id:
                self.unlink(
                    cr, uid,
                    same_date_n_id, context=context
                )
            self.create(cr,uid,{
                'n_shares': n,
                'target_day': pointsDate,
                'remainder_wh': remainder
            }, context=context)

    def clean(self,cr,uid,context=None):
        ids=self.search(cr,uid, [], context=context)
        self.unlink(cr,uid,ids)

    def newRemaindersToTrack(self,cr,uid,nshares,context=None):
        """
            Add an startup remainder for each number of shares
            provided, with 0Wh and the date of the first 1-share
            remainder.
            If no 1-share remainder exists, it has no effect.
        """
        cr.execute("""
            SELECT r.n_shares,r.target_day,r.remainder_wh
            FROM generationkwh_remainder AS r
            WHERE n_shares = 1
            ORDER BY r.target_day ASC LIMIT 1
            """)

        first1ShareRemainder = cr.fetchone()
        if first1ShareRemainder is None: return
        _,date,_ = first1ShareRemainder
        self.updateRemainders(cr,uid,[
            (n,date,0)
            for n in nshares
            ] ,context)

    def filled(self,cr,uid,context=None):
        """Returns a list of n-shares that have two or more remainders,
        meaning that besides initialization, some data has been added."""

        cr.execute("""
            SELECT r.n_shares
                FROM generationkwh_remainder AS r
                GROUP BY r.n_shares
                HAVING count(r.id)>1
            """)
        result = [
            n_shares
            for n_shares, in cr.fetchall()
        ]
        return result
        


GenerationkWhRemainder()


class GenerationkWhRemainderTesthelper(osv.osv):
    '''Implements generationkwh remainder testhelper '''

    _name = "generationkwh.remainder.testhelper"
    _auto = False

    def lastRemainders(self, cr, uid, context=None):

        remainder = self.pool.get('generationkwh.remainder')
        remainders = remainder.lastRemainders(cr, uid, context)
        return [(r[0], str(r[1]), r[2]) for r in remainders]

    def updateRemainders(self, cr, uid, remainders, context=None):
        remainder = self.pool.get('generationkwh.remainder')
        remainder.updateRemainders(cr, uid, [
            (nshares, str(target_day), remainder_wh)
            for nshares, target_day, remainder_wh in remainders
            ], context)

    def clean(self,cr,uid,context=None):
        remainder = self.pool.get('generationkwh.remainder')
        remainder.clean(cr, uid, context)


GenerationkWhRemainderTesthelper()

