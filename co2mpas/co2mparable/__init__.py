# -*- coding: utf-8 -*-
#
# Copyright 2015-2017 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
Simple co2mparable-hasher definitions to cnditionally enable it

without iporting full dependencies (too slow);  model-items can set their ``co2hash``
attribute by calling :func:`tag_checksum()` here, even when hasher disabled.
"""
import os
from typing import Optional


#: Env-var that when true, co2mparable is generated and optionally compared
#: against an existing co2mparable given in --co2mparable=<old-yaml>
CO2MPARE_ENABLED = 'CO2MPARE_ENABLED'
#: Env-var that when true, generate compressed co2mparable (as '.xz' with LZMA).
CO2MPARE_ZIP = 'CO2MPARE_ZIP'
#: Env-var that when true, co2mparable stored as yaml else as text-lines..
CO2MPARE_YAML = 'CO2MPARE_YAML'
#: Env-var specifying an existing yaml(.xz) co2mparable to compare while executing.
CO2MPARE_WITH_FPATH = 'CO2MPARE_WITH_FPATH'
#: Env-var when true, and comparing, ck runs twice
#: to give a 2nd opportunity to inspect the problem to debuggers.
CO2MPARE_DEBUG = 'CO2MPARE_DEBUG'

def bool_env(env_var, default):
    """
    A `true` env-var is any value (incl. empty) except: 0, false, no, off

    .. Attention::
        On *Windows* it's impossible to assign the empty-string to a variable!
    """
    if env_var not in os.environ:
        return default
    v = os.environ[env_var]
    return v and v.lower() not in ('0 false no off') or v == ''


#: Global stored for :func:`tag_checksum()` below, and to detect double-monkeypatches.
_hasher = None


def enable_hasher(*,
                  enabled: Optional[bool] = None,
                  compare_with_fpath: Optional[str] = None):
    """
    :param enabled:
        a 3-state flag, when `None`, env[CO2MPARE_ENABLED] decides
    :param compare_with_fpath:
        if it evaluates to false, env[CO2MPARE_WITH_FPATH] decides

    """
    global _hasher

    if enabled or enabled is None and bool_env(CO2MPARE_ENABLED, False):
        ## Slow(!) recursive import below, because it
        #  it references elements too deep into the model.
        if _hasher:
            raise AssertionError("Already intercepted *schedula*!")

        from . import co2hasher
        _hasher = co2hasher.Co2Hasher(
            compare_with_fpath=(compare_with_fpath
                                 if compare_with_fpath != '<DISABLED>' else
                                 None),
            dump_yaml=bool_env(CO2MPARE_YAML, False),
            zip_output=bool_env(CO2MPARE_ZIP, True)
        )


def tag_checksum(tagged, item1, *items) -> Optional[int]:
    "Call this to tag an object with a has hash from the active hasher, f any."
    if _hasher:
        tagged.co2hash = _hasher.checksum(item1, *items)