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
    
    # 1. Load Referendum Data
    # - sep=';': The file uses semi-colons as separators.
    # - dtype={'Department code': str}: Read codes as strings to handle '2A', '2B' etc.
    referendum = pd.read_csv(
        "data/referendum.csv", 
        sep=';', 
        dtype={'Department code': str}
    )
    
    # Standardization: Pad department codes with 0 (e.g., turn '1' into '01')
    # This is crucial for merging with the departments dataframe later.
    referendum['Department code'] = referendum['Department code'].str.zfill(2)
    
    # CRITICAL FIX: Do not rename referendum columns here.
    # The subsequent functions rely on the original names like 'Registered', 'Choice A', etc.

    # 2. Load Regions Data
    # - dtype={'code': str}: Preserves leading zeros in region codes (e.g. '01')
    regions = pd.read_csv(
        "data/regions.csv", 
        dtype={'code': str}
    )
    # FIX: Column renaming for regions removed from here.

    # 3. Load Departments Data
    # - dtype=str: Ensure both department and region codes are treated as strings
    departments = pd.read_csv(
        "data/departments.csv", 
        dtype={'code': str, 'region_code': str}
    )
    # FIX: Column renaming for departments removed from here.

    return referendum, regions, departments

def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    # FIX: Rename columns here where it is needed for merging and final structure.
    # 1. Rename departments columns
    departments = departments.rename(columns={
        'code': 'code_dep', 
        'region_code': 'code_reg', 
        'name': 'nom_dep'
    })
    
    # 2. Rename regions columns
    regions = regions.rename(columns={
        'code': 'code_reg', 
        'name': 'nom_reg'
    })

    # 3. Perform the merge
    df_merged = departments.merge(
        regions, on='code_reg', how='left' # Removed suffixes as columns are now explicitly named
    )
    
    # 4. Final renaming and column selection
    final_df = df_merged.rename(
        columns={'nom_dep': 'name_dep', 'nom_reg': 'name_reg'}
    )[['code_reg', 'name_reg', 'code_dep', 'name_dep']]

    return final_df


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.
    """
    # Use 'Department code' from the un-renamed referendum DataFrame
    referendum_filtered = referendum[
        ~referendum['Department code'].str.contains('Z')
    ].copy()
    
    # Merge on 'Department code' (left) and 'code_dep' (right)
    df_merged = referendum_filtered.merge(
        regions_and_departments, left_on='Department code', right_on='code_dep', how='left'
    )
    df_merged = df_merged.dropna(subset=['code_reg'])
    
    return df_merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    # Use the original English column names for summation
    cols_to_sum = [
        'Registered', 
        'Abstentions',
        'Null', 
        'Choice A', 
        'Choice B'
    ]
    
    # Group by region code and name, and sum the required columns
    df_results = referendum_and_areas.groupby(
        ['code_reg', 'name_reg']
    )[cols_to_sum].sum().reset_index()

    # Set 'code_reg' as index as requested
    df_results.set_index('code_reg', inplace=True)
    
    # Reorder columns as requested
    final_cols = ['name_reg'] + cols_to_sum
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
    geo_regions = gpd.read_file("data/regions.geojson", dtype={'code': str})

    # 2. Compute the ratio of 'Choice A' over all expressed ballots
    referendum_result_by_regions['Expressed'] = (
        referendum_result_by_regions['Choice A'] + referendum_result_by_regions['Choice B']
    )
    referendum_result_by_regions['ratio'] = (
        referendum_result_by_regions['Choice A'] / referendum_result_by_regions['Expressed']
    )

    # 3. Merge results with GeoDataFrame
    # Include 'name_reg' in the merge to satisfy test_plot_referendum_map assertion
    geo_merged = geo_regions.merge(
        referendum_result_by_regions[['name_reg', 'ratio']],
        left_on='code',
        right_index=True,
        how='left'
    )
    
    # 4. Plot the map
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    geo_merged.plot(
        column='ratio',
        ax=ax,
        legend=True,
        cmap='RdYlGn', 
        legend_kwds={'label': "Ratio of 'Choice A' over Expressed Ballots"},
        edgecolor='black'
    )
    
    ax.set_title("Referendum Results by Region (Ratio of 'Choice A')")
    ax.set_axis_off()

    return geo_merged


if __name__ == "__main__":
    # NOTE: This block assumes the existence of the 'data' directory
    
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
        # In a real environment, you would save the figure or display it.
        # plt.savefig("referendum_map.png")
        print("\nMap plotted successfully.")
        
    except FileNotFoundError as e:
        print(f"\nError: Data file not found. Please ensure the 'data' directory exists and contains all required files (referendum.csv, regions.csv, departments.csv, regions.geojson).")
        print(f"Missing file path: {e}")