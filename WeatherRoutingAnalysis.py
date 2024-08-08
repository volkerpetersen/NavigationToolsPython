#!/usr/bin/env python
# -- coding: utf-8 --
# ---------------------------------------------------------------------------
__author__ = "Volker Petersen <volker.petersen01@gmail.com>"
__app__ = "WeatherRoutingAnalysis.py"
__version__ = "version 1.0.0, Python >3.11.0"
__date__ = "Date: 2024/05/28"
__copyright__ = "Copyright (c) 2024 Volker Petersen"
__license__ = "GNU General Public License, published by the Free Software Foundation"
__doc__ = """
-----------------------------------------------------------------------------
 Summarize and plot Expedition's Routing Analysis csv file 
-----------------------------------------------------------------------------
"""

try:
    import sys
    import os
    import csv
    import matplotlib.pyplot as plt
    import time
    from pypdf import PdfWriter
    import subprocess

except ImportError as e:
    print(
        f"Import error: {str(e)} \nAborting the program {__app__}")
    sys.exit()

sails = []
pdfList = []
io_retries = 3

plt.style.use('ggplot')
#plt.style.use('fivethirtyeight')
# global plot parameters
linewidth = 1                  # linewidth for all lines
markerSize = 5                 # marker size for line plots
barColor = 'steelblue'  # marker color for scatter plots
gridColor = 'dimGrey'          # color of the plot grids
figsize = (13, 8)              # size of all plot windows

def save_plot(name, fig, addToList=True, showPlot=False):
    """---------------------------------------------------------------------
    save a plot figure to file

    Args:
        name (string):        file name for the plot
        fig (matplotlib obj): matplotlib figure to work on
        addToList (boolean):  when True add plot to settings['plotlist']
        showPlot (boolean):   when True, display the plot

    Returns:
        success (boolean)
    """
    i = 0
    success = True

    while i < io_retries:
        try:
            fig.savefig(name, bbox_inches="tight", pad_inches=0.25)
            if addToList:
                pdfList.append(name)
            break
        except Exception as e:
            print(f"Warning: Failed {i+1} of {io_retries} attempts "
                  f"to save plot '{name}' with error.\n'{str(e)}'\n"
                  f"Trying again in 5 seconds....\n")
            time.sleep(5)   # wait 5 seconds
        i = i + 1
    if(i >= io_retries):
        success = False
        print(
            f"ERROR: Failed {io_retries} attempts to save plot '{name}'\nSkipping this plot.")

    return success


def read_Expedition_Routing_Analysis(path, filename):
    """---------------------------------------------------------------------
    summarize and Expedition Weather Routing Analysis csv file

    Args:
        path (string):        path to the csv file
        filename (string):    file name of the csv file to be processed

    Returns:
        summary (dict):       dictionary with the results
    """
    filepath = os.path.join(path, filename)
    if not os.path.isfile(filepath):
        print(f"\nCan't locate file '{filepath}'. Teminating App!")
        summary = {}
        return summary
    
    twa = ['n/a']
    summary = {'tws': {}, 'twa': {}, 'sails': {}, 'hours': 0}

    with open(filepath) as csv_file:
        windFlag = False
        sailFlag = False
        reader = csv.reader(csv_file)
        for row in reader:
            if windFlag and len(row) and len(row[0]):
                if row[0] not in summary['tws']:
                    tws = f"{row[0]}"
                    summary['tws'][tws] = 0
                for idx in range(1,len(row)):
                    try:
                        summary['twa'][twa[idx]] += float(row[idx])
                        summary['tws'][tws] += float(row[idx])
                        summary['hours'] += float(row[idx])
                    except Exception as e:
                        print(f"Error parsing the csv file with error code '{str(e)}' in row")
                        print(row)
                        summary = {}
                        return summary
            if sailFlag and len(row) and len(row[0]):
                if row[0] not in summary['sails']:
                    summary['sails'][row[0]] = float(row[1])
                else:
                    summary['sails'][row[0]] = float(row[1])
            if len(row) and 'tws' in row[0].lower():
                windFlag = True
                for idx in range(1, len(row)):
                    summary['twa'][row[idx]] = 0
                    twa.append(row[idx])
            if len(row) and 'sails' in row[0].lower():
                sailFlag = True
                windFlag = False
                for sail in sails:
                    summary['sails'][sail] = 0
            if not len(row) or not len(row[0]):
                windFlag = False
                sailFlag = False
    return summary

def create_one_page_report(exp, routingPath, inputFile):
    xlabel = f"Percentage of {exp['hours']:.2f} hrs race"
    figCtr = 1
    fig = plt.figure(figCtr, figsize=(8,12))
    axs = fig.subplots(nrows=3, ncols=1, sharex=False)
    
    # first subplot
    percent = [val / exp['hours'] for val in list(exp['tws'].values())]
    ax = axs[0]
    ax.barh(list(exp['tws'].keys()), 
                percent, color=barColor, align='center')
    ax.grid(color=gridColor)
    xticks = ax.get_xticks()
    xlabels = [f"{x*100:,.1f}%" for x in xticks]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    ax.set_title("TWS Distribution")
    ax.set_ylabel("TWS (kts)")

    # second subplot
    percent = [val / exp['hours'] for val in list(exp['twa'].values())]
    ax = axs[1]
    ax.barh(list(exp['twa'].keys()), 
                percent, color=barColor, align='center')
    ax.grid(color=gridColor)
    xticks = ax.get_xticks()
    xlabels = [f"{x*100:,.1f}%" for x in xticks]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    ax.set_title("TWA Distribution")
    ax.set_ylabel("TWA (degrees)")

    # third subplot
    percent = [val / exp['hours'] for val in list(exp['sails'].values())]
    ax = axs[2]
    ax.barh(list(exp['sails'].keys()), 
                percent, color=barColor, align='center')
    ax.grid(color=gridColor)
    xticks = ax.get_xticks()
    xlabels = [f"{x*100:,.1f}%" for x in xticks]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    ax.set_title("Sail Utilization")
    ax.set_ylabel("Sails")
    ax.set_xlabel(xlabel)

    name = inputFile.replace(".csv", "_Analysis.pdf")
    fname = os.path.normpath(os.path.join(routingPath, name))

    success = save_plot(fname, fig, addToList=False, showPlot=False)
    if success:
        return fname
    else:
        return None

