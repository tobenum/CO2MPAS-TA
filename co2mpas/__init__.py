# -*- coding: utf-8 -*-
#
# Copyright 2015-2019 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
"Vehicle simulator predicting NEDC CO2 emissions from WLTP time-series.

.. currentmodule:: co2mpas

.. autosummary::
    :nosignatures:
    :toctree: _build/co2mpas/

    ~model
    ~io
    ~batch
    ~datasync
    ~plot
    ~plan
    ~utils
    ~report
"""
import tqdm
import logging
import os.path as osp
import schedula as sh
from ._version import *
from .core import wait_sites, SITES
from .core.write import default_start_time, default_timestamp

log = logging.getLogger(__name__)
dsp = sh.BlueDispatcher(name='process')


def init_conf(inputs):
    """
    Initialize CO2MPAS model configurations.

    :param inputs:
         Initialization inputs.
    :type inputs: dict | schedula.Token

    :return:
        Initialization inputs.
    :rtype: dict | schedula.Token
    """
    if inputs is not sh.NONE and inputs.get('model_conf'):
        from .conf import dfl
        dfl.load(inputs['model_conf'])
    return inputs


dsp.add_data(sh.START, filters=[init_conf, lambda x: sh.NONE])


@sh.add_function(dsp, outputs=['demo'])
def save_demo_files(output_folder):
    """
    Save CO2MPAS demo files.

    :param output_folder:
        Output folder.
    :type output_folder: str
    """
    import glob
    from shutil import copy2
    from pkg_resources import resource_filename
    for src in glob.glob(resource_filename('co2mpas', 'demo/*.xlsx')):
        copy2(src, osp.join(output_folder, osp.basename(src)))


@sh.add_function(dsp, outputs=['template'])
def save_co2mpas_template(output_file):
    """
    Save CO2MPAS input template.

    :param output_file:
        Output file.
    :type output_file: str
    """
    from shutil import copy2
    from pkg_resources import resource_filename
    src = resource_filename('co2mpas', 'templates/co2mpas_template.xlsx')
    copy2(src, output_file)


@sh.add_function(dsp, outputs=['modelconf'])
def save_co2mpas_conf(output_file):
    """
    Save CO2MPAS model configurations.

    :param output_file:
        Output file.
    :type output_file: str
    """
    from .conf import dfl
    dfl.dump(output_file)


@sh.add_function(dsp, outputs=['core_model'])
def register_core():
    """
    Register core model.

    :return:
        CO2MPAS core model.
    :rtype: schedula.Dispatcher
    """
    from .core import dsp
    return dsp.register(memo={})


dsp.add_data('sites', SITES, sh.inf(100, 1))


@sh.add_function(dsp, outputs=['sites'])
def plot_model(core_model, cache_folder):
    """
    Plot CO2MPAS core model.

    :param core_model:
        CO2MPAS core model.
    :type core_model: schedula.Dispatcher

    :param cache_folder:
        Folder to save temporary html files.
    :type cache_folder: str

    :return:
        Running sites.
    :rtype: set
    """
    sites = set()
    core_model.plot(directory=cache_folder, sites=sites)
    return sites


dsp.add_func(
    wait_sites, inputs_kwargs=True, outputs=['plot'], weight=sh.inf(100, 1)
)


def _yield_files(*paths, cache=None):
    import glob
    ext = ('co2mpas.ta', 'xlsx', 'dill', 'xls')
    cache = set() if cache is None else cache
    for path in paths:
        path = osp.abspath(path)
        if path in cache:
            continue
        cache.add(path)
        if osp.isdir(path):
            yield from _yield_files(
                *filter(osp.isfile, glob.glob(osp.join(path, '*'))), cache=cache
            )
        elif osp.isfile(path) and path.endswith(ext):
            yield path
        else:
            raise FileNotFoundError


class _ProgressBar(tqdm.tqdm):
    def __init__(self, *args, _format_meter=None, **kwargs):
        if _format_meter:
            self._format_meter = _format_meter
        super(_ProgressBar, self).__init__(*args, **kwargs)

    @staticmethod
    def _format_meter(bar, data):
        return '%s: Processing %s\n' % (bar, data)

    # noinspection PyMissingOrEmptyDocstring
    def format_meter(self, n, *args, **kwargs):
        bar = super(_ProgressBar, self).format_meter(n, *args, **kwargs)
        try:
            return self._format_meter(bar, self.iterable[n])
        except IndexError:
            return bar


dsp.add_func(default_start_time, outputs=['start_time'])
dsp.add_func(default_timestamp, outputs=['timestamp'])


@sh.add_function(dsp, outputs=['core_solutions'])
def run_core(core_model, cmd_flags, timestamp, input_files, **kwargs):
    """
    Run core model.

    :param core_model:
        CO2MPAS core model.
    :type core_model: schedula.Dispatcher

    :param cmd_flags:
        Command line options.
    :type cmd_flags: dict

    :param timestamp:
        Run timestamp.
    :type timestamp: str

    :param input_files:
        List of input flies and/or folder.
    :type input_files: iterable

    :return:
        Core model solutions.
    :rtype: dict[str, schedula.Solution]
    """
    solutions, it = {}, list(_yield_files(*input_files))
    if it:
        for fp in _ProgressBar(it):
            solutions[fp] = core_model(dict(
                input_file_name=fp, cmd_flags=cmd_flags, timestamp=timestamp
            ), **kwargs)
    return solutions


def _define_inputs(sol, inputs):
    kw = dict(sources=inputs, check_inputs=False, graph=sol.dsp.dmap)
    keys = set(sol) - set(sol.dsp.get_sub_dsp_from_workflow(**kw).data_nodes)
    return sh.combine_dicts({k: sol[k] for k in keys}, inputs)


def _format_meter(bar, row):
    return '%s: Processing %s (%s)\n' % (bar, row['id'], row['base'])


def _run_variations(plan, bases, core_model, timestamp):
    for r in _ProgressBar(plan, _format_meter=_format_meter):
        sol, data = bases[r['base']], r['data']
        if 'solution' in sol:
            s = sol['solution']
            base = _define_inputs(s, sh.combine_nested_dicts(sh.selector(
                data, s, allow_miss=True
            ), data))
        else:
            base = sh.combine_nested_dicts(sol['base'], data, depth=2)

        for i, d in base.items():
            if hasattr(d, 'items'):
                base[i] = {k: v for k, v in d.items() if v is not sh.EMPTY}

        sol = core_model(_define_inputs(sol, dict(
            base=base,
            vehicle_name='-'.join((r['id'], sol['vehicle_name'])),
            timestamp=timestamp
        )))

        summary, keys = {}, {
            tuple(k.split('.')[:0:-1]) for k in base if k.startswith('output.')
        }
        for k, v in data.items():
            k = ('plan %s' % k).split('.')[::-1]
            sh.get_nested_dicts(summary, *k).update(v)

        for k, v in sh.stack_nested_keys(sol['summary'], depth=3):
            if k[:-1] not in keys:
                sh.get_nested_dicts(summary, *k).update(v)
        sol['summary'] = summary
        yield sol


@sh.add_function(dsp, outputs=['solutions'])
def run_plan(core_solutions, core_model, cmd_flags, timestamp):
    """
    Run simulation plans.

    :param core_solutions:
        Core model solutions.
    :type core_solutions:  dict[str, schedula.Solution]

    :param core_model:
        CO2MPAS core model.
    :type core_model: schedula.Dispatcher

    :param cmd_flags:
        Command line options.
    :type cmd_flags: dict

    :param timestamp:
        Run timestamp.
    :type timestamp: str

    :return:
        All model solutions.
    :rtype: list[schedula.Solution]
    """
    bases = core_solutions.copy()
    plan = sum((sol['plan'] for sol in bases.values()), [])  # Merge plans.
    # Run base.
    fp = {r['base'] for r in plan if r['run_base']} - set(bases)
    bases.update(run_core(core_model, cmd_flags, timestamp, fp))
    solutions = list(bases.values())
    # Load inputs.
    fp = {r['base'] for r in plan if not r['run_base']} - set(bases) - fp
    bases.update(run_core(
        core_model, cmd_flags, timestamp, fp, outputs=['base', 'vehicle_name']
    ))
    if plan:
        solutions.extend(_run_variations(plan, bases, core_model, timestamp))
    return solutions


@sh.add_function(dsp, outputs=['summary'])
def get_summary(solutions):
    """
    Extract summary data from model solutions.

    :param solutions:
        All model solutions.
    :type solutions: list[schedula.Solution]

    :return:
        Summary data.
    :rtype: list
    """
    return [sh.combine_dicts(
        dict(sh.stack_nested_keys(sol.get('summary', {}), depth=4)), base={
            'id': sol['vehicle_name'],
            'base': sol['input_file_name']
        }
    ) for sol in solutions]


@sh.add_function(dsp, outputs=['output_summary_file'])
def define_output_summary_file(cmd_flags, timestamp):
    """
    Defines the output summary file path.

    :param cmd_flags:
        Command line options.
    :type cmd_flags: dict

    :param timestamp:
        Run timestamp.
    :type timestamp: str

    :return:
        Output summary file path.
    :rtype: str
    """
    fp = cmd_flags.get('output_folder', './outputs')
    return osp.join(fp, '%s-summary.xlsx' % timestamp)


@sh.add_function(dsp, outputs=['run'])
def save_summary(summary, output_summary_file, start_time):
    """
    Save CO2MPAS model configurations.

    :param summary:
        Summary data.
    :type summary: list

    :param output_summary_file:
        Output summary file path.
    :type output_summary_file: str

    :param start_time:
        Run start time.
    :type start_time: datetime.datetime
    """
    import pandas as pd
    # noinspection PyProtectedMember
    from .core.write.convert import _co2mpas_info2df, _add_units, _sort_key
    df = pd.DataFrame(summary)
    df.set_index(['id', 'base'], inplace=True)
    df = df.reindex(columns=sorted(
        df.columns,
        key=lambda x: _sort_key(x, p_keys=('cycle', 'stage', 'usage', 'param'))
    ))
    df.columns = pd.MultiIndex.from_tuples(_add_units(df.columns))

    with pd.ExcelWriter(output_summary_file) as writer:
        df.to_excel(writer, 'summary')
        _co2mpas_info2df(start_time).to_excel(writer, 'proc_info')


@sh.add_function(dsp, outputs=['done'], weight=sh.inf(100, 0))
def log_done(start_time):
    """
    Logs the overall execution time.

    :param start_time:
        Run start time.
    :type start_time: datetime.datetime

    :return:
        Execution time [s].
    :rtype:
    """
    import datetime
    sec = (datetime.datetime.today() - start_time).total_seconds()
    log.info('Done! [%.2f sec]' % sec)
    return sec
