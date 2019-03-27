# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
Functions and a model `dsp` to model the mechanic of the vehicle.
"""
import schedula as sh
from .defaults import dfl

dsp = sh.BlueDispatcher(
    name='Vehicle free body diagram',
    description='Calculates forces and power acting on the vehicle.'
)


@sh.add_function(dsp, outputs=['velocities'])
def calculate_velocities(times, obd_velocities):
    """
    Filters the obd velocities [km/h].

    :param times:
        Time vector [s].
    :type times: numpy.array

    :param obd_velocities:
        OBD velocity vector [km/h].
    :type obd_velocities: numpy.array

    :return:
        Velocity vector [km/h].
    :rtype: numpy.array
    """
    from co2mpas.utils import median_filter
    import numpy as np
    dt_window = dfl.functions.calculate_velocities.dt_window
    return median_filter(times, obd_velocities, dt_window, np.mean)


@sh.add_function(dsp, outputs=['accelerations'])
def calculate_accelerations(times, velocities):
    """
    Calculates the acceleration from velocity time series [m/s2].

    :param times:
        Time vector [s].
    :type times: numpy.array

    :param velocities:
        Velocity vector [km/h].
    :type velocities: numpy.array

    :return:
        Acceleration vector [m/s2].
    :rtype: numpy.array
    """
    from scipy.interpolate import InterpolatedUnivariateSpline as Spl
    acc = Spl(times, velocities / 3.6).derivative()(times)
    b = (velocities[:-1] == 0) & (velocities[1:] == velocities[:-1])
    acc[:-1][b] = 0
    if b[-1]:
        acc[-1] = 0
    return acc


@sh.add_function(dsp, outputs=['aerodynamic_resistances'])
def calculate_aerodynamic_resistances(f2, velocities):
    """
    Calculates the aerodynamic resistances of the vehicle [N].

    :param f2:
        As used in the dyno and defined by respective guidelines [N/(km/h)^2].
    :type f2: float

    :param velocities:
        Velocity vector [km/h].
    :type velocities: numpy.array | float

    :return:
        Aerodynamic resistance vector [N].
    :rtype: numpy.array | float
    """

    return f2 * velocities ** 2


dsp.add_data('n_passengers', dfl.values.n_passengers)
dsp.add_data('passenger_mass', dfl.values.passenger_mass)
dsp.add_data('cargo_mass', dfl.values.cargo_mass)
dsp.add_data('fuel_mass', dfl.values.fuel_mass)


@sh.add_function(dsp, outputs=['passengers_mass'])
def calculate_passengers_mass(n_passengers, passenger_mass):
    """
    Calculate passengers mass including driver [kg].

    :param n_passengers:
        Number of passengers including driver [-].
    :type n_passengers: int

    :param passenger_mass:
        Average passenger mass [kg].
    :type passenger_mass: float

    :return:
        Passengers mass including the driver [kg].
    :rtype: float
    """

    return passenger_mass * n_passengers


@sh.add_function(dsp, outputs=['unladen_mass'])
def calculate_unladen_mass(curb_mass, fuel_mass):
    """
    Calculate unladen mass [kg].

    :param curb_mass:
        Curb mass [kg].
    :type curb_mass: float

    :param fuel_mass:
        Fuel mass [kg].
    :type fuel_mass: float

    :return:
        Unladen mass [kg].
    :rtype: float
    """

    return curb_mass + fuel_mass


@sh.add_function(dsp, outputs=['unladen_mass'])
def calculate_unladen_mass_v1(vehicle_mass, passengers_mass, cargo_mass):
    """
    Calculate unladen mass [kg].

    :param vehicle_mass:
        Vehicle mass [kg].
    :type vehicle_mass: float

    :param passengers_mass:
        Passengers mass including the driver [kg].
    :type passengers_mass: float

    :param cargo_mass:
        Cargo mass [kg].
    :type cargo_mass: float

    :return:
        Unladen mass [kg].
    :rtype: float
    """

    return vehicle_mass - passengers_mass - cargo_mass


@sh.add_function(dsp, outputs=['curb_mass'])
def calculate_curb_mass(unladen_mass, fuel_mass):
    """
    Calculate unladen mass [kg].

    :param unladen_mass:
        Unladen mass [kg].
    :type unladen_mass: float

    :param fuel_mass:
        Fuel mass [kg].
    :type fuel_mass: float

    :return:
        Curb mass [kg].
    :rtype: float
    """

    return unladen_mass - fuel_mass


@sh.add_function(dsp, outputs=['vehicle_mass'])
def calculate_vehicle_mass(unladen_mass, passengers_mass, cargo_mass):
    """
    Calculate vehicle_mass [kg].

    :param unladen_mass:
        Unladen mass [kg].
    :type unladen_mass: float

    :param passengers_mass:
        Passengers mass including the driver [kg].
    :type passengers_mass: float

    :param cargo_mass:
        Cargo mass [kg].
    :type cargo_mass: float

    :return:
        Vehicle mass [kg].
    :rtype: float
    """

    return unladen_mass + passengers_mass + cargo_mass


@sh.add_function(dsp, outputs=['raw_frontal_area'])
def calculate_raw_frontal_area(vehicle_height, vehicle_width):
    """
    Calculates raw frontal area of the vehicle [m2].

    :param vehicle_height:
        Vehicle height [m].
    :type vehicle_height: float

    :param vehicle_width:
        Vehicle width [m].
    :type vehicle_width: float

    :return:
        Raw frontal area of the vehicle [m2].
    :rtype: float
    """
    return vehicle_height * vehicle_width


@sh.add_function(dsp, outputs=['raw_frontal_area'], weight=5)
def calculate_raw_frontal_area_v1(vehicle_mass, vehicle_category):
    """
    Calculates raw frontal area of the vehicle [m2].

    :param vehicle_mass:
        Vehicle mass [kg].
    :type vehicle_mass: float

    :param vehicle_category:
        Vehicle category (i.e., A, B, C, D, E, F, S, M, and J).
    :type vehicle_category: str

    :return:
        Raw frontal area of the vehicle [m2].
    :rtype: float
    """
    from asteval import Interpreter as Interp
    d = dfl.functions.calculate_raw_frontal_area_v1
    return Interp().eval(d.formulas[vehicle_category.upper()])(vehicle_mass)


@sh.add_function(dsp, outputs=['frontal_area'])
def calculate_frontal_area(raw_frontal_area):
    """
    Calculates the vehicle frontal area [m2].

    :param raw_frontal_area:
        Raw frontal area of the vehicle [m2].
    :type raw_frontal_area: float

    :return:
        Frontal area of the vehicle [m2].
    :rtype: float
    """
    d = dfl.functions.calculate_frontal_area.projection_factor
    return raw_frontal_area * d


@sh.add_function(dsp, outputs=['aerodynamic_drag_coefficient'])
def calculate_aerodynamic_drag_coefficient(vehicle_category):
    """
    Calculates the aerodynamic drag coefficient [-].

    :param vehicle_category:
        Vehicle category (i.e., A, B, C, D, E, F, S, M, and J).
    :type vehicle_category: str

    :return:
        Aerodynamic drag coefficient [-].
    :rtype: float
    """
    d = dfl.functions.calculate_aerodynamic_drag_coefficient
    return d.cw[vehicle_category.upper()]


@sh.add_function(dsp, outputs=['aerodynamic_drag_coefficient'])
def calculate_aerodynamic_drag_coefficient_v1(vehicle_body):
    """
    Calculates the aerodynamic drag coefficient [-].

    :param vehicle_body:
        Vehicle body (i.e., cabriolet, sedan, hatchback, stationwagon,
        suv/crossover, mpv, coupé, bus, bestelwagen, pick-up).
    :type vehicle_body: str

    :return:
        Aerodynamic drag coefficient [-].
    :rtype: float
    """
    d = dfl.functions.calculate_aerodynamic_drag_coefficient_v1
    return d.cw[vehicle_body.lower()]


dsp.add_data('air_temperature', dfl.values.air_temperature)
dsp.add_data('atmospheric_pressure', dfl.values.atmospheric_pressure)


@sh.add_function(dsp, outputs=['air_density'])
def calculate_air_density(air_temperature, atmospheric_pressure):
    """
    Calculates the air density [kg/m3].

    :param air_temperature:
        Air temperature [°C].
    :type air_temperature: float

    :param atmospheric_pressure:
        Atmospheric pressure [kPa].
    :type atmospheric_pressure: float

    :return:
        Air density [kg/m3].
    :rtype: float
    """
    # http://www.thecartech.com/subjects/auto_eng/Road_loads.htm
    return 3.48 * atmospheric_pressure / (273.16 + air_temperature)


dsp.add_data('has_roof_box', dfl.values.has_roof_box)


@sh.add_function(dsp, outputs=['f2'], weight=5)
def calculate_f2(
        air_density, aerodynamic_drag_coefficient, frontal_area, has_roof_box):
    """
    Calculates the f2 coefficient [N/(km/h)^2].

    :param air_density:
        Air density [kg/m3].
    :type air_density: float

    :param aerodynamic_drag_coefficient:
        Aerodynamic drag coefficient [-].
    :type aerodynamic_drag_coefficient: float

    :param frontal_area:
        Frontal area of the vehicle [m2].
    :type frontal_area: float
    
    :param has_roof_box:
         Has the vehicle a roof box? [-].
    :type has_roof_box: bool

    :return:
        As used in the dyno and defined by respective guidelines [N/(km/h)^2].
    :rtype: float
    """

    c = aerodynamic_drag_coefficient * frontal_area * air_density

    if has_roof_box:
        c *= dfl.functions.calculate_f2.roof_box

    return 0.5 * c / 3.6 ** 2


dsp.add_data('tyre_class', dfl.values.tyre_class)


@sh.add_function(dsp, outputs=['rolling_resistance_coeff'])
def calculate_rolling_resistance_coeff(tyre_class, tyre_category):
    """
    Calculates the rolling resistance coefficient [-].

    :param tyre_class: 
        Tyre class (i.e., C1, C2, and C3).
    :type tyre_class: str

    :param tyre_category: 
        Tyre category (i.e., A, B, C, D, E, F, and G).
    :type tyre_category: str

    :return: 
        Rolling resistance coefficient [-].
    :rtype: float
    """
    coeff = dfl.functions.calculate_rolling_resistance_coeff.coeff
    return coeff[tyre_class.upper()][tyre_category.upper()]


@sh.add_function(dsp, outputs=['f0'], weight=5)
def calculate_f0(vehicle_mass, rolling_resistance_coeff):
    """
    Calculates rolling resistance [N].

    :param vehicle_mass:
        Vehicle mass [kg].
    :type vehicle_mass: float

    :param rolling_resistance_coeff:
        Rolling resistance coefficient [-].
    :type rolling_resistance_coeff: float

    :return:
        Rolling resistance force [N] when angle_slope == 0.
    :rtype: float
    """

    return vehicle_mass * 9.81 * rolling_resistance_coeff


@sh.add_function(dsp, outputs=['f1'], weight=5)
def calculate_f1(f2):
    """
    Calculates the f1 road load [N/(km/h)].

    :param f2:
        As used in the dyno and defined by respective guidelines [N/(km/h)^2].
    :type f2: float

    :return: 
        Defined by dyno procedure [N/(km/h)].
    :rtype: float
    """

    q, m = dfl.functions.calculate_f1.qm
    return m * f2 + q


dsp.add_data('angle_slope', dfl.values.angle_slope)


@sh.add_function(dsp, outputs=['distances'])
def calculate_distances(times, velocities):
    """
    Calculates the cumulative distance vector [m].

    :param times:
        Time vector [s].
    :type times: numpy.array

    :param velocities:
        Velocity vector [km/h].
    :type velocities: numpy.array

    :return:
        Cumulative distance vector [m].
    :rtype: numpy.array
    """
    from scipy.integrate import cumtrapz
    return cumtrapz(velocities / 3.6, times, initial=0)


@sh.add_function(dsp, outputs=['angle_slopes'])
def calculate_angle_slopes(distances, elevations):
    """
    Returns the angle slope vector [rad].

    :param distances:
       Cumulative distance vector [m].
    :type distances: numpy.array

    :param elevations:
        Elevation vector [m].
    :type elevations: numpy.array

    :return:
       Angle slope vector [rad].
    :rtype: numpy.array
    """
    import numpy as np
    from scipy.interpolate import InterpolatedUnivariateSpline as Spl
    i = np.append([0], np.where(np.diff(distances) > 0)[0] + 1)
    return np.arctan(Spl(distances[i], elevations[i]).derivative()(distances))


@sh.add_function(dsp, outputs=['angle_slopes'], weight=5)
def calculate_angle_slopes_v1(times, angle_slope):
    """
    Returns the angle slope vector [rad].

    :param times:
        Time vector [s].
    :type times: numpy.array

    :param angle_slope:
         Angle slope [rad].
    :type angle_slope: float

    :return:
        Angle slope vector [rad].
    :rtype: numpy.array
    """
    import numpy as np
    return np.ones_like(times, dtype=float) * angle_slope


@sh.add_function(dsp, outputs=['rolling_resistance'])
def calculate_rolling_resistance(f0, angle_slopes):
    """
    Calculates rolling resistance [N].

    :param f0:
        Rolling resistance force [N] when angle_slope == 0.
    :type f0: float

    :param angle_slopes:
        Angle slope vector [rad].
    :type angle_slopes: numpy.array

    :return:
        Rolling resistance force [N].
    :rtype: numpy.array
    """
    import numpy as np
    return f0 * np.cos(angle_slopes)


@sh.add_function(dsp, outputs=['velocity_resistances'])
def calculate_velocity_resistances(f1, velocities):
    """
    Calculates forces function of velocity [N].

    :param f1:
        Defined by dyno procedure [N/(km/h)].
    :type f1: float

    :param velocities:
        Velocity vector [km/h].
    :type velocities: numpy.array | float

    :return:
        Forces function of velocity [N].
    :rtype: numpy.array | float
    """

    return f1 * velocities


@sh.add_function(dsp, outputs=['climbing_force'])
def calculate_climbing_force(vehicle_mass, angle_slopes):
    """
    Calculates the vehicle climbing resistance [N].

    :param vehicle_mass:
        Vehicle mass [kg].
    :type vehicle_mass: float

    :param angle_slopes:
        Angle slope vector [rad].
    :type angle_slopes: numpy.array

    :return:
        Vehicle climbing resistance [N].
    :rtype: numpy.array
    """
    import numpy as np
    return vehicle_mass * 9.81 * np.sin(angle_slopes)


@sh.add_function(dsp, outputs=['n_dyno_axes'])
def select_default_n_dyno_axes(cycle_type, n_wheel_drive):
    """
    Selects the default number of dyno axes[-].

    :param cycle_type:
        Cycle type (WLTP or NEDC).
    :type cycle_type: str

    :param n_wheel_drive:
        Number of wheel drive [-].
    :type n_wheel_drive: int

    :return:
        Number of dyno axes [-].
    :rtype: int
    """
    par = dfl.functions.select_default_n_dyno_axes

    try:
        return par.DYNO_AXES[cycle_type.upper()][n_wheel_drive]
    except KeyError:
        return n_wheel_drive // 2


@sh.add_function(dsp, outputs=['inertial_factor'])
def select_inertial_factor(n_dyno_axes):
    """
    Selects the inertia factor [%] according to the number of dyno axes.

    :param n_dyno_axes:
        Number of dyno axes [-].
    :type n_dyno_axes: int

    :return:
        Factor that considers the rotational inertia [%].
    :rtype: float
    """

    return 1.5 * n_dyno_axes


@sh.add_function(dsp, outputs=['rotational_inertia_forces'])
def calculate_rotational_inertia_forces(
        vehicle_mass, inertial_factor, accelerations):
    """
    Calculate rotational inertia forces [N].

    :param vehicle_mass:
        Vehicle mass [kg].
    :type vehicle_mass: float

    :param inertial_factor:
        Factor that considers the rotational inertia [%].
    :type inertial_factor: float

    :param accelerations:
        Acceleration vector [m/s2].
    :type accelerations: numpy.array | float

    :return:
        Rotational inertia forces [N].
    :rtype: numpy.array | float
    """

    return vehicle_mass * inertial_factor * accelerations / 100


# noinspection PyPep8Naming
@sh.add_function(dsp, outputs=['motive_forces'])
def calculate_motive_forces(
        vehicle_mass, accelerations, climbing_force, aerodynamic_resistances,
        rolling_resistance, velocity_resistances, rotational_inertia_forces):
    """
    Calculate motive forces [N].

    :param vehicle_mass:
        Vehicle mass [kg].
    :type vehicle_mass: float

    :param accelerations:
        Acceleration vector [m/s2].
    :type accelerations: numpy.array | float

    :param climbing_force:
        Vehicle climbing resistance [N].
    :type climbing_force: float | numpy.array

    :param rolling_resistance:
        Rolling resistance force [N].
    :type rolling_resistance: float | numpy.array

    :param aerodynamic_resistances:
        Aerodynamic resistance vector [N].
    :type aerodynamic_resistances: numpy.array | float

    :param velocity_resistances:
        Forces function of velocity [N].
    :type velocity_resistances: numpy.array | float

    :param rotational_inertia_forces:
        Rotational inertia forces [N].
    :type rotational_inertia_forces: numpy.array | float

    :return:
        Motive forces [N].
    :rtype: numpy.array | float
    """

    # namespace shortcuts
    Frr = rolling_resistance
    Faero = aerodynamic_resistances
    Fclimb = climbing_force
    Fvel = velocity_resistances
    Finertia = rotational_inertia_forces

    return vehicle_mass * accelerations + Fclimb + Frr + Faero + Fvel + Finertia


@sh.add_function(dsp, outputs=['motive_powers'])
def calculate_motive_powers(motive_forces, velocities):
    """
    Calculates motive power [kW].

    :param motive_forces:
        Motive forces [N].
    :type motive_forces: numpy.array | float

    :param velocities:
        Velocity vector [km/h].
    :type velocities: numpy.array | float

    :return:
        Motive power [kW].
    :rtype: numpy.array | float
    """

    return motive_forces * velocities / 3600


dsp.add_data(
    'road_loads', description='Cycle road loads [N, N/(km/h), N/(km/h)^2].'
)
dsp.add_function('grouping', sh.bypass, ['f0', 'f1', 'f2'], ['road_loads'])
dsp.add_function('splitting', sh.bypass, ['road_loads'], ['f0', 'f1', 'f2'])
dsp.add_data('correct_f0', dfl.values.correct_f0)


@sh.add_function(dsp, outputs=['f0'])
def apply_f0_correction(f0_uncorrected, correct_f0):
    """
    Corrects the rolling resistance force [N] if a different preconditioning
    cycle was used for WLTP (WLTP precon) and NEDC (NEDC precon).

    :param f0_uncorrected:
        Uncorrected rolling resistance force [N] when angle_slope == 0.
    :type f0_uncorrected: float

    :param correct_f0:
        A different preconditioning cycle was used for WLTP and NEDC?
    :type correct_f0: bool

    :return:
        Rolling resistance force [N] when angle_slope == 0.
    :rtype: float
    """

    if correct_f0:
        return f0_uncorrected - 6.0
    return f0_uncorrected
