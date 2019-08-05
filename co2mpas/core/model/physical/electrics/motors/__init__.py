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

    alternator
    p0
    p1
    p2
    p3
    p4
    starter
"""

import schedula as sh
from .alternator import dsp as _alternator
from .p0 import dsp as _p0
from .p1 import dsp as _p1
from .p2 import dsp as _p2
from .p3 import dsp as _p3
from .p4 import dsp as _p4
from .starter import dsp as _starter

dsp = sh.BlueDispatcher(name='Motors', description='Models the vehicle motors.')

dsp.add_dispatcher(
    dsp_id='alternator',
    dsp=_alternator,
    inputs=(
        'alternator_currents', 'alternator_nominal_voltage', 'motive_powers',
        'alternator_electric_powers', 'alternator_efficiency', 'accelerations',
        'service_battery_state_of_charges', 'service_battery_charging_statuses',
        'alternator_current_model', 'on_engine', 'alternator_charging_currents',
        'service_battery_initialization_time', 'times',
    ),
    outputs=(
        'alternator_current_model', 'alternator_currents', 'alternator_powers',
        'alternator_electric_powers'
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p0',
    dsp=_p0,
    inputs=(
        'motor_p0_electric_powers', 'motor_p0_maximum_power', 'motor_p0_powers',
        'motor_p0_maximum_torque', 'motor_p0_speed_ratio', 'motor_p0_torques',
        'motor_p0_efficiency', 'motor_p0_rated_speed', 'motor_p0_speeds',
        'engine_speeds_out',
    ),
    outputs=(
        'motor_p0_electric_powers', 'motor_p0_maximum_power', 'motor_p0_powers',
        'motor_p0_maximum_torque', 'motor_p0_speed_ratio', 'motor_p0_torques',
        'motor_p0_maximum_powers', 'motor_p0_rated_speed', 'motor_p0_speeds',
        'engine_speeds_out', 'motor_p0_maximum_power_function',
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p1',
    dsp=_p1,
    inputs=(
        'motor_p1_electric_powers', 'motor_p1_maximum_power', 'motor_p1_powers',
        'motor_p1_maximum_torque', 'motor_p1_speed_ratio', 'motor_p1_torques',
        'motor_p1_efficiency', 'motor_p1_rated_speed', 'motor_p1_speeds',
        'engine_speeds_out',
    ),
    outputs=(
        'motor_p1_electric_powers', 'motor_p1_maximum_power', 'motor_p1_powers',
        'motor_p1_maximum_torque', 'motor_p1_speed_ratio', 'motor_p1_torques',
        'motor_p1_maximum_powers', 'motor_p1_rated_speed', 'motor_p1_speeds',
        'engine_speeds_out', 'motor_p1_maximum_power_function',
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p2',
    dsp=_p2,
    inputs=(
        'motor_p2_electric_powers', 'motor_p2_maximum_power', 'motor_p2_powers',
        'motor_p2_maximum_torque', 'motor_p2_speed_ratio', 'motor_p2_torques',
        'motor_p2_efficiency', 'motor_p2_rated_speed', 'motor_p2_speeds',
        'gear_box_speeds_in',
    ),
    outputs=(
        'motor_p2_electric_powers', 'motor_p2_maximum_power', 'motor_p2_powers',
        'motor_p2_maximum_torque', 'motor_p2_speed_ratio', 'motor_p2_torques',
        'motor_p2_maximum_powers', 'motor_p2_rated_speed', 'motor_p2_speeds',
        'gear_box_speeds_in',
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p3',
    dsp=_p3,
    inputs=(
        'motor_p3_electric_powers', 'motor_p3_maximum_power', 'motor_p3_powers',
        'motor_p3_maximum_torque', 'motor_p3_speed_ratio', 'motor_p3_torques',
        'motor_p3_efficiency', 'motor_p3_rated_speed', 'motor_p3_speeds',
        'final_drive_speeds_in',
    ),
    outputs=(
        'motor_p3_electric_powers', 'motor_p3_maximum_power', 'motor_p3_powers',
        'motor_p3_maximum_torque', 'motor_p3_speed_ratio', 'motor_p3_torques',
        'motor_p3_maximum_powers', 'motor_p3_rated_speed', 'motor_p3_speeds',
        'final_drive_speeds_in',
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='motor_p4',
    dsp=_p4,
    inputs=(
        'motor_p4_electric_powers', 'motor_p4_maximum_power', 'motor_p4_powers',
        'motor_p4_maximum_torque', 'motor_p4_speed_ratio', 'motor_p4_torques',
        'motor_p4_efficiency', 'motor_p4_rated_speed', 'motor_p4_speeds',
        'wheel_speeds',
    ),
    outputs=(
        'motor_p4_electric_powers', 'motor_p4_maximum_power', 'motor_p4_powers',
        'motor_p4_maximum_torque', 'motor_p4_speed_ratio', 'motor_p4_torques',
        'motor_p4_maximum_powers', 'motor_p4_rated_speed', 'motor_p4_speeds',
        'wheel_speeds',
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='starter',
    dsp=_starter,
    inputs=(
        'delta_time_engine_starter', 'times', 'on_engine', 'starter_efficiency',
        'engine_moment_inertia', 'engine_speeds_out', 'starter_nominal_voltage',
    ),
    outputs=(
        'starter_electric_powers', 'starter_powers', 'starter_currents',
        'starter_model', 'delta_time_engine_starter'
    ),
    include_defaults=True
)