def create_three_page_report(exp, routingPath, inputFile):
    xlabel = f"Percentage of {exp['hours']:.2f} hrs race"
    figCtr = 1
    fig = plt.figure(figCtr, figsize=figsize)
    percent = [val / exp['hours'] for val in list(exp['tws'].values())]
    plt.barh(list(exp['tws'].keys()), 
                percent, color=barColor, align='center')
    plt.grid(color=gridColor)
    ax = plt.gca()
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{x*100:,.1f}%" for x in xticks])
    plt.title("TWS Distribution")
    plt.ylabel("TWS (kts)")
    plt.xlabel(xlabel)

    name = os.path.normpath(os.path.join(routingPath, "twsPlot.pdf"))
    save_plot(name, fig, addToList=True, showPlot=False)

    figCtr += 1
    fig = plt.figure(figCtr, figsize=figsize)
    percent = [val / exp['hours'] for val in list(exp['twa'].values())]
    plt.barh(list(exp['twa'].keys()), 
                percent, color=barColor, align='center')
    plt.grid(color=gridColor)
    ax = plt.gca()
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{x*100:,.1f}%" for x in xticks])
    plt.title("TWA Distribution")
    plt.ylabel("TWA (degrees)")
    plt.xlabel(xlabel)

    name = os.path.normpath(os.path.join(routingPath, "twaPlot.pdf"))
    save_plot(name, fig, addToList=True, showPlot=False)

    figCtr += 1
    fig = plt.figure(figCtr, figsize=figsize)
    percent = [val / exp['hours'] for val in list(exp['sails'].values())]
    plt.barh(list(exp['sails'].keys()), 
                percent, color=barColor, align='center')
    plt.grid(color=gridColor)
    ax = plt.gca()
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{x*100:,.1f}%" for x in xticks])
    plt.title("Sail Utilization")
    plt.ylabel("Sails")
    plt.xlabel(xlabel)

    name = os.path.normpath(os.path.join(routingPath, "sails.pdf"))
    save_plot(name, fig, addToList=True, showPlot=False)


    mergedPDF = PdfWriter()
    for pdfName in pdfList:
        title = os.path.basename(pdfName)
        title = title.replace(".pdf", "")
        title = title.upper()

        i = 0
        while i < io_retries:
            try:
                mergedPDF.append(pdfName, outline_item=title)
                break                   
            except Exception as e:
                print(f"Warning: Failed {i+1} of {io_retries} attempts "
                      f"to merge PDF '{pdfName}'.\n'{str(e)}'\n"
                      f"Trying again in 5 seconds....\n")
                time.sleep(5)   # wait 5 seconds
            i = i + 1
        if(i >= io_retries):
            print(
                f"ERROR: Failed {io_retries} attempts to merge PDF '{pdfName}'\nSkipping this PDF.")

    name = inputFile.replace(".csv", "_Analysis.pdf")
    filename = os.path.normpath(os.path.join(routingPath, name))

    i = 0
    while i < io_retries:
        try:
            mergedPDF.write(filename)
            mergedPDF.close()
            break
        except Exception as e:
            print(f"Warning: Failed {i+1} of {io_retries} attempts "
                  f"to save the PDF '{filename}'.\n'{str(e)}'\n"
                  f"Trying again in 5 seconds....\n")
            time.sleep(5)   # wait 5 seconds
        i = i + 1
    if(i >= io_retries):
        filename = None
        print(
            f"ERROR: Failed {io_retries} attempts to save the PDF '{filename}'\nSkipping this PDF.")

    return filename

def create_Expedition_Routing_Report(path, fname, pages=1):
    exp = read_Expedition_Routing_Analysis(path, fname)

    report = None
    if len(exp):
        if pages == 1:
            report = create_one_page_report(exp, path, fname)
        elif pages == 3:
            report = create_three_page_report(exp, path, fname)
        else:
            print(f"\nInvalid report request ({pages}) - choices are 1 or 3.\n")

    if report:
       subprocess.Popen(report,shell=True) 

    return report

if __name__ == "__main__":
    print(f"\nStarting {__app__} {__version__}\n{__doc__}")
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    rootPath = os.path.dirname(scriptPath)
    routingPath = os.path.join(rootPath, "WeatherRouting_Analysis")
    
    fileName = "ATI_2024.csv"
    report = create_Expedition_Routing_Report(routingPath, fileName, pages=1)
    
    if report:
        print(f"PDF report at:\n{routingPath} {report}")
    
    print("\nDone!")