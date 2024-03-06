import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.colors
import matplotlib.patches as patches
from  matplotlib.cm import ScalarMappable

from pathlib import Path
from src.plot import common

def plot_heatmap(data, cmap, ax, cbar, vmin=0, vmax=1, rasterized=True):
    return sns.heatmap(data, cmap=cmap, cbar = cbar, vmin=vmin, vmax=vmax, ax=ax, rasterized=rasterized)

def add_rectangle(ax, xcoord, ycoord, w, h):
    ax.add_patch(
        patches.Rectangle(
            (xcoord, ycoord),
            w,
            h,
            edgecolor='darkgrey',
            fill=True,
            fc=(0.7, 0.7, 0.7, 0.15),
            lw=1,
        )
    )

def add_annotation(ax, text, xcoord, ycoord):
    ax.annotate(text, xy=(xcoord, ycoord), fontsize=8, ha='center', va='center_baseline', color="dimgrey")

def return_custom_cmap(mapping_dict):
    color_dict = common.color_dict_tech
    dict_cmap = {value: color_dict[key] for key, value in mapping_dict.items()}
    custom_cmap = matplotlib.colors.ListedColormap([dict_cmap[key] for key in sorted(mapping_dict.values())])
    return custom_cmap

def return_transparent_cmap():
    #second cmap: transparency cmap
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["white","white","white"])
    # Get the colormap colors
    transparent_cmap = cmap(np.arange(cmap.N))
    # linear transparent colormap:
    transparent_cmap[:,-1] =np.linspace(0, 1, cmap.N)[::-1]
    # Create new colormap
    transparent_cmap = matplotlib.colors.ListedColormap(transparent_cmap)
    return transparent_cmap

