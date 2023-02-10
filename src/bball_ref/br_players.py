import requests
import pandas as pd
import numpy as np
from utils.lookup import lookup
from utils.util import get_player_suffix
from bball_ref.br_utils import get_dataframe
from utils.constants import DESIRED_LOG_COLUMNS

def player_game_logs(_name, first_year, last_year, season_type="Playoffs"):
    name = lookup(_name, ask_matches=False)
    suffix = get_player_suffix(name)[:-5]
    print(suffix)
    curr = first_year
    dfs = []
    while curr <= last_year:
        if season_type == "Playoffs":
            url = f'https://www.basketball-reference.com{suffix}/gamelog-playoffs/'
        else: 
            url = f'https://www.basketball-reference.com/{suffix}/gamelog/{curr}'
        data_pd = get_dataframe(url, "pgl_basic_playoffs")
        data_pd = data_pd.drop(["G", "Series", "G#", "", "GS"], axis=1)
        data_pd = data_pd.replace("", 0)
        #data_pd = data_pd[[data_pd.columns[2], "Tm", "Opp", "MP", "FG", "FGA", "FG%", "3P", "3PA", "3P%", "FT", "FTA", "FT%", 
        #"ORB", "DRB", "TRB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "+/-"]].dropna(subset=['MP']).replace(np.nan, 0)
        data_pd[data_pd.columns[0]] = data_pd[data_pd.columns[0]].str[:4].astype("string")
        data_pd = (data_pd[(data_pd["AST"].str.contains("Inactive")==False) & (data_pd["AST"].str.contains("AST")==False) & 
            (data_pd["AST"].str.contains("Did Not Play")==False) & (data_pd["AST"].str.contains("Did Not Dress")==False)]
            .rename(columns={data_pd.columns[0]: "SEASON", "Tm": "TEAM_ABBR", "Opp": "MATCHUP", 
            "MP": "MIN"})
        )
        data_pd["minutes"] = data_pd["MIN"].str.extract(r'([1-9]*[0-9]):')
        data_pd["seconds"] = data_pd["MIN"].str.extract(r':([0-5][0-9])')
        data_pd["MIN"] = data_pd["minutes"].astype("int32") + (data_pd["seconds"].astype("int32") / 60)
        data_pd = data_pd.drop(columns=["minutes", "seconds"])
        convert_dict = {
        'SEASON': 'int32', 'TEAM_ABBR': 'string', 'MATCHUP': 'string', 'MIN': 'float64','FG': 'int32', 'FGA': 'int32', 'FG%': 'float64', 
        '3P': 'int32', '3PA': 'int32', '3P%': 'float64', 'FT': 'int32', 'FTA': 'int32', 'FT%': 'float64', 'ORB': 'int32', 
        'DRB': 'int32', 'TRB': 'int32', 'AST' : 'int32', 'STL': 'int32', 'BLK': 'int32', 'TOV' : 'int32', 'PF': 'int32', 
        'PTS': 'int32', 'GmSc': 'float64', '+/-' : 'int32'
        }
        keep = {key: convert_dict[key] for key in data_pd.columns.values}
        data_pd = data_pd.astype(keep)
        if season_type == "Regular Season":
            data_pd["SEASON"] = curr
        data_pd = data_pd.query("SEASON >= @first_year and SEASON <= @last_year")
        dfs.append(data_pd)
        curr += 1
        if season_type == "Playoffs":
            break
    result = pd.concat(dfs)
    result = result.reset_index(drop=True)
    result.index += 1
    for i, col in enumerate(DESIRED_LOG_COLUMNS):
        if col not in result.columns.values:
            result[col] = np.nan
            left = [x for x in range(i)]
            right = [x for x in range(i, len(result.columns) - 1)]
            result = result.iloc[:, left + [len(result.columns) - 1] + right]
    return result