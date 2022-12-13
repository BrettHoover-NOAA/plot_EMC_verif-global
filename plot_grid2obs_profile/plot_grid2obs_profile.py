##########################################################################
# The list of cycles to extract data from, which will be aggregated for
# profiles and plotted individually for traces, is defined by:
#    1) Use of get_datelist() to automatically generate a list of cycles
#       at regular steps between a beginning and ending date, e.g.:
#
#       cycles=get_datelist(dt_beg,dt_end,hrs)
#
#    2) During search for gsistat files for each cycle, if a gsistat file
#       is missing, the date is removed from cycles
#    3) During collection of statistics, if there are no valid statistics
#       for a given cycle, NaN values are returned and plotted
#
# Figures are saved to pname and tname, respectively
#
# tskip defines the number of time-periods in the trace that are skipped
# when adding tick-labels. Tick-labels are dates of the form (e.g.)
# 'Aug01-00z', so for long timeseries traces the labels will be written
# over each other unless some of them are skipped. I usually use some
# multiple of 4, so that the tick-labels always correspond to the same
# analysis-period.
##########################################################################

def parse_yaml(yaml_file):
    import yaml
    # YAML entries come in two types:
    # key='figure' : provides figure filename for profile figure
    #                (filenm), list of pressure levels (pre_levs),
    #                variable-type (var), ob-type (ob), vxmask
    #                region (region), and forecast hour (fhr, 
    #                'HH[H...]0000' format)
    # any other key: provides dictionaries for a dataset to
    #                be plotted that include the experiment name
    #                (expr), name for figure legend (figname),
    #                and directory where statistics files are
    #                available (statdir)
    with open(yaml_file, 'r') as stream:
        try:
            parsed_yaml = yaml.safe_load(stream)
        except yaml.YAMLError as YAMLError:
            parsed_yaml = None
            print(f'YAMLError: {YAMLError}')
        if parsed_yaml is not None:
            # Extract 'figure' data
            try:
                figName = parsed_yaml['figure']['filenm']
                preList = parsed_yaml['figure']['pre_levs']
                var = parsed_yaml['figure']['var']
                ob = parsed_yaml['figure']['ob']
                vxMask = parsed_yaml['figure']['region']
                fcstHr = parsed_yaml['figure']['fhr']
            except KeyError as MissingFiguresError:
                figName = None
                preList = None
                var = None
                ob = None
                vxMask = None
                fcstHr = None
                print(f'MissingFiguresError: {MissingFiguresError}')
            # Extract all other keys as filtering dictionaries, store
            # in setdict list
            setdict = []
            fdicts = {x: parsed_yaml[x] for x in parsed_yaml
                      if x not in {'figure'}}
            for fd in fdicts.keys():
                try:
                    fdict = fdicts[fd]
                except KeyError as FilterKeyError:
                    print(f'FilterKeyError: {FilterKeyError}')
                    continue
                setdict.append(fdict)
    return figName, preList, var, ob, vxMask, fcstHr, setdict

def extract_val_from_statfile(statFile,fhr):
    # The EMC_verif-global stats files have 2 columns:
    # fhr    val
    # --     --
    # --     --
    # --     --
    # --     --
    # ...
    # Typically we see there are 2 entries for fhr, but the corresponding val is
    # the same (not sure why). This function searches the dataframe of statFile
    # and pulls all values corresponding to fhr. If there is only one unique value
    # it is returned, otherwise NaN is returned.
    #
    # INPUTS:
    #    statFile: full path to statistics file
    #    fhr: forecast hour (string)
    #
    # OUTPUTS:
    #    stat: retrieved statistic, or np.nan if no statistic exists
    #
    # DEPENDENCIES:
    #    numpy, pandas
    #
    import numpy as np
    import pandas as pd
    # Define dataframe from space-delimited statfile
    df = pd.read_csv(statFile,header=None,delimiter=' ')
    # Assign header names for columns
    df.columns = ['fhr','val']
    # Extract frame values corresponding to the value of fhr (fhr: string-to-integer)
    x = df.loc[df['fhr'] == int(fhr),'val'].values
    # Test for a single unique value for x
    if np.size(np.unique(x)) == 1:
        x = x[0]
    else:
        x = np.nan
    # Return x
    return x

