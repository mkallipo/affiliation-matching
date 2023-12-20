# script.py
import pandas as pd
import re
##import unicodedata
import html


from collections import defaultdict

import pickle

##import Levenshtein
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

##import functions
from helper_functions import *
from main_functions import *


with open('dix_acad.pkl', 'rb') as f:
    dix_acad = pickle.load(f)

with open('dix_mult.pkl', 'rb') as f:
    dix_mult = pickle.load(f)

with open('dix_city.pkl', 'rb') as f:
    dix_city = pickle.load(f)
    
with open('dix_country.pkl', 'rb') as f:
    dix_country = pickle.load(f)
    
    

def find_ror(string):
    df = pd.DataFrame()
 
    df['Unique affiliations'] = [[string]]
    academia = create_df_algorithm(df)
    
    result = Aff_Ids(len(academia), academia,dix_acad, dix_mult, dix_city, dix_country, .65,.65)
    
    if len(result)>0:
         
        
        dict_aff_open = {x: y for x, y in zip(result['Original affiliations'], result['Matched organizations'])}
        dict_aff_id = {x: y for x, y in zip(result['Original affiliations'], result['ROR'])}
    
        dict_aff_score = {}
        for i in range(len(result)):
            if type(result['Similarity score'].iloc[i]) == list:
                dict_aff_score[result['Original affiliations'].iloc[i]] = result['Similarity score'].iloc[i]
            else:
                dict_aff_score[result['Original affiliations'].iloc[i]] = [result['Similarity score'].iloc[i]]
                

        pids = []
        for i in range(len(df)):
            pidsi = []
            for aff in df['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_id.keys()):
                    pidsi = pidsi + dict_aff_id[aff]
            # elif 'unmatched organization(s)' not in pidsi:
            #     pidsi = pidsi + ['unmatched organization(s)']
            pids.append(pidsi)
                    
                    
        names = []
        for i in range(len(df)):
            namesi = []
            for aff in df['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_open.keys()):
                    try:
                        namesi = namesi + dict_aff_open[aff]
                    except TypeError:
                        namesi = namesi + [dict_aff_open[aff]]
                    
            names.append(namesi)
            
        scores = []
        for i in range(len(df)):
            scoresi = []
            for aff in df['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_score.keys()):
                    scoresi = scoresi +  dict_aff_score[aff]
                    
            scores.append(scoresi)
            
            
        df['Matched organizations'] = names
        df['ROR'] = pids
        df['Scores'] = scores


       
        def update_Z(row):
            if len(row['ROR']) == 0 or len(row['Scores']) == 0:
                return []
            
            new_Z = []
            for ror, score in zip(row['ROR'], row['Scores']):
                entry = {'ROR_ID': ror, 'Score': score}
                new_Z.append(entry)
            return new_Z

        matching = df.apply(update_Z, axis=1)

        df['Matchings'] = matching

        
        l =  df['Matchings'].iloc[0]
        return sorted(l, key=lambda x: list(x.values())[1])
    else: 
        return None