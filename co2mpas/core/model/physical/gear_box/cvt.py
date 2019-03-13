# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
Functions and a model `dsp` to model the CVT.
"""
import numpy as np
import schedula as sh
from ..defaults import dfl

dsp = sh.BlueDispatcher(name='CVT model', description='Models the gear box.')


@sh.add_function(dsp, outputs=['correct_gear'])
def default_correct_gear():
    """
    Returns a fake function to correct the gear.

    :return:
        A function to correct the predicted gear.
    :rtype: callable
    """
    from .at_gear import CorrectGear
    return CorrectGear()


# noinspection PyMissingOrEmptyDocstring,PyPep8Naming,PyUnusedLocal
class CVT:
    def __init__(self):
        import xgboost as xgb
        self.base_model = xgb.XGBRegressor
        self.model = None

    def fit(self, on_engine, engine_speeds_out, velocities, accelerations,
            gear_box_powers_out):
        b = on_engine
        X = np.column_stack((velocities, accelerations, gear_box_powers_out))[b]
        y = engine_speeds_out[b]

        # noinspection PyArgumentEqualDefault
        self.model = self.base_model(
            random_state=0,
            max_depth=3,
            n_estimators=int(min(300.0, 0.25 * (len(y) - 1)))
        )
        self.model.fit(X, y)
        return self

    # noinspection PyUnusedLocal
    @staticmethod
    def yield_gear(times, *args, **kwargs):
        for _ in range(times.shape[0]):
            yield 1

    def predict(self, velocities, accelerations, gear_box_powers_out):
        X = np.column_stack((velocities, accelerations, gear_box_powers_out))
        return self.model.predict(X)

    def yield_speed(self, stop_velocity, gears, velocities, accelerations,
                    gear_box_powers_out):
        func = self.model.predict
        x = np.empty((1, 3), float)
        for v in zip(velocities, accelerations, gear_box_powers_out):
            x[:, :] = v
            yield func(x)


@sh.add_function(dsp, outputs=['CVT'])
def calibrate_cvt(
        on_engine, engine_speeds_out, velocities, accelerations,
        gear_box_powers_out):
    """
    Calibrates a model for continuously variable transmission (CVT).

    :param on_engine:
        If the engine is on [-].
    :type on_engine: numpy.array

    :param engine_speeds_out:
        Engine speed [RPM].
    :type engine_speeds_out: numpy.array

    :param velocities:
        Vehicle velocity [km/h].
    :type velocities: numpy.array

    :param accelerations:
        Vehicle acceleration [m/s2].
    :type accelerations: numpy.array

    :param gear_box_powers_out:
        Gear box power vector [kW].
    :type gear_box_powers_out: numpy.array

    :return:
        Continuously variable transmission model.
    :rtype: callable
    """
    model = CVT().fit(
        on_engine, engine_speeds_out, velocities, accelerations,
        gear_box_powers_out
    )

    return model


dsp.add_data('max_gear', 1)


@sh.add_function(dsp, outputs=['gears'])
def predict_gears(velocities):
    """
    Predicts gear vector [-].

    :param velocities:
        Vehicle velocity [km/h].
    :type velocities: numpy.array

    :return:
        Gear vector [-].
    :rtype: numpy.array
    """

    return np.ones_like(velocities, dtype=int)


@sh.add_function(
    dsp,
    inputs=['CVT', 'velocities', 'accelerations', 'gear_box_powers_out'],
    outputs=['gear_box_speeds_in'],
    out_weight={'gear_box_speeds_in': 10}
)
def predict_gear_box_speeds_in(
        cvt, velocities, accelerations, gear_box_powers_out):
    """
    Predicts gear box speed vector, gear vector, and maximum gear [RPM, -, -].

    :param cvt:
        Continuously variable transmission model.
    :type cvt: callable

    :param velocities:
        Vehicle velocity [km/h].
    :type velocities: numpy.array

    :param accelerations:
        Vehicle acceleration [m/s2].
    :type accelerations: numpy.array

    :param gear_box_powers_out:
        Gear box power vector [kW].
    :type gear_box_powers_out: numpy.array

    :return:
        Gear box speed vector, gear vector, and maximum gear [RPM, -, -].
    :rtype: numpy.array, numpy.array, int
    """

    return cvt.predict(velocities, accelerations, gear_box_powers_out)


dsp.add_data('stop_velocity', dfl.values.stop_velocity)


@sh.add_function(dsp, outputs=['max_speed_velocity_ratio'])
def identify_max_speed_velocity_ratio(
        velocities, engine_speeds_out, idle_engine_speed, stop_velocity):
    """
    Identifies the maximum speed velocity ratio of the gear box [h*RPM/km].

    :param velocities:
        Vehicle velocity [km/h].
    :type velocities: numpy.array

    :param engine_speeds_out:
        Engine speed [RPM].
    :type engine_speeds_out: numpy.array

    :param idle_engine_speed:
        Engine speed idle median and std [RPM].
    :type idle_engine_speed: (float, float)

    :param stop_velocity:
        Maximum velocity to consider the vehicle stopped [km/h].
    :type stop_velocity: float

    :return:
        Maximum speed velocity ratio of the gear box [h*RPM/km].
    :rtype: float
    """

    b = (velocities > stop_velocity)
    b &= (engine_speeds_out > idle_engine_speed[0])
    return max(engine_speeds_out[b] / velocities[b])