def plot_hm_figS3(path_to_data, rowvar_name, row_titles, x_var = "co2_LCO", y_var = "h2_LCO"):
    # import plotting parameters from plot_fun
    #color_dict_tech = plot_fun.color_dict_tech
    rename_sectors = common.rename_sectors

    #associate type of technology to discrete value
    dict_type_ID = {"h2": 0, "comp":0.33, "ccu":0.66, "ccs":1}

    #make custom heatmaps based on the technologies available
    defaultcmap = return_custom_cmap(dict_type_ID)
    transparent_cmap = return_transparent_cmap()

    # define default ticks for the colorbar
    defaultcmap_ticks = ['H2/NH3','DAC \ncompen-\nsation', 'CCU', 'CCS']
    #load data calculated by calc_data_figS3
    df_fig = pd.read_csv(path_to_data)
    #remove the first two columns, which are just old indice
    df_fig = df_fig.iloc[:,2:]
    #add values to identify the categories in the heat map, using the appropriate dict
    df_fig["type_ID"] = df_fig["type"].map(dict_type_ID)

    ### MAKE fighm ###
    # define variables considered in each axis (var 1 = y axis, var 2 = x axis, var 3 = row variable)

    col_vars = ["greenfield", "brownfield"]
    row_vars = ["", "_comp"]
    sector_var = "steel"

    scenario_name = ["Steel sector:\ngreenfield case", "Steel sector:\nbrownfield case"]

    rows = len(row_vars)
    cols = len(col_vars)

    # define figure size
    fig, axs = plt.subplots(nrows=len(row_vars), ncols=len(col_vars), figsize=(4*len(col_vars),4*len(row_vars)), constrained_layout=True)

    for row in range(len(row_vars)):
        #select the appropriate row var
        row_var = row_vars[row]
        #filter data accordingly
        sub_df = df_fig.reset_index(drop=True)

        #add row title, on the left hand side. As defined by "scenario name" variable
        for col in range(len(col_vars)):
            ax = axs[row, col]
            pad = 5
            if col == 0:
                ax.annotate(f'{row_titles[row]}',
                            xy=(0, 0.5), xytext=(-ax.yaxis.labelpad - pad, 0),
                            xycoords=ax.yaxis.label, textcoords='offset points',
                            size='large', ha='center', va='center', rotation = 90)

            #get the correct column variable
            col_var = col_vars[col] + row_var

            #again, filter the data to find the appropriate portion
            sub_sub_df = sub_df.loc[(sub_df["sector"] == sector_var) & (sub_df[rowvar_name] == col_var)].reset_index(drop=True)
            
            # create the dfs that will be used for the heat map
            # one with the sectoral color, one for the transparent layer, one for the fscp contour
            sns_df = sub_sub_df.pivot(index = y_var, columns = x_var, values="type_ID")
            sns_diff_df = sub_sub_df.pivot(index = y_var,columns = x_var, values = "delta_fscp")
            contour_df = sub_sub_df.pivot(index = y_var, columns = x_var, values = "fscp")

            #plot the sectoral color heat map
            heatmap_cmap = defaultcmap
            heatmap = plot_heatmap(sns_df, heatmap_cmap, ax, (col == cols-1)&(row >= 0), rasterized=True)


            # Colorbar setting: currently, first and second row consider all options (including full DACCS)
            # third row does not, and the colorbar used changes. Full climate neutrality is also required,
            # so all options are complemented with DACCS
            colorbar = ax.collections[0].colorbar
            if colorbar is not None:
                if row > 0:
                    ticklabels = ['H2/NH3\n+ DACCS','DACCS', 'CCU\n+ DACCS', 'CCS\n+ DACCS']
                else:
                    ticklabels = defaultcmap_ticks

                # Calculate tick positions
                step = 1.0 / (len(ticklabels))
                ticks = np.arange(0+ step/2, 1 + step/2, step)

                colorbar.set_ticks(ticks)
                colorbar.set_ticklabels(ticklabels)

            # add the additional transparent layer to show the fscp difference between the first and second minima
            heatmap_diff = plot_heatmap(sns_diff_df, transparent_cmap, ax, cbar = False, vmin=0, vmax=100)
            # and the contour line
            contour_values = {"steel": [0, 50, 100, 150, 200,250], "cement": [0,50, 100, 150, 200, 250]}.get(col_var, [0, 400, 800, 1200, 1600])
            contour = ax.contour(np.arange(.5, contour_df.shape[1]), np.arange(.5, contour_df.shape[0]), contour_df, contour_values, colors='dimgrey', alpha=0.8, linewidths=0.8)

            #change contour label params
            ax.clabel(contour, inline=True, fontsize=8)

            #add the rectangles to show the 2022 and 2050 regions
            # our assumptions for 2050: CO2 cost between 100 and 700 EUR/tCO2, h2 cost between 60 and 160 EUR/MWh
            # our assumptions for 2022: CO2 cost between 900 and 1200 EUR/tCO2, h2 cost between 120 and 240 EUR/MWh
            co2_2050_xcoord = (np.abs(sns_df.columns.to_numpy() - 100)).argmin()
            h2_2050_ycoord = (np.abs(sns_df.index.to_numpy() - 60)).argmin()
            co2_2050_w = (np.abs(sns_df.columns.to_numpy() - 700)).argmin() - co2_2050_xcoord
            h2_2050_h = (np.abs(sns_df.index.to_numpy() - 160)).argmin() - h2_2050_ycoord

            co2_2022_xcoord = (np.abs(sns_df.columns.to_numpy() - 900)).argmin()
            h2_2022_ycoord = (np.abs(sns_df.index.to_numpy() - 120)).argmin()
            co2_2022_w = (np.abs(sns_df.columns.to_numpy() - 1200)).argmin() - co2_2022_xcoord
            h2_2022_h = (np.abs(sns_df.index.to_numpy() - 240)).argmin() - h2_2022_ycoord

            # Draw the rectangle patches
            add_rectangle(ax, co2_2050_xcoord, h2_2050_ycoord, co2_2050_w, h2_2050_h)
            add_rectangle(ax, co2_2022_xcoord, h2_2022_ycoord, co2_2022_w+1, h2_2022_h+1)

            # Add annotations
            add_annotation(ax, ">2050", co2_2050_xcoord + co2_2050_w/2, h2_2050_ycoord)
            add_annotation(ax, "2022", co2_2022_xcoord+co2_2022_w/2, h2_2022_ycoord)

            # change x and y parameter ticks manually
            ax.locator_params(axis='x', nbins=11)

            # Get unique y_var values and sort them
            y_var_unique = np.sort(sub_sub_df[y_var].unique())
            no_yvars = len(y_var_unique)

            # Set y-ticks at equally spaced intervals
            y_ticks = np.linspace(0, no_yvars-1, 7)
            ax.set_yticks(y_ticks)

            # Set y-tick labels at corresponding y_var values
            y_ticklabels = np.round(np.linspace(y_var_unique[0], y_var_unique[-1], len(y_ticks)), 0).astype(int)
            ax.set_yticklabels(y_ticklabels)

            ax.invert_yaxis()

            if y_var == "h2_LCO":
                # Add a secondary axis for H2, to show the cost in EUR/kg
                ax2 = ax.twinx()
                h2tck = y_var_unique / 30

                ax2.set_yticks(ax.get_yticks())
                ax2_yticklabels = np.round(np.linspace(min(h2tck), max(h2tck), len(ax.get_yticks())),1)
                ax2.set_yticklabels(ax2_yticklabels)

            
            # Additional aesthetics: labels, titles, etc.
            if col == 0:
                ax.set_ylabel('Green H2 cost (EUR/MWh)')
                ax2.set_yticklabels([])
            elif col == cols-1:
                ax2.set_ylabel("Green H2 cost (EUR/kg)\n")
                ax.set_ylabel("")
                ax.set_yticklabels([])
            else:
                ax.set_ylabel("")
                ax.set_yticklabels([])
                ax2.set_yticklabels([])
            
            if row == 0 :
                ax.set_title(scenario_name[col])
                ax.set_xlabel("")
                ax.set_xticklabels([])
            elif row == rows-1:
                ax.set_xlabel('CO2 from DAC cost (EUR/tCO2)')
            else: 
                ax.set_xlabel("")
                ax.set_xticklabels([])

    fig.get_layout_engine().set(w_pad=4 / 72, h_pad=4 / 72, hspace=0, wspace=0, rect=[0, 0, .9, 1])

def plot_supretrofit():
    row_titles = ["Standard case", "Climate neutrality case"]
    plot_hm_figS3(#'code_figS3/figS3_rawdata.csv',
                path_to_data = str(Path(__file__).parent.parent / '../data/supretrofit_rawdata.csv'),
                rowvar_name= "scenario",
                row_titles=row_titles)
    plt.show()