def retrieve_statfile_list(statsDir,statType,expr,pre,var,ob,vxMask,isCI=False):
    # Searches statsDir for a statistics file matching input statType, expr, pre, 
    # var, ob, vxMask, and whether the statistic is a CI or not (isCI). Returns 
    # None if no unique file is found.
    #
    # INPUTS:
    #    statsDir: full path to directory containing statistics files
    #    statType: type of statistic ('rmse','bias')
    #    expr: experiment name
    #    pre: pressure level (string)
    #    var: variable type (e.g. 'UGRD_VGRD')
    #    ob: observation type (e.g. 'ADPUPA')
    #    vxMask: regional mask type (e.g. 'SH')
    #    isCI: boolean for if statistic is a confidence interval
    #
    # OUTPUTS:
    #    full path to statistics file, or None if no unique file was found
    #
    # DEPENDENCIES:
    #    glob
    from glob import glob
    # Generate search string with wild-cards in selected places
    srchStr = (statsDir + '*/grid2obs/*/data/' + #...................... all potential paths to files
               statType + '_' + expr + '_' + ob + #..................... <STAT>_<EXPR>_<OB> sequence
               '_valid*to*_valid*to*Z_init*to*Z_fcst_lead_avgs_' + #.... all potential validation date/cycle, init date/cycle seq
               'fcst' + var + 'P' + pre + #............................. forecast <VAR>P<PRE> seq
               '_obs' + var + 'P' + pre + #............................. observation <VAR>P<PRE> seq
               '_vxmask' + vxMask) #.................................... <VXMASK> seq
    # Perform search to generate list
    if isCI:
        srchStr = srchStr + '_CI_EMC.txt'
        statfileList = glob(srchStr)
    else:
        srchStr = srchStr + '.txt'
        statfileList = glob(srchStr)
    # Return list contents if a single entry exists, otherwise return None
    if len(statfileList) == 0:
        return None
    elif len(statfileList) > 1:
        return None
    else:
        return statfileList[0]

def collect_statistics(statsDirs,statType,exprNames,preList,fhr,var,ob,vxMask):
    # For each experiment in exprNames:
    #    Find the appropriate (fhr,ob,vxMask,statType) file and any corresponding CI file for each level in preList
    #    Extract the statistic and any CI if it exists
    #    Store statistic and CI in array for each level in preList (or np.nan if no stat/CI exists for level)
    #
    # INPUTS:
    #    statsDirs: directory path to grid2obs statistics *.txt files from EMC_verify-global fore each experiment
    #    statType: type of statistic to collect ('rmse','bias')
    #    exprNames: list of experiment names to search for
    #    fhr: forecast hour (string)
    #    var: variable type (e.g. 'UGRD_VGRD')
    #    ob: observation type (e.g. 'ADPUPA')
    #    vxMask: regional mask type (e.g. 'NH', 'SH', 'TROP')
    #
    # OUTPUTS:
    #    statList: list of (nLev,2) arrays containing statistic and CI at each nLev levels in preList
    #
    # DEPENDENCIES:
    #    numpy, pandas, glob
    #
    import numpy as np
    import pandas as pd
    from glob import glob
    # Define number of experiments and pressure levels
    numExpr = len(exprNames)
    numLevs = len(preList)
    # Initialize empty statList
    statList = []
    # Loop through exprNames
    for i in range(len(exprNames)):
        expr = exprNames[i]
        statsDir = statsDirs[i]
        # Initialize np.nan array of size (numLevs,2) for experiment statistics and CI
        statArray = np.nan*np.ones((numLevs,2))
        # Loop through preList
        for k in range(len(preList)):
            pre = preList[k]
            # Retrieve statistics file for expr, pre, ob, vxMask
            statFile = retrieve_statfile_list(statsDir,statType,expr,pre,var,ob,vxMask,isCI=False)
            # IF file exists, extract statistic
            stat = np.nan if statFile == None else extract_val_from_statfile(statFile,fhr)
            # Retrieve CI file for expr, pre, ob, vxMask
            statFile = retrieve_statfile_list(statsDir,statType,expr,pre,var,ob,vxMask,isCI=True)
            # IF file exists, extract CI
            ci = None if statFile == None else extract_val_from_statfile(statFile,fhr)
            # Assign stat and ci to array
            statArray[k,0] = stat
            statArray[k,1] = ci
        # Append statArray to statList
        statList.append(statArray)
    # Return statList
    return statList

