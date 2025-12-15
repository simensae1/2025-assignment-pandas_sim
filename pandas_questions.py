"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.DataFrame({})
    regions = pd.DataFrame({})
    departments = pd.DataFrame({})

    return referendum, regions, departments

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import os

# Define the directory where data files are expected
DATA_DIR = 'data'


def load_data():
    """Load data from the CSV files referendum/regions/departments."""
    
    # Construct full file paths
    referendum_path = os.path.join(DATA_DIR, 'referendum.csv')
    regions_path = os.path.join(DATA_DIR, 'regions.csv')
    departments_path = os.path.join(DATA_DIR, 'departments.csv')
    
    # Load dataframes
    referendum = pd.read_csv(referendum_path, sep=';', dtype={'code_dep': str})
    regions = pd.read_csv(regions_path, sep=';', dtype={'code_reg': str})
    departments = pd.read_csv(departments_path, sep=';', dtype={'code_dep': str, 'code_reg': str})

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    df_merged = departments.merge(
        regions, on='code_reg', how='left', suffixes=('_dep', '_reg')
    )
    final_df = df_merged.rename(
        columns={'nom_dep': 'name_dep', 'nom_reg': 'name_reg'}
    )[['code_reg', 'name_reg', 'code_dep', 'name_dep']]

    return final_df


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """
    referendum_filtered = referendum[
        ~referendum['code_dep'].str.contains('Z')
    ].copy()
    df_merged = referendum_filtered.merge(
        regions_and_departments, on='code_dep', how='left'
    )
    df_merged = df_merged.dropna(subset=['code_reg'])

    return df_merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    cols_to_sum = [
        'Inscrits',  # Registered
        'Abstentions',
        'Blancs et Nuls',  # Null
        'OUI',  # Choice A
        'NON'  # Choice B
    ]
    
    # Group by region code and name, and sum the required columns
    df_results = referendum_and_areas.groupby(
        ['code_reg', 'name_reg']
    )[cols_to_sum].sum().reset_index()

    # Rename columns to match the requirement
    df_results.rename(
        columns={
            'Inscrits': 'Registered',
            'Blancs et Nuls': 'Null',
            'OUI': 'Choice A',
            'NON': 'Choice B',
        },
        inplace=True
    )
    
    # Set 'code_reg' as index as requested
    df_results.set_index('code_reg', inplace=True)
    
    # Reorder columns as requested
    final_cols = ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    return df_results[final_cols]


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """
    # 1. Load GeoJSON data
    geojson_path = os.path.join(DATA_DIR, 'regions.geojson')
    geo_regions = gpd.read_file(geojson_path, dtype={'code': str})

    # 2. Compute the ratio of 'Choice A' over all expressed ballots
    # Expressed Ballots = Registered - Abstentions - Null (or Choice A + Choice B)
    referendum_result_by_regions['Expressed'] = (
        referendum_result_by_regions['Choice A'] + referendum_result_by_regions['Choice B']
    )
    referendum_result_by_regions['ratio'] = (
        referendum_result_by_regions['Choice A'] / referendum_result_by_regions['Expressed']
    )

    # 3. Merge results with GeoDataFrame
    # The GeoDataFrame uses 'code' for the region code, and the results table uses 'code_reg' (index)
    geo_merged = geo_regions.merge(
        referendum_result_by_regions[['ratio']],
        left_on='code',
        right_index=True,
        how='left'
    )
    
    # 4. Plot the map
    # Create the map (figsize chosen for better display)
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # Plotting the ratio (rate of 'Choice A')
    geo_merged.plot(
        column='ratio',
        ax=ax,
        legend=True,
        cmap='RdYlGn',  # Red-Yellow-Green colormap for political/binary results
        legend_kwds={'label': "Ratio of 'Choice A' over Expressed Ballots"},
        edgecolor='black'
    )
    
    ax.set_title("Referendum Results by Region (Ratio of 'Choice A')")
    ax.set_axis_off()  # Remove axis ticks and labels

    return geo_merged


if __name__ == "__main__":
    # NOTE: This block assumes the existence of the 'data' directory
    # containing: referendum.csv, regions.csv, departments.csv, regions.geojson
    
    try:
        referendum, df_reg, df_dep = load_data()
        print("Data loaded successfully.")

        regions_and_departments = merge_regions_and_departments(
            df_reg, df_dep
        )
        print("Regions and departments merged.")

        referendum_and_areas = merge_referendum_and_areas(
            referendum, regions_and_departments
        )
        print(f"Referendum and areas merged. {len(referendum_and_areas)} rows remain after filtering.")

        referendum_results = compute_referendum_result_by_regions(
            referendum_and_areas
        )
        print("\n--- Aggregated Results by Region (Head) ---")
        print(referendum_results.head())

        gpd_result = plot_referendum_map(referendum_results)
        print("\nMap plotted successfully.")
        
        # Display the map
        plt.show()

    except FileNotFoundError as e:
        print(f"\nError: Data file not found. Please ensure the 'data' directory exists and contains all required files (referendum.csv, regions.csv, departments.csv, regions.geojson).")
        print(f"Missing file path: {e}")