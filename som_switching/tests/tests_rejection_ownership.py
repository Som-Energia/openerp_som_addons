# -*- coding: utf-8 -*-
from __future__ import absolute_import

from destral import testing
from tools.misc import cache


class TestRejectionOwnership(testing.OOTestCaseWithCursor):
    require_demo_data = True

    def setUp(self):
        super(TestRejectionOwnership, self).setUp()
        self.headers = self.pool.get("giscedata.switching.step.header")
        self.rejections = self.pool.get("giscedata.switching.rebuig")
        data = self.pool.get("ir.model.data")
        self.case_id = data.get_object_reference(
            self.cursor, self.uid, "som_switching", "sw_001"
        )[1]
        self.partner_id = data.get_object_reference(
            self.cursor, self.uid, "base", "main_partner"
        )[1]
        self.reason_id = data.get_object_reference(
            self.cursor, self.uid, "giscedata_switching", "sw_motiu_rebuig_40"
        )[1]

    def create_header(self):
        return self.headers.create(self.cursor, self.uid, {
            "sw_id": self.case_id,
            "emisor_id": self.partner_id,
            "receptor_id": self.partner_id,
            "date_created": "2026-11-25 10:00:00",
            "rebuig_ids": [(0, 0, {
                "seq_rebuig": 1,
                "motiu_rebuig": self.reason_id,
                "desc_rebuig": "Existing request in progress",
            })],
        })

    def rejection_ids(self, header_id):
        return self.headers.read(
            self.cursor, self.uid, header_id, ["rebuig_ids"]
        )["rebuig_ids"]

    def test_copied_header_owns_independent_rejections(self):
        original_id = self.create_header()
        original_rejections = self.rejection_ids(original_id)
        copied_id = self.headers.copy(self.cursor, self.uid, original_id)
        copied_rejections = self.rejection_ids(copied_id)

        self.assertEqual(len(copied_rejections), 1)
        self.assertNotEqual(original_rejections, copied_rejections)
        fields = ["seq_rebuig", "motiu_rebuig", "desc_rebuig"]
        original = self.rejections.read(
            self.cursor, self.uid, original_rejections[0], fields
        )
        copied = self.rejections.read(
            self.cursor, self.uid, copied_rejections[0], fields
        )
        original.pop("id")
        copied.pop("id")
        self.assertEqual(original, copied)
        self.headers.unlink(self.cursor, self.uid, [copied_id])
        self.assertEqual(self.rejection_ids(original_id), original_rejections)

    def test_deleting_legacy_shared_rejection_preserves_other_header(self):
        original_id = self.create_header()
        original_rejections = self.rejection_ids(original_id)
        copied_id = self.headers.copy(self.cursor, self.uid, original_id)
        copied_rejections = self.rejection_ids(copied_id)
        # Recreate the sharing left by copies made before the fix.
        self.headers.write(
            self.cursor, self.uid, [copied_id],
            {"rebuig_ids": [(6, 0, original_rejections)]},
        )
        self.rejections.unlink(self.cursor, self.uid, copied_rejections)

        self.headers.unlink(self.cursor, self.uid, [copied_id])

        self.assertEqual(self.rejection_ids(original_id), original_rejections)
        self.headers.unlink(self.cursor, self.uid, [original_id])
        self.assertEqual(
            self.rejections.search(
                self.cursor, self.uid, [("id", "in", original_rejections)]
            ),
            [],
        )

    def test_deleting_shared_headers_in_batch_cleans_orphaned_rejections(self):
        first_id = self.create_header()
        second_id = self.create_header()
        first_rejections = self.rejection_ids(first_id)
        second_rejections = self.rejection_ids(second_id)
        self.headers.write(
            self.cursor, self.uid, [second_id],
            {"rebuig_ids": [(4, rejection_id) for rejection_id in first_rejections]},
        )

        self.headers.unlink(self.cursor, self.uid, [first_id, second_id])

        self.assertEqual(
            self.rejections.search(
                self.cursor, self.uid,
                [("id", "in", first_rejections + second_rejections)],
            ),
            [],
        )

    def test_batch_deletion_preserves_rejections_referenced_outside_batch(self):
        first_id = self.create_header()
        second_id = self.create_header()
        surviving_id = self.create_header()
        shared_rejections = self.rejection_ids(first_id)
        private_rejections = self.rejection_ids(second_id)
        for header_id in [second_id, surviving_id]:
            self.headers.write(
                self.cursor, self.uid, [header_id],
                {"rebuig_ids": [
                    (4, rejection_id) for rejection_id in shared_rejections
                ]},
            )

        self.headers.unlink(self.cursor, self.uid, [first_id, second_id])

        self.assertTrue(
            set(shared_rejections).issubset(self.rejection_ids(surviving_id))
        )
        self.assertEqual(
            self.rejections.search(
                self.cursor, self.uid, [("id", "in", private_rejections)]
            ),
            [],
        )

    def test_copying_inherited_step_owns_independent_rejections(self):
        header_id = self.create_header()
        steps = self.pool.get("giscedata.switching.a3.02")
        step_id = steps.create(self.cursor, self.uid, {
            "header_id": header_id,
            "rebuig": True,
            "data_rebuig": "2026-11-25",
        })
        original_rejections = self.rejection_ids(header_id)

        copied_id = steps.copy(self.cursor, self.uid, step_id)

        copied = steps.read(
            self.cursor, self.uid, copied_id, ["header_id", "rebuig_ids"]
        )
        self.assertNotEqual(copied["header_id"][0], header_id)
        self.assertEqual(len(copied["rebuig_ids"]), len(original_rejections))
        self.assertFalse(set(copied["rebuig_ids"]).intersection(original_rejections))
        steps.unlink(self.cursor, self.uid, [copied_id])
        self.assertEqual(self.rejection_ids(header_id), original_rejections)

    def test_header_without_rejections_can_be_copied_and_deleted(self):
        header_id = self.create_header()
        self.rejections.unlink(
            self.cursor, self.uid, self.rejection_ids(header_id)
        )

        copied_id = self.headers.copy(self.cursor, self.uid, header_id)
        self.assertEqual(self.rejection_ids(copied_id), [])
        self.headers.unlink(self.cursor, self.uid, [copied_id, header_id])

    def test_deleting_visible_header_preserves_hidden_owners_rejection(self):
        hidden_id = self.create_header()
        shared_ids = self.rejection_ids(hidden_id)
        visible_id = self.headers.copy(self.cursor, self.uid, hidden_id)
        copied_ids = self.rejection_ids(visible_id)
        self.headers.write(
            self.cursor, self.uid, [visible_id],
            {"rebuig_ids": [(6, 0, shared_ids)]},
        )
        self.rejections.unlink(self.cursor, self.uid, copied_ids)
        users = self.pool.get("res.users")
        restricted_uid = users.copy(self.cursor, self.uid, self.uid, {
            "name": "ATR rejection restricted user",
            "login": "atr_rejection_restricted",
        })
        self.assertNotEqual(restricted_uid, 1)
        model_id = self.pool.get("ir.model").search(
            self.cursor, self.uid,
            [("model", "=", "giscedata.switching.step.header")],
        )[0]
        self.addCleanup(cache.clean_caches_for_db, self.database)
        self.pool.get("ir.rule.group").create(self.cursor, self.uid, {
            "name": "Hide the original rejection header",
            "model_id": model_id,
            "global": True,
            "rules": [(0, 0, {
                "domain_force": repr([("id", "!=", hidden_id)]),
            })],
        })
        self.assertEqual(
            self.headers.search(
                self.cursor, restricted_uid, [("id", "in", [hidden_id, visible_id])]
            ),
            [visible_id],
        )

        self.headers.unlink(self.cursor, restricted_uid, [visible_id])

        self.assertEqual(self.rejection_ids(hidden_id), shared_ids)
        self.assertEqual(
            self.rejections.search(self.cursor, self.uid, [("id", "in", shared_ids)]),
            shared_ids,
        )
