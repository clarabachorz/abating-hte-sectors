import pandas as pd
from src.plot import common
from src.calc import calc_costs


def load_IEA_data(file_paths):
    dataframes = []
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        df = df[df["category"] == "cat3_energy"]
        df = df[["subsector.y", "value_cat"]]
        dataframes.append(df)
    return dataframes

def get_LCOcontributions(df, LCO_comps):
    # Get the breakdown for the sectors (index 0) and reset the index to get the tech name
    detailed_LCO = calc_costs.breakdown_LCO_comps(LCO_comps)[0].set_index("tech")

    # use the regex to filter column with co2 and h2 contributions, and sum them
    LCO_h2_contribution = detailed_LCO.filter(regex="^(h2|.*_h2$)$").sum(axis=1)
    LCO_co2_contribution = detailed_LCO.filter(regex="^(co2|.*_co2$)$").sum(axis=1)

    # concatenating the dataframes to get the final dataframe
    costs_breakdown = pd.concat(
        [
            LCO_co2_contribution,
            LCO_h2_contribution,
            detailed_LCO["LCO"],
        ],
        axis=1,
        keys=["co2_cost", "h2_cost", "lco"],
    ).fillna(0)

    # calculate LCO without co2 and h2 costs
    costs_breakdown["lco_noh2co2"] = costs_breakdown["lco"] - (costs_breakdown["co2_cost"] + costs_breakdown["h2_cost"])

    # Merge with main df, df_macc
    merged_df = pd.merge(df, costs_breakdown, on="tech", how="left").drop("lco", axis=1)
    return merged_df

def get_LCOs(
    h2_cost=250, co2_cost=1200, co2_transport_storage=15, calc_LCO_comps=False
):
    # run the technoeconomic calculation
    if not calc_LCO_comps:
        df_data = calc_costs.calc_all_LCO(
            elec_co2em=0,
            h2_LCO=h2_cost,
            co2_LCO=co2_cost,
            co2ts_LCO=co2_transport_storage,
            co2tax_othercosts=0,
        )
    else:
        df_data, LCO_comps = calc_costs.calc_all_LCO_wbreakdown(
            elec_co2em=0,
            h2_LCO=h2_cost,
            co2_LCO=co2_cost,
            co2ts_LCO=co2_transport_storage,
            co2tax_othercosts=0,
        )

    # split tech name into type (ccs, ccu, ..) and actual sector
    df_data[["type", "sector"]] = df_data["tech"].str.split("_", expand=True)

    #all fuel rows in this df have sector = None. Separate them out
    df_fuels = df_data[df_data["sector"].isnull()]

    # groups the dataframe by sector, and calculates all FSCPs.
    df_macc = df_data.groupby("sector", as_index=False, group_keys=False).apply(
        lambda x: calc_costs.calc_FSCP(x)
    )

    #reassemble the dataframe to include the fuel rows
    df_macc = pd.concat([df_macc, df_fuels])

    if calc_LCO_comps:
        return (df_macc, LCO_comps)
    else:
        return df_macc

def plot_basicfigs():
    # Code starts here
        
    # calculate the df with default co2 and h2 LCOs
    df_macc, LCO_comps_default = get_LCOs(calc_LCO_comps=True) #h2_cost=250, co2_cost=1200, co2_transport_storage=15

    #then, calculate the LCO breakdown for the LCO_comps_default df
    # the function isolates the total contributions of h2 and co2 to each row of the df
    df_macc_wLCObreakdown = get_LCOcontributions(df_macc, LCO_comps_default)

    ### UNCOMMENT BELOW TO DO SOME PLOTTING (FIGURE 1)###

    # line below: full panel plotting, with no MAC, but instead LCO breakdown
    common.plot_large_panel(
        df_macc_wLCObreakdown,
    )

    #parameters for the bar plots
    h2_costs = [2 * 30, 4 * 30, 6 * 30, 8 * 30] #in EUR/MWh
    h2_costs = [100, 150, 200, 250] #in EUR/MWh
    co2_costs = [300, 300, 300, 300] #in EUR/tonne CO2
    co2_costs_fuels = [200, 400, 600, 800] #in EUR/tonne CO2
    co2_transport_storage_costs = 15 #in EUR/tonne CO2

    LCOs_df = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs,calc_LCO_comps=True) for h2, co2 in zip(h2_costs, co2_costs)]
    LCOs_fuels_df = [get_LCOs(h2_cost=h2, co2_cost=co2, co2_transport_storage=co2_transport_storage_costs, calc_LCO_comps=True) for h2, co2 in zip(h2_costs, co2_costs_fuels)]

    common.plot_barplotfscp(
        pd.concat([LCO_df[0] for LCO_df in LCOs_df]),
        pd.concat([calc_costs.breakdown_LCO_comps(LCO_df[1])[0] for LCO_df in LCOs_df]),
        sector="steel",
    )

    common.plot_barplotfuels(
        pd.concat([LCO_fuel_df[0] for LCO_fuel_df in LCOs_fuels_df]),
        pd.concat([calc_costs.breakdown_LCO_comps(LCO_fuel_df[1])[1] for LCO_fuel_df in LCOs_fuels_df]),
    )


    # df_macc.to_csv("./analysis/fig1_test.csv")
