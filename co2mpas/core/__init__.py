# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
It contains functions and a model `dsp` to processes a vehicle from the file
path to the write of its outputs.
"""

import logging
import schedula as sh
import os.path as osp
from co2mpas.utils import check_first_arg, ret_v
from .load import dsp as _load
from .model import dsp as _model
from .report import dsp as _report
from .write import dsp as _write

log = logging.getLogger(__name__)

dsp = sh.BlueDispatcher(
    name='core',
    description='Processes a vehicle from the file path to the write of its'
                ' outputs.'
)
_cmd_flags = [
    'only_summary', 'soft_validation', 'engineering_mode', 'enable_selector',
    'type_approval_mode', 'encryption_keys', 'sign_key', 'plot_workflow',
    'output_template', 'output_folder'
]


@sh.add_function(
    dsp, inputs_kwargs=True, inputs_defaults=True, outputs=_cmd_flags
)
def parse_cmd_flags(cmd_flags=None):
    """
    Parses the command line options.

    :param cmd_flags:
        Command line options.
    :type cmd_flags: dict

    :return:
        Default parameters of process model.
    :rtype: tuple
    """
    flags = sh.combine_dicts(cmd_flags or {}, base={
        'only_summary': False,
        'soft_validation': False,
        'engineering_mode': False,
        'enable_selector': False,
        'type_approval_mode': False,
        'plot_workflow': False,
        'encryption_keys': None,
        'sign_key': None,
        'output_template': sh.NONE,
        'output_folder': './outputs'
    })
    return sh.selector(_cmd_flags, flags, output_type='list')


dsp.add_dispatcher(
    dsp=_load,
    inputs=(
        'input_file_name', 'soft_validation', 'engineering_mode', 'cmd_flags',
        'type_approval_mode', 'input_file', 'raw_data', 'encryption_keys',
        'sign_key'
    ),
    outputs=('plan', 'flag', 'dice', 'meta', 'base', 'input_file'),
)

dsp.add_function(
    function=sh.SubDispatch(_model),
    inputs=['base'],
    outputs=['solution']
)


@sh.add_function(dsp, outputs=['output_data'])
def parse_solution(solution):
    """
    Parse the CO2MPAS model solution.

    :param solution:
        CO2MPAS model solution.
    :type solution: schedula.Solution

    :return:
        CO2MPAS outputs.
    :rtype: dict[dict]
    """

    res = {}
    for k, v in solution.items():
        sh.get_nested_dicts(res, *k.split('.'), default=ret_v(v))

    for k, v in list(sh.stack_nested_keys(res, depth=3)):
        n, k = k[:-1], k[-1]
        if n == ('output', 'calibration') and k in ('wltp_l', 'wltp_h'):
            v = sh.selector(('co2_emission_value',), v, allow_miss=True)
            if v:
                d = sh.get_nested_dicts(res, 'target', 'prediction')
                d[k] = sh.combine_dicts(v, d.get(k, {}))

    res['pipe'] = solution.pipe

    return res


dsp.add_dispatcher(
    dsp=_report,
    inputs=['output_data'],
    outputs=['report', 'summary'],
)


def check_only_summary(kw):
    """
    Check if `only_summary` is true.

    :param kw:
        `write` dispatcher inputs.
    :type kw: dict

    :return:
        Is `only_summary` true?
    :rtype: bool
    """
    return not kw.get('only_summary', True)


dsp.add_dispatcher(
    dsp=_write,
    inputs=[
        'input_file_name', 'input_file', 'vehicle_name', 'output_folder',
        'output_file_name', 'report', 'flag', 'type_approval_mode', 'timestamp',
        {'only_summary': sh.SINK}
    ],
    outputs=['output_file', 'vehicle_name', 'start_time', 'timestamp',
             'output_file_name', sh.SINK],
    input_domain=check_only_summary
)

SITES = set()


def wait_sites(sites=None):
    """
    Pause for sites shutdown.

    :param sites:
        Running sites.
    :type sites: set
    """
    import time
    sites = SITES if sites is None else sites
    try:
        while sites:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
    while sites:
        sites.pop().shutdown()


# noinspection PyUnusedLocal
def plot_model_workflow(output_file_name=None, vehicle_name='', **kw):
    """
    Defines the kwargs to plot the dsp workflow.

    :param output_file_name:
        File name where to plot the workflow.
    :type output_file_name: str

    :param vehicle_name:
        Vehicle name.
    :type vehicle_name: str

    :param kw:
        Additional kwargs.
    :type kw: dict

    :return:
        Kwargs to plot the dsp workflow.
    :rtype: dict
    """
    try:
        ofname = None
        if output_file_name:
            ofname = osp.splitext(output_file_name)[0]
        log.info("Plotting workflow of %s... into '%s'", vehicle_name, ofname)
        return {'directory': ofname, 'sites': SITES, 'index': True}
    except RuntimeError as ex:
        log.warning(ex, exc_info=1)
    return sh.NONE


dsp.add_function(
    function=sh.add_args(plot_model_workflow),
    inputs=['plot_workflow', 'output_file_name', 'vehicle_name'],
    outputs=[sh.PLOT],
    weight=sh.inf(100, 0),
    input_domain=check_first_arg
)
