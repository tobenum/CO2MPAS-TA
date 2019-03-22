# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
Functions and a model `dsp` to write CO2MPAS output data.

Sub-Modules:

.. currentmodule:: co2mpas.core.write

.. autosummary::
    :nosignatures:
    :toctree: write/

    convert
    excel
"""
import os
import logging
import os.path as osp
import schedula as sh
from .excel import write_to_excel
from .convert import convert2df
from co2mpas._version import __version__
from co2mpas.utils import check_first_arg, check_first_arg_false

try:
    from dice.co2mpas import dsp as _dice
except ImportError:
    _dice = None

log = logging.getLogger(__name__)
dsp = sh.BlueDispatcher(
    name='write', description='Write the outputs of the CO2MPAS model.'
)


@sh.add_function(dsp, outputs=['start_time'])
def default_start_time():
    """
    Returns the default run start time.

    :return:
        Run start time.
    :rtype: datetime.datetime
    """
    import datetime
    return datetime.datetime.today()


dsp.add_func(
    convert2df, inputs_kwargs=True, inputs_defaults=True, outputs=['dfs']
)


@sh.add_function(dsp, outputs=['output_template'], weight=sh.inf(1, 0))
def default_output_template():
    """
    Returns the default template output.

    :return:
        Template output.
    :rtype: str
    """
    from pkg_resources import resource_filename as res_fn
    return res_fn('co2mpas', 'templates/co2mpas_output_template.xlsx')


dsp.add_func(write_to_excel, outputs=['excel_output'])

dsp.add_function(
    function=sh.add_args(sh.bypass),
    inputs=['type_approval_mode', 'excel_output'],
    outputs=['output_file'],
    input_domain=check_first_arg_false
)


@sh.add_function(dsp, outputs=['timestamp'])
def default_timestamp(start_time):
    """
    Returns the default timestamp.

    :param start_time:
        Run start time.
    :type start_time: datetime.datetime

    :return:
        Run timestamp.
    :rtype: str
    """
    return start_time.strftime('%Y%m%d_%H%M%S')


def default_output_file_name(
        output_folder, vehicle_name, timestamp, ext='xlsx'):
    """
    Returns the output file name.

    :param output_folder:
        Output folder.
    :type output_folder: str

    :param vehicle_name:
        Vehicle name.
    :type vehicle_name: str

    :param timestamp:
        Run timestamp.
    :type timestamp: str

    :param ext:
        File extension.
    :type ext: str | None

    :return:
        Output file name.
    :rtype: str

    """
    fp = osp.join(output_folder, '%s-%s' % (timestamp, vehicle_name))
    if ext is not None:
        fp = '%s.%s' % (fp, ext)
    return fp


dsp.add_function(
    function=sh.add_args(default_output_file_name),
    inputs=['type_approval_mode', 'output_folder', 'vehicle_name', 'timestamp'],
    outputs=['output_file_name'],
    input_domain=check_first_arg_false
)

if _dice is not None:
    dsp.add_data('co2mpas_version', __version__)
    _out, _inp = ['output_file_name', 'output_file'], [
        'base', 'dice', 'excel_output', 'input_file', 'output_folder', 'report',
        'encryption_keys', 'start_time', 'meta', 'sign_key', 'co2mpas_version',
        'timestamp'
    ]

    # noinspection PyProtectedMember
    dsp.add_function(
        function=sh.Blueprint(
            sh.SubDispatchFunction(_dice, inputs=_inp, outputs=_out)
        )._set_cls(sh.add_args),
        function_id='write_ta_output',
        description='Write ta output file.',
        inputs=['type_approval_mode'] + _inp,
        outputs=_out,
        input_domain=check_first_arg
    )


@sh.add_function(dsp)
def save_output_file(output_file, output_file_name):
    """
    Save output file.

    :param output_file_name:
        Output file name.
    :type output_file_name: str

    :param output_file:
        Output file.
    :type output_file: io.BytesIO
    """
    output_file.seek(0)
    os.makedirs(osp.dirname(output_file_name), exist_ok=True)
    with open(output_file_name, 'wb') as f:
        f.write(output_file.read())
    log.info('CO2MPAS output written into (%s).', output_file_name)