# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from flask import g

from pyprof_timer import Timer


class FlaskTimer(Timer):
    """The timer implementation in Flask."""

    @classmethod
    def get_context(cls):
        """Return the request context."""
        return g
