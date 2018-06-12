# -*- coding: utf-8 -*-
#
# Copyright 2015-2017 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
"""
co2dice: prepare/sign/send/receive/validate/archive Type Approval sampling emails of *co2mpas*.

This is an articulated application comprised of the following:

- A GUI application, based on the :mod:`tkinter` framework;
- a library performing the backend-tasks,
  implemented with :class:`baseapp.Spec` instances;
- the ``co2dice`` hierarchical cmd-line tool,
  implemented with :class:`baseapp.Cmd` instances.

::
           .------------.
    ,-.    |     GUI    |----+
    `-'    *------------*    |   .--------------.
    /|\    .------------.    +---| Spec classes |-.
     |     |  co2dice   |-.  |   *--------------* |
    / \    |    CMDs    |----+     *--------------*
           *------------* |
             *------------*

The ``Spec`` and ``Cmd`` classes are build on top of the
`traitlets framework <http://traitlets.readthedocs.io/>`
to read and validate configuration parameters found in files
and/or cmd-line arguments (see :mod:`baseapp`).

For usage examples read the "Random Sampling" section in the manual (http://co2mpas.io).
"""
from collections import namedtuple, defaultdict
import enum
from polyversion import polyversion, polytime
import re
from typing import Text, Tuple

from .._vendor import traitlets as trt

__copyright__ = "Copyright (C) 2015-2018 European Commission (JRC)"
__license__   = "EUPL 1.1+"
__title__     = "co2dice"
__summary__   = __doc__.splitlines()[0]
__uri__       = "https://co2mpas.io"

## FIXME: change projectname when co2dice graduates to own project.
__version__ = polyversion(pname='co2mpas', mono_project=True)
version = __version__
__updated__ = polytime()


class CmdException(trt.TraitError):
    pass


_file_arg_regex = re.compile('(inp|out)=(.+)', re.IGNORECASE)

all_io_kinds = tuple('inp out other'.split())


class PFiles(namedtuple('PFiles', all_io_kinds)):
    """
    Holder of project-files stored in the repository.

    :ivar inp:   ``[fname1, ...]``
    :ivar out:   ``[fname1, ...]``
    :ivar other: ``[fname1, ...]``
    """
    ## INFO: Defined here to avoid circular deps between report.py <-> project.py,
    #  because it is used in their function declarations.

    @staticmethod
    def io_kinds_list(*io_kinds) -> Tuple[Text]:
        """
        :param io_kinds:
            if none specified, return all kinds,
            otherwise, validates and converts everything into a string.
        """
        if not io_kinds:
            io_kinds = all_io_kinds
        else:
            assert not (set(io_kinds) - set(all_io_kinds)), (
                "Invalid io-kind(s): ", set(io_kinds) - set(all_io_kinds))
        return tuple(set(io_kinds))

    def nfiles(self):
        return sum(len(f) for f in self._asdict().values())

    def find_nonfiles(self):
        import os.path as osp
        import itertools as itt

        return [fpath for fpath in
                itt.chain(self.inp, self.out, self.other)
                if not osp.isfile(fpath)]

    def check_files_exist(self, name):
        badfiles = self.find_nonfiles()
        if badfiles:
            raise CmdException("%s: cannot find %i file(s): %s" %
                               (name, len(badfiles), badfiles))


#: Allow creation of PFiles with partial arguments.
PFiles.__new__.__defaults__ = ([], ) * len(all_io_kinds)
