# -*- coding: utf-8 -*-
from __future__ import absolute_import

from functools import wraps


def is_dry_run(context=None):
    return bool(context and context.get("is_dry_run", False))


def skip_job_in_dry_run(function):
    """Avoid creating an async job when called in dry-run mode."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        context = kwargs.get("context")
        if context is None and args and isinstance(args[-1], dict):
            context = args[-1]
        if is_dry_run(context):
            return False
        return function(*args, **kwargs)
    return wrapped
