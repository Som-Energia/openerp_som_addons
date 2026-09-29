# -*- coding: utf-8 -*-
from __future__ import absolute_import

import unittest

from base_extended_som.utils import is_dry_run, skip_job_in_dry_run


class TestDryRunUtils(unittest.TestCase):
    def test_is_dry_run(self):
        self.assertFalse(is_dry_run())
        self.assertFalse(is_dry_run({}))
        self.assertFalse(is_dry_run({"is_dry_run": False}))
        self.assertTrue(is_dry_run({"is_dry_run": True}))

    def test_skip_job_executes_without_context(self):
        calls = []

        @skip_job_in_dry_run
        def function(*args, **kwargs):
            calls.append((args, kwargs))
            return "executed"

        self.assertEqual(function(1), "executed")
        self.assertEqual(calls, [((1,), {})])

    def test_skip_job_executes_when_dry_run_is_false(self):
        calls = []

        @skip_job_in_dry_run
        def function(*args, **kwargs):
            calls.append((args, kwargs))
            return "executed"

        context = {"is_dry_run": False}
        self.assertEqual(function(context=context), "executed")
        self.assertEqual(calls, [((), {"context": context})])

    def test_skip_job_returns_false_with_keyword_context(self):
        calls = []

        @skip_job_in_dry_run
        def function(*args, **kwargs):
            calls.append((args, kwargs))

        self.assertFalse(function(context={"is_dry_run": True}))
        self.assertEqual(calls, [])

    def test_skip_job_returns_false_with_positional_context(self):
        calls = []

        @skip_job_in_dry_run
        def function(*args, **kwargs):
            calls.append((args, kwargs))

        self.assertFalse(function(1, {"is_dry_run": True}))
        self.assertEqual(calls, [])
