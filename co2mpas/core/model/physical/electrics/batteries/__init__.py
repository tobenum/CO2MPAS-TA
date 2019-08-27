# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
Functions and a model `dsp` to model the vehicle batteries.

Sub-Modules:

.. currentmodule:: co2mpas.core.model.physical.electrics.batteries

.. autosummary::
    :nosignatures:
    :toctree: batteries/

    dcdc
    drive
    service
"""

import schedula as sh
from .service import dsp as _service
from .drive import dsp as _drive
from .dcdc import dsp as _dcdc

dsp = sh.BlueDispatcher(
    name='Batteries', description='Models the vehicle batteries.'
)

dsp.add_dispatcher(
    dsp_id='service_battery',
    dsp=_service,
    inputs=(
        'initial_service_battery_state_of_charge', 'alternator_electric_powers',
        'service_battery_start_window_width', 'service_battery_nominal_voltage',
        'service_battery_state_of_charge_balance', 'on_engine', 'accelerations',
        'cycle_type', 'service_battery_electric_powers', 'service_battery_load',
        'service_battery_electric_powers_supply_threshold', 'engine_powers_out',
        'service_battery_capacity', 'starter_electric_powers', 'engine_starts',
        'service_battery_initialization_time', 'service_battery_status_model',
        'service_battery_electric_powers_supply', 'service_battery_currents',
        'dcdc_converter_electric_powers', 'service_battery_state_of_charges',
        'service_battery_state_of_charge_balance_window', 'motive_powers',
        'service_battery_loads', 'times', 'has_energy_recuperation',
        'dcdc_current_model', 'alternator_current_model',
    ),
    outputs=(
        'initial_service_battery_state_of_charge', 'service_battery_currents',
        'service_battery_electric_powers', 'service_battery_state_of_charges',
        'service_battery_initialization_time', 'service_battery_status_model',
        'service_battery_state_of_charge_balance', 'service_battery_capacity',
        'service_battery_delta_state_of_charge', 'service_battery_loads',
        'service_battery_charging_statuses', 'service_battery_model',
        'service_battery_electric_powers_supply_threshold',
        'service_battery_state_of_charge_balance_window', 'service_battery_load'
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='drive_battery',
    dsp=_drive,
    inputs=(
        'dcdc_converter_electric_powers_demand', 'drive_battery_n_series_cells',
        'motor_p4_electric_powers', 'drive_battery_loads', 'drive_battery_load',
        'drive_battery_currents', 'drive_battery_capacity', 'drive_battery_r0',
        'initial_drive_battery_state_of_charge', 'drive_battery_ocv', 'times',
        'drive_battery_n_parallel_cells', 'electrical_hybridization_degree',
        'drive_battery_electric_powers', 'drive_battery_state_of_charges',
        'dcdc_converter_efficiency', 'motor_p2_electric_powers',
        'motor_p3_front_electric_powers', 'motor_p3_rear_electric_powers',
        'motor_p0_electric_powers', 'motor_p1_electric_powers',
        'drive_battery_voltages', 'service_battery_model',
    ),
    outputs=(
        'drive_battery_currents', 'drive_battery_loads', 'drive_battery_load',
        'drive_battery_n_series_cells', 'drive_battery_ocv', 'drive_battery_r0',
        'initial_drive_battery_state_of_charge', 'drive_battery_capacity',
        'drive_battery_delta_state_of_charge', 'drive_battery_n_parallel_cells',
        'drive_battery_electric_powers', 'drive_battery_state_of_charges',
        'drive_battery_model', 'drive_battery_voltages',
        'motors_electric_powers',
    ),
    include_defaults=True
)

dsp.add_dispatcher(
    dsp_id='dcdc_converter',
    dsp=_dcdc,
    inputs=(
        'service_battery_state_of_charges', 'service_battery_charging_statuses',
        'dcdc_converter_electric_powers', 'service_battery_initialization_time',
        'service_battery_nominal_voltage', 'dcdc_converter_efficiency', 'times',
        'dcdc_converter_currents', 'dcdc_charging_currents', 'on_engine',
        'dcdc_current_model', 'is_hybrid',
    ),
    outputs=(
        'dcdc_converter_electric_powers_demand', 'dcdc_current_model',
        'dcdc_converter_electric_powers', 'dcdc_converter_currents'
    ),
    include_defaults=True
)
