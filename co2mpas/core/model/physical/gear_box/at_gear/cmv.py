# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
Functions and a model `dsp` to model the CMV Approach.
"""
import itertools
import collections
import numpy as np
import schedula as sh
from ...defaults import dfl
from .core import prediction_gears_gsm, define_gear_filter

dsp = sh.BlueDispatcher(name='Corrected Matrix Velocity Approach')

dsp.add_data('stop_velocity', dfl.values.stop_velocity)


def _correct_gsv(gsv, stop_velocity):
    """
    Corrects gear shifting velocity matrix from unreliable limits.

    :param gsv:
        Gear shifting velocity matrix.
    :type gsv: dict

    :param stop_velocity:
        Maximum velocity to consider the vehicle stopped [km/h].
    :type stop_velocity: float

    :return:
        Gear shifting velocity matrix corrected from unreliable limits.
    :rtype: dict
    """

    gsv[0] = [0, (stop_velocity, (dfl.INF, 0))]

    # noinspection PyMissingOrEmptyDocstring
    def func(x):
        return not x and float('inf') or 1 / x

    for v0, v1 in sh.pairwise(gsv.values()):
        up0, s0, down1, s1 = v0[1][0], v0[1][1][1], v1[0][0], v1[0][1][1]

        if down1 + s1 <= v0[0]:
            v0[1], v1[0] = up0 + s0, up0 - s0
        elif up0 >= down1:
            v0[1], v1[0] = up0 + s0, down1 - s1
            continue
        elif (v0[1][1][0], func(s0)) >= (v1[0][1][0], func(s1)):
            v0[1], v1[0] = up0 + s0, up0 - s0
        else:
            v0[1], v1[0] = down1 + s1, down1 - s1

        v0[1] += stop_velocity

    gsv[max(gsv)][1] = dfl.INF

    return gsv


def _identify_gear_shifting_velocity_limits(gears, velocities, stop_velocity):
    """
    Identifies gear shifting velocity matrix.

    :param gears:
        Gear vector [-].
    :type gears: numpy.array

    :param velocities:
        Vehicle velocity [km/h].
    :type velocities: numpy.array

    :param stop_velocity:
        Maximum velocity to consider the vehicle stopped [km/h].
    :type stop_velocity: float

    :return:
        Gear shifting velocity matrix.
    :rtype: dict
    """

    limits = {}

    for v, (g0, g1) in zip(velocities, sh.pairwise(gears)):
        if v >= stop_velocity and g0 != g1:
            limits[g0] = limits.get(g0, [[], []])
            limits[g0][int(g0 < g1)].append(v)

    def _rjt_out(x, default):
        if x:
            x = np.asarray(x)

            # noinspection PyTypeChecker
            m, (n, s) = np.median(x), (len(x), np.std(x))

            y = s and 2 > (abs(x - m) / s)

            if s and y.any():
                y = x[y]

                # noinspection PyTypeChecker
                m, (n, s) = np.median(y), (len(y), np.std(y))

            return m, (n, s)
        else:
            return default

    max_gear = max(limits)
    gsv = collections.OrderedDict()
    for k in range(max_gear + 1):
        v0, v1 = limits.get(k, [[], []])
        gsv[k] = [_rjt_out(v0, (-1, (0, 0))),
                  _rjt_out(v1, (dfl.INF, (0, 0)))]

    return _correct_gsv(gsv, stop_velocity)


# noinspection PyPep8Naming
def _convert_limits(it, X):
    from scipy.interpolate import InterpolatedUnivariateSpline as Spline
    it = sorted(it)
    x, l, u = zip(*it[1:])

    _inf = u[-1]
    x = np.asarray(x)
    l, u = np.asarray(l) / x, np.asarray(u) / x
    L = Spline(x, l, k=1)(X) * X
    U = np.append(Spline(x[:-1], u[:-1], k=1)(X[:-1]) * X[:-1], [_inf])
    L[0], U[0] = it[0][1:]

    return L, U


def _grouper(iterable, n):
    """
    Collect data into fixed-length chunks or blocks.

    :param iterable:
        Iterable object.
    :param iterable: iter

    :param n:
        Length chunks or blocks.
    :type n: int
    """
    args = [iter(iterable)] * n
    return zip(*args)


# noinspection PyMissingOrEmptyDocstring,PyUnusedLocal
class CMV(collections.OrderedDict):
    def __init__(self, *args, velocity_speed_ratios=None):
        super(CMV, self).__init__(*args)
        if args and isinstance(args[0], CMV):
            if velocity_speed_ratios:
                self.convert(velocity_speed_ratios)
            else:
                velocity_speed_ratios = args[0].velocity_speed_ratios

        self.velocity_speed_ratios = velocity_speed_ratios or {}

    def __repr__(self):
        from pprint import pformat
        name = self.__class__.__name__
        items = [(k, v) for k, v in self.items()]
        vsr = pformat(self.velocity_speed_ratios)
        s = '{}({}, velocity_speed_ratios={})'.format(name, items, vsr)
        return s.replace('inf', "float('inf')")

    def fit(self, correct_gear, gears, engine_speeds_out, times, velocities,
            accelerations, motive_powers, velocity_speed_ratios, stop_velocity):
        from ..mechanical import calculate_gear_box_speeds_in
        self.clear()
        self.velocity_speed_ratios = velocity_speed_ratios
        self.update(_identify_gear_shifting_velocity_limits(
            gears, velocities, stop_velocity
        ))
        if dfl.functions.CMV.ENABLE_OPT_LOOP:
            from co2mpas.utils import mae
            gear_id, velocity_limits = zip(*sorted(self.items())[1:])
            max_gear, _inf = gear_id[-1], float('inf')
            update, predict = self.update, self.predict

            def _update_gvs(vel_limits):
                self[0] = (0, vel_limits[0])
                self[max_gear] = (vel_limits[-1], _inf)
                update(dict(zip(gear_id, _grouper(vel_limits[1:-1], 2))))

            def _error_fun(vel_limits):
                _update_gvs(vel_limits)

                g_pre = predict(
                    times, velocities, accelerations, motive_powers,
                    correct_gear=correct_gear
                )

                speed_pred = calculate_gear_box_speeds_in(
                    g_pre, velocities, velocity_speed_ratios, stop_velocity
                )
                return np.float32(mae(speed_pred, engine_speeds_out))

            x0 = [self[0][1]].__add__(
                list(itertools.chain(*velocity_limits))[:-1]
            )
            from scipy.optimize import fmin
            _update_gvs(fmin(_error_fun, x0, disp=False))

        return self

    def correct_constant_velocity(
            self, up_cns_vel=(), up_window=0.0, up_delta=0.0, dn_cns_vel=(),
            dn_window=0.0, dn_delta=0.0):
        """
        Corrects the gear shifting matrix velocity for constant velocities.

        :param up_cns_vel:
            Constant velocities to correct the upper limits [km/h].
        :type up_cns_vel: tuple[float]

        :param up_window:
            Window to identify if the shifting matrix has limits close to
            `up_cns_vel` [km/h].
        :type up_window: float

        :param up_delta:
            Delta to add to the limit if this is close to `up_cns_vel` [km/h].
        :type up_delta: float

        :param dn_cns_vel:
            Constant velocities to correct the bottom limits [km/h].
        :type dn_cns_vel: tuple[float]

        :param dn_window:
            Window to identify if the shifting matrix has limits close to
            `dn_cns_vel` [km/h].
        :type dn_window: float

        :param dn_delta:
            Delta to add to the limit if this is close to `dn_cns_vel` [km/h].
        :type dn_delta: float

        :return:
            A gear shifting velocity matrix corrected from NEDC velocities.
        :rtype: dict
        """

        def _set_velocity(velocity, const_steps, window, delta):
            for s in const_steps:
                if s < velocity < s + window:
                    return s + delta
            return velocity

        for k, v in sorted(self.items()):
            v = [
                _set_velocity(v[0], dn_cns_vel, dn_window, dn_delta),
                _set_velocity(v[1], up_cns_vel, up_window, up_delta)
            ]

            if v[0] >= v[1]:
                v[0] = v[1] + dn_delta

            try:
                if self[k - 1][1] <= v[0]:
                    v[0] = self[k - 1][1] + up_delta
            except KeyError:
                pass
            self[k] = tuple(v)

        return self

    def plot(self):
        import matplotlib.pylab as plt
        for k, v in self.items():
            kv = {}
            for (s, l), x in zip((('down', '--'), ('up', '-')), v):
                if x < dfl.INF:
                    kv['label'] = 'Gear %d:%s-shift' % (k, s)
                    kv['linestyle'] = l
                    # noinspection PyProtectedMember
                    kv['color'] = plt.plot([x] * 2, [0, 1], **kv)[0]._color
        plt.legend(loc='best')
        plt.xlabel('Velocity [km/h]')

    def _prepare(self, times, velocities, accelerations, motive_powers,
                 engine_coolant_temperatures):
        keys = sorted(self.keys())
        matrix, r, c = {}, velocities.shape[0], len(keys) - 1
        for i, g in enumerate(keys):
            down, up = self[g]
            matrix[g] = p = np.tile(g, r)
            p[velocities < down] = keys[max(0, i - 1)]
            p[velocities >= up] = keys[min(i + 1, c)]
        return matrix

    def predict(self, times, velocities, accelerations, motive_powers,
                engine_coolant_temperatures=None,
                correct_gear=lambda i, g, *args: g[i],
                gear_filter=define_gear_filter(), index=0, gears=None):
        if gears is None:
            gears = np.zeros_like(times, int)

        for _ in self.yield_gear(
                times, velocities, accelerations, motive_powers,
                engine_coolant_temperatures, correct_gear, index, gears):
            pass

        # if gear_filter is not None:
        #    gears[index:times.shape[0]] = gear_filter(times, gears)

        return gears[index:times.shape[0]]

    @staticmethod
    def get_gear(gear, index, gears, times, velocities, accelerations,
                 motive_powers, engine_coolant_temperatures, matrix):
        return matrix[gear][index]

    def yield_gear(self, times, velocities, accelerations, motive_powers,
                   engine_coolant_temperatures=None,
                   correct_gear=lambda i, g, *args: g[i], index=0, gears=None):

        matrix = self._prepare(
            times, velocities, accelerations, motive_powers,
            engine_coolant_temperatures
        )
        if hasattr(correct_gear, 'prepare'):
            matrix = correct_gear.prepare(
                matrix, times, velocities, accelerations, motive_powers,
                engine_coolant_temperatures
            )

        valid_gears = np.array(list(getattr(self, 'gears', self)))

        def get_valid_gear(g):
            if g in valid_gears:
                return g
            return valid_gears[np.abs(np.subtract(valid_gears, g)).argmin()]

        gear = valid_gears.min()
        if gears is None:
            gears = np.zeros_like(times, int)
        else:
            gear = get_valid_gear(gears[index])

        args = (
            gears, times, velocities, accelerations, motive_powers,
            engine_coolant_temperatures, matrix
        )

        for i in np.arange(index, times.shape[0], dtype=int):
            gear = gears[i] = get_valid_gear(correct_gear(
                self.get_gear(gear, i, *args), i, *args
            ))
            yield gear

    def yield_speed(self, stop_velocity, gears, velocities, *args, **kwargs):
        vsr = self.velocity_speed_ratios
        for g, v in zip(gears, velocities):
            r = v > stop_velocity and vsr.get(g, 0)
            yield v / r if r else 0

    # noinspection PyPep8Naming
    def convert(self, velocity_speed_ratios):
        if velocity_speed_ratios != self.velocity_speed_ratios:
            vsr, n_vsr = self.velocity_speed_ratios, velocity_speed_ratios
            it = [(vsr.get(k, 0), v[0], v[1]) for k, v in self.items()]

            K, X = zip(*[(k, v) for k, v in sorted(n_vsr.items())])

            L, U = _convert_limits(it, X)

            self.clear()

            for k, l, u in sorted(zip(K, L, U), reverse=it[0][0] > it[1][0]):
                self[k] = (l, u)

            self.velocity_speed_ratios = n_vsr

        return self


@sh.add_function(dsp, outputs=['CMV'])
def calibrate_gear_shifting_cmv(
        correct_gear, gears, engine_speeds_out, times, velocities,
        accelerations, motive_powers, velocity_speed_ratios, stop_velocity):
    """
    Calibrates a corrected matrix velocity to predict gears.

    :param correct_gear:
        A function to correct the predicted gear.
    :type correct_gear: callable

    :param gears:
        Gear vector [-].
    :type gears: numpy.array

    :param engine_speeds_out:
        Engine speed vector [RPM].
    :type engine_speeds_out: numpy.array

    :param times:
        Time vector [s].
    :type times: numpy.array

    :param velocities:
        Vehicle velocity [km/h].
    :type velocities: numpy.array

    :param accelerations:
        Vehicle acceleration [m/s2].
    :type accelerations: numpy.array

    :param motive_powers:
        Motive power [kW].
    :type motive_powers: numpy.array

    :param velocity_speed_ratios:
        Constant velocity speed ratios of the gear box [km/(h*RPM)].
    :type velocity_speed_ratios: dict[int | float]

    :param stop_velocity:
        Maximum velocity to consider the vehicle stopped [km/h].
    :type stop_velocity: float

    :returns:
        A corrected matrix velocity to predict gears.
    :rtype: dict
    """

    cmv = CMV().fit(
        correct_gear, gears, engine_speeds_out, times, velocities,
        accelerations, motive_powers, velocity_speed_ratios, stop_velocity
    )

    return cmv


# predict gears with corrected matrix velocity
dsp.add_function(
    function=prediction_gears_gsm,
    inputs=['correct_gear', 'gear_filter', 'CMV', 'times', 'velocities',
            'accelerations', 'motive_powers', 'cycle_type',
            'velocity_speed_ratios'],
    outputs=['gears']
)