def plot_stat_profiles(rmsList, biasList, nameList, plevList,
                       colMap=['tab10', 10]):
    ######################################################################
    # Generates profiles of rms and bias for each set, with error-bars
    #
    # INPUTS
    #    rmsList: list of numpy arrays (nlev,2) of rms and CI values by 
    #             pressure level for each set
    #    biasList: list of numpy arrays (nlev,) of bias and CI values by
    #              pressure level for each set
    #    nameList: list of names for each set (for figure legend)
    #    plevList: list of profile pressure levels (str or float)
    #    colMap: 2-element list containing colormap and colormap-range for
    #            panels (default: ['tab10',10]))
    # OUTPUTS
    #    plotFig: plot figure, as plt.fig()
    #
    # DEPENDENCIES
    # numpy
    # matplotlib.rc
    # matplotlib.pyplot
    # matplotlib.cm
    ######################################################################
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    #
    # Set font size and type
    #
    font = {'family': 'DejaVu Sans',
            'weight': 'bold',
            'size': 22}

    matplotlib.rc('font', **font)
    #
    # Identify number of profile sets (should be indentical for rmsList,
    # biasList)
    #
    n_profiles = len(rmsList)
    #
    # Define colormap: The default settings are to select a range of 10 on
    # 'tab10', so that 10 pairs of rms/bias profiles can be produced for
    # the left panel that correspond to 10 ob-counts on the right panel.
    # The user can select a different colormap and range with colMapLeft
    # and colMapRight options.
    # If you want to sample the entire colorbar, set the range to the
    # number of datasets plotted.
    #
    # scalarMapList is used to select colors for each profile/bar
    scalarMap = cm.ScalarMappable(cmap=colMap[0])
    scalarMapList = scalarMap.to_rgba(range(colMap[1]))
    #
    # Generate figure
    plt.figure(figsize=(9, 18))
    # Define offset values (needed to define y-axis limits on both plots,
    # for consistency)
    y_offset = 8.0*(np.arange(n_profiles)-np.floor(n_profiles/2))
    # For each set, plot rms and bias: plot lines and circular markers
    legend_list = []
    # Define levs from plevList by asserting as float32 numpy array
    levs = np.asarray(plevList,dtype=np.float32)
    n_levs = np.size(levs)
    for i in range(n_profiles):
        rms = rmsList[i]
        bias = biasList[i]
        # Define y-axis limits
        y_min = min(levs)+min(y_offset)-8.0
        y_max = max(levs)+max(y_offset)+8.0
        # rms profile
        prof_color = list(scalarMapList[i][0:3])
        if np.any(~np.isnan(rms[:,0])):
            legend_list.append(nameList[i]+' rms')
            plt.plot(rms[:,0].squeeze(), levs, color=prof_color, linewidth=3)
            plt.plot(rms[:,0].squeeze(), levs, 'o', color=prof_color, markersize=8,
                     label='_nolegend_')
        if np.any(~np.isnan(rms[:,1])):
            plt.errorbar(x=rms[:,0].squeeze(),y=levs,xerr=rms[:,1].squeeze(),
                         ecolor=prof_color,elinewidth=10,capsize=10,capthick=2,
                         alpha=0.33,label='_nolegend_')
        # bias profile
        prof_color = list(scalarMapList[i][0:3])
        if np.any(~np.isnan(bias[:,0])):
            legend_list.append(nameList[i]+' bias')
            plt.plot(bias[:,0].squeeze(), levs, color=prof_color, linewidth=3,
                     linestyle='dashdot')
            plt.plot(bias[:,0].squeeze(), levs, 'o', color=prof_color, markersize=8,
                     label='_nolegend_')
        if np.any(~np.isnan(bias[:,1])):
            plt.errorbar(x=bias[:,0].squeeze(),y=levs,xerr=bias[:,1].squeeze(),
                         ecolor=prof_color,elinewidth=10,capsize=10,capthick=2,
                         alpha=0.33,label='_nolegend_')
    # Zero-line
    plt.plot(np.zeros((n_levs, )), levs, color='k', linewidth=1,
             linestyle='dashed', label='_nolegend_')
    # Set y-limits to entire range
    plt.ylim((y_min, y_max))
    plt.yticks(levs)
    # Reverse y-axis, if levs is in descending-order (often the case with
    # pressure coordinate data)
    if (levs[1] < levs[0]):
        plt.gca().invert_yaxis()
    # Set legend
    plt.legend(legend_list, frameon=False, fontsize=10)
    # Set x-label
    plt.xlabel('RMS or Bias')
    # Turn off interactive-mode to suppress plotting figure
    plt.ioff()
    # Return
    return plt.gcf()

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    figName, preList, var, ob, vxMask, fcstHr, setdict = parse_yaml('grid2obs.yaml')
    statsDirs=[]
    exprNames=[]
    figNames=[]
    for sd in setdict:
        statsDirs.append(sd['statdir'])
        exprNames.append(sd['expr'])
        figNames.append(sd['figname'])
    rmse=collect_statistics(statsDirs,'rmse',exprNames,preList,fcstHr,var,ob,vxMask)
    bias=collect_statistics(statsDirs,'bias',exprNames,preList,fcstHr,var,ob,vxMask)
    fig=plot_stat_profiles(rmse, bias, figNames, preList)
    fig.axes[0].set_title('Fit2Obs '+ob+' '+vxMask+' '+str(int(float(fcstHr)/10000.))+' hrs')
    fig.savefig(figName,bbox_inches='tight',facecolor='w')

