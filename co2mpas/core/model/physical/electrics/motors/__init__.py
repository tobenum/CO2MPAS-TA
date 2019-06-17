# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
Functions and a model `dsp` to model the electric motors of the vehicle.

Sub-Modules:

.. currentmodule:: co2mpas.core.model.physical.electrics.motors

.. autosummary::
    :nosignatures:
    :toctree: motors/

    p0
    p1
    p2
    p3
    p4
    starter
"""

import schedula as sh
from .p0 import dsp as _p0
from .p1 import dsp as _p1
from .p2 import dsp as _p2
from .p3 import dsp as _p3
from .p4 import dsp as _p4

dsp = sh.BlueDispatcher(name='Motors', description='Models the vehicle motors.')

dsp.add_dispatcher(
    dsp_id='motor_p0',
    dsp=_p0,
    inputs=(
        'engine_speeds_out', 'motor_p0_speed_ratio', 'motor_p0_speeds',
        'motor_p0_powers', 'motor_p0_torques', 'motor_p0_efficiency',
        'motor_p0_electric_power_loss_function', 'motor_p0_loss_param_a',
        'motor_p0_loss_param_b', 'motor_p0_electric_powers',
    ),
    outputs=(
        'motor_p0_speed_ratio', 'motor_p0_speeds', 'motor_p0_powers',
        'motor_p0_torques', 'motor_p0_efficiency', 'motor_p0_electric_powers',
        'motor_p0_efficiency_ratios'
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p1',
    dsp=_p1,
    inputs=(
        'engine_speeds_out', 'motor_p1_speed_ratio', 'motor_p1_speeds',
        'motor_p1_powers', 'motor_p1_torques', 'motor_p1_efficiency',
        'motor_p1_electric_power_loss_function', 'motor_p1_loss_param_a',
        'motor_p1_loss_param_b', 'motor_p1_electric_powers'
    ),
    outputs=(
        'motor_p1_speed_ratio', 'motor_p1_speeds', 'motor_p1_powers',
        'motor_p1_torques', 'motor_p1_efficiency', 'motor_p1_electric_powers',
        'motor_p1_efficiency_ratios'
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p2',
    dsp=_p2,
    inputs=(
        'gear_box_speeds_in', 'motor_p2_speed_ratio', 'motor_p2_speeds',
        'motor_p2_powers', 'motor_p2_torques', 'motor_p2_efficiency',
        'motor_p2_electric_power_loss_function', 'motor_p2_loss_param_a',
        'motor_p2_loss_param_b', 'motor_p2_electric_powers'
    ),
    outputs=(
        'motor_p2_speed_ratio', 'motor_p2_speeds', 'motor_p2_powers',
        'motor_p2_torques', 'motor_p2_efficiency', 'motor_p2_electric_powers',
        'motor_p2_efficiency_ratios'
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p3',
    dsp=_p3,
    inputs=(
        'final_drive_speeds_in', 'motor_p3_speed_ratio', 'motor_p3_speeds',
        'motor_p3_powers', 'motor_p3_torques', 'motor_p3_efficiency',
        'motor_p3_electric_power_loss_function', 'motor_p3_loss_param_a',
        'motor_p3_loss_param_b', 'motor_p3_electric_powers',
    ),
    outputs=(
        'motor_p3_speed_ratio', 'motor_p3_speeds', 'motor_p3_powers',
        'motor_p3_torques', 'motor_p3_efficiency', 'motor_p3_electric_powers',
        'motor_p3_efficiency_ratios'
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p4',
    dsp=_p4,
    inputs=(
        'wheel_speeds', 'motor_p4_speed_ratio', 'motor_p4_speeds',
        'motor_p4_powers', 'motor_p4_torques', 'motor_p4_efficiency',
        'motor_p4_electric_power_loss_function', 'motor_p4_loss_param_a',
        'motor_p4_loss_param_b', 'motor_p4_electric_powers'
    ),
    outputs=(
        'motor_p4_speed_ratio', 'motor_p4_speeds', 'motor_p4_powers',
        'motor_p4_torques', 'motor_p4_efficiency', 'motor_p4_electric_powers',
        'motor_p4_efficiency_ratios'
    ),
    include_defaults=True
)


@sh.add_function(dsp, outputs=['motors_electric_powers'])
def calculate_motors_electric_powers(
        motor_p0_electric_powers, motor_p1_electric_powers,
        motor_p2_electric_powers, motor_p3_electric_powers,
        motor_p4_electric_powers):
    """
    Calculate motors electric power [kW].

    :param motor_p0_electric_powers:
        Electric power of motor P0 [kW].
    :type motor_p0_electric_powers: numpy.array | float

    :param motor_p1_electric_powers:
        Electric power of motor P1 [kW].
    :type motor_p1_electric_powers: numpy.array | float

    :param motor_p2_electric_powers:
        Electric power of motor P2 [kW].
    :type motor_p2_electric_powers: numpy.array | float

    :param motor_p3_electric_powers:
        Electric power of motor P3 [kW].
    :type motor_p3_electric_powers: numpy.array | float

    :param motor_p4_electric_powers:
        Electric power of motor P4 [kW].
    :type motor_p4_electric_powers: numpy.array | float

    :return:
        Motors electric power [kW].
    :rtype: numpy.array | float
    """
    p = motor_p0_electric_powers + motor_p1_electric_powers
    p += motor_p2_electric_powers
    p += motor_p3_electric_powers
    p += motor_p4_electric_powers
    return p