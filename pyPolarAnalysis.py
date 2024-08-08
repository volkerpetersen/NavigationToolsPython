#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from __future__ import unicode_literals
# --------------------------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__version__ = "pyPolarAnalysis.py (ver 2.1.0)"
__date__ = "Date: 2019/11/06"
__copyright__ = "Copyright (c) 2019 Volker Petersen"
__license__ = "Python 3.7 | GPL http://www.gnu.org/licenses/gpl.txt"
__doc__ = """
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
"""

try:
    import sys
    import math
    import matplotlib.pyplot as plt
    import numpy as np
    from tabulate import tabulate
    from sklearn.metrics import r2_score
except ImportError as e:
    print("Import error: %s\nAborting the program %s" % (str(e), __version__))
    sys.exit()


def read_csv(filename):
    polar = np.genfromtxt(filename, delimiter=',', skip_header=1)
    TWS = polar[0]
    TWA = polar[:, 0]
    return (polar[1:, 1:], TWA[1:], TWS[1:])


def polynomial(bsp, twa, tws):
    z = np.polyfit(twa, bsp, 5)
    np.set_printoptions(precision=4)
    print("Polynomial Coeff. at %2d TWS: " % tws)
    print("    ", z)
    p = np.poly1d(z)
    rsquared = r2_score(bsp, p(twa))
    print("R-squared: %.2f%%\n" % (100.0*rsquared))

    '''
	TWA = np.linspace(30, 180, num=75)
	plt.figure()
	plt.plot(twa, bsp, '.', TWA, p(TWA), '-')
	plt.title('TWS: %2d' %tws)
	plt.ylabel('Boat Speed (kts)')
	plt.xlabel('TWA (kts)')
	plt.grid(True)
	plt.show()
	'''
    return (p, rsquared)


def distance_sailed(distanceToMark, headingToMark, twa, bsp, tackangle):
    twa = math.radians(twa)
    hdg = math.radians(headingToMark)
    tack = math.radians(tackangle)

    a = distanceToMark * math.cos(twa - hdg)
    b = distanceToMark * math.sin(twa - hdg)
    if (tack == 0.0):
        c = b / math.tan(math.radians(180.0) - 2.0*twa)
    else:
        c = b / math.tan(math.radians(180.0) - twa - tack)

    distance = a + c + math.sqrt(b*b + c*c)
    time = distance / bsp

    return(time, distance)


def vmc_info(distanceToMark, headingToMark, TWA, BSP):
    # first iteration - find the optimum TWA for beating into the wind
    minTWA = 0.0
    minTime = False
    minDistance = 0.0
    idx = 0
    for twa in TWA:
        (time, distance) = distance_sailed(
            distanceToMark, headingToMark, twa, BSP[idx], 0.0)
        if (not minTime or minTime > time):
            minTime = time
            minDistance = distance
            minTWA = twa
            minBSP = BSP[idx]

        #opt.append([tws, twa, BSP[idx], distance, time])
        idx = idx + 1

    # second iteration - find the optimum TWA toward the mark
    minTWA = 0.0
    minTime = False
    minDistance = 0.0
    idx = 0
    for twa in TWA:
        (time, distance) = distance_sailed(
            distanceToMark, headingToMark, twa, BSP[idx], minTWA)
        if (not minTime or minTime > time):
            minTime = time
            minDistance = distance
            minTWA = twa
            minBSP = BSP[idx]

        #opt.append([tws, twa, BSP[idx], distance, time])
        idx = idx + 1

    return(minBSP, minDistance, minTime, minTWA)


if __name__ == "__main__":
    print("\nStarting %s" % __version__)
    print(__doc__)

    # print(os.getcwd())

    # polar is 2d numpy array with columns as TWS and rows as TWA
    (polar, TWA, TWS) = read_csv("J109-ODJib-ODSpin.csv")
    print(TWA)
    predictionModels = {}
    color = ['b', 'g', 'r', 'c', 'y', 'k', 'm']
    line = 0
    plt.figure(figsize=(9, 9))
    twa = np.linspace(20, 170, num=75)
    for tws in TWS:
        twsstr = 'TWS %2d' % tws
        (p, rsquared) = polynomial(polar[:, line], TWA, tws)
        predictionModels[tws] = p
        bsp = p(twa)
        plt.plot(twa, bsp, '-', color=color[line])
        line = line + 1
    plt.title('Boat Speed over TWA')
    plt.legend([' 6', ' 8', '10', '12', '14', '16', '20'], loc=2)
    plt.xlabel('TWA')
    plt.ylabel('BSP (kts)')
    plt.grid(True)
    plt.show()

    twa = np.linspace(25, 85, 200)
    rows = []
    headingToMark = 25.0
    distanceToMark = 11.0  # in nm
    minValues = {}
    for tws in TWS:
        p = predictionModels[tws]
        bsp = p(twa)
        (minBSP, minDistance, minTime, minTWA) = vmc_info(
            distanceToMark, headingToMark, twa, bsp)
        rows.append([tws, minTWA, minBSP, minDistance, minTime])
        minValues[tws] = [minTWA, minBSP]

    print("Optimium TWA for each TWS for a %.1fmn distance to mark at heading %.1f:" % (
        distanceToMark, headingToMark))
    print(tabulate(rows,
                   headers=["TWS", "TWA", "BSP", "Distance", "Time"],
                   floatfmt=',.2f', numalign="right"))

    # create polar diagram
    twa = np.linspace(30, 180, num=75)
    theta = np.radians(twa)
    fig = plt.figure(figsize=(9, 9))
    ax = plt.subplot(111, polar=True)
    line = 0
    for tws in TWS:
        twsSTR = "%2d" % tws
        p = predictionModels[tws]
        bsp = p(twa)
        ax.plot(theta, bsp, color=color[line], ls='-', lw=2, label=twsSTR)
        ax.plot(np.radians(minValues[tws][0]),
                minValues[tws][1], 'o', lw=4, color='k')
        line = line + 1

    ax.set_theta_offset(0.5*np.pi)  # set theta axis offset of 90 degrees so
    # that 0 degrees is on top
    ax.set_theta_direction(-1)      # set theta axis to clockwise
    plt.show()
