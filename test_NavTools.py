#!/usr/bin/env python
# -- coding: utf-8 --
# ---------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "NavToolsTesting.py"
__version__ = "version 2.1.0, Python 3.8"
__date__ = "Date: 2022/06/15"
__copyright__ = "Copyright (c) 2022 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-----------------------------------------------------------------------------
  Navigation Tools package test functions
-----------------------------------------------------------------------------
"""
navtools = None
try:
    import sys
    import os
    from typing import Dict
    from NavToolsLib import NavTools

except ImportError as e:
    print("Import error: %s \nAborting the program %s" % (e, __version__))
    sys.exit()

DEFAULT = "2019_12_NYC_Norfolk.gpx"


def float_equality(num1, num2):
    if abs(num1-num2) < 0.00001:
        return True
    else:
        return False


def fetch_file(file):
    inputfile = open(file, "r")
    xml = inputfile.read()
    inputfile.close()
    return xml


def test_library_import():
    global navtools
    navtools = NavTools()


def test_settings():
    settings = navtools.getConfig(verbose=False)
    assert (isinstance(settings, Dict) and len(settings) > 0)


def test_readGPX(file=DEFAULT):
    settings = navtools.getConfig(verbose=False)
    file = os.path.join(settings["gpxPath"], file)
    xml = fetch_file(file)
    assert (len(xml) > 0)


def test_wpDistance():
    assert(float_equality(navtools.calc_distance(
        45.0, -91.0, 46.0, -91.0), 60.10862))
    # equator distances
    assert(float_equality(navtools.calc_distance(
        0.0, -91.0, 0.0, -92.0), 60.10862))


def test_routeDistances(file=DEFAULT):
    settings = navtools.getConfig(verbose=False)
    file = os.path.join(settings["gpxPath"], file)
    xml = fetch_file(file)

    msg = navtools.ComputeRouteDistances(
        xml, verbose=False, skipWP=True, noSpeed=False)
    assert (("6.12kts" in msg) and ("301.28nm" in msg))


if __name__ == "__main__":
    """-------------------------------------------------------------------------
        Script starting point
    """
    print("\nStarting %s" % __app__)
    print(__doc__)
    print("Run this test program using 'pytest -v test_NavTools.py'.\n")
