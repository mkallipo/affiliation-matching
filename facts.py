import pandas as pd
import re
##import unicodedata
import html


from collections import defaultdict

import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

##import functions

import sys 
from importlib import reload
from unidecode import unidecode


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



countries = {
    'GBR': 'united kingdom',
    'NLD': 'netherlands',
    'FRA': 'france',
    'DEU': 'germany',
    'SWE': 'sweden',
    'AUT': 'austria',
    'CHE': 'switzerland',
    'IRL': 'ireland',
    'ITA': 'italy',
    'LIE': 'liechtenstein',
    'FIN': 'finland',
    'QAT': 'qatar',
    'HUN': 'hungary',
    'ESP': 'spain'
}




    
def facts_ror(csv_file):
    facts_df = pd.read_csv(csv_file)
    
    facts_df['Unique affiliations'] = list(facts_df['institution'])

    for i,name in enumerate(list(facts_df['institution'])):
        if name[-2:] == ' U':
            facts_df.at[i,'Unique affiliations'] = clean_string_facts(name) + 'niversity' + ', ' + facts_df['country'].iloc[i]
            
        elif name[:3] == 'TU ':
            facts_df.at[i,'Unique affiliations'] = 'Technische Universitat'+ clean_string_facts(name)[2:] + ', ' + facts_df['country'].iloc[i]
            
        elif name[-3:] == ' FH':
            facts_df.at[i,'Unique affiliations'] = clean_string_facts(name)[:-2] + 'University Applied Sciences' + ', ' + facts_df['country'].iloc[i]
            
        elif name[-3:] == ' TU':
            facts_df.at[i,'Unique affiliations'] = clean_string_facts(name)[:-2] + 'Technische Universitat' + ', ' + facts_df['country'].iloc[i]
        else:
            facts_df.at[i,'Unique affiliations'] =clean_string_facts(name) + ', ' + facts_df['country'].iloc[i]


    doi_df = facts_df.copy()

    doi_df = doi_df.rename(columns= {'doi':'DOI'}) 

    for i in range(len(doi_df)):
        doi_df.at[i, 'Unique affiliations']= [doi_df['Unique affiliations'].iloc[i]]


    doi_df = doi_df[['DOI','institution', 'Unique affiliations']]

    academia_df = create_df_algorithm_facts(doi_df)


    if len(academia_df)>0:   
        result = Aff_Ids(len(academia_df), academia_df,dix_acad, dix_mult, dix_city, dix_country, 0.8,0.8)

        dict_aff_open = {x: y for x, y in zip(result['Original affiliations'], result['Matched organizations'])}
        dict_aff_id = {x: y for x, y in zip(result['Original affiliations'], result['ROR'])}

        dict_aff_score = {}
        for i in range(len(result)):
            if type(result['Similarity score'].iloc[i]) == list:
                dict_aff_score[result['Original affiliations'].iloc[i]] = result['Similarity score'].iloc[i]
            else:
                dict_aff_score[result['Original affiliations'].iloc[i]] = [result['Similarity score'].iloc[i]]
                    

        pids = []
        for i in range(len(doi_df)):
            pidsi = []
            for aff in doi_df['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_id.keys()):
                    pidsi = pidsi + dict_aff_id[aff]
            # elif 'unmatched organization(s)' not in pidsi:
            #     pidsi = pidsi + ['unmatched organization(s)']
            pids.append(pidsi)
                        
                    
        names = []
        for i in range(len(doi_df)):
            namesi = []
            for aff in doi_df['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_open.keys()):
                    try:
                        namesi = namesi + dict_aff_open[aff]
                    except TypeError:
                        namesi = namesi + [dict_aff_open[aff]]
                    
            names.append(namesi)
            
        scores = []
        for i in range(len(doi_df)):
            scoresi = []
            for aff in doi_df['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_score.keys()):
                    scoresi = scoresi +  dict_aff_score[aff]
                    
            scores.append(scoresi)
            
            
        doi_df['Matched organizations'] = names
        doi_df['ROR'] = pids
        doi_df['Scores'] = scores


        unmatched = [i for i in range(len(doi_df)) if doi_df['Matched organizations'].iloc[i] == []]
                
        matched = [i for i in range(len(doi_df))  if i not in unmatched]


        final_df0 =  doi_df.iloc[matched].copy()
        final_df0.reset_index(inplace = True)

        final_df = final_df0[['DOI',"institution",'Matched organizations','ROR', 'Scores']].copy()

        def update_Z(row):
            if len(row['ROR']) == 0 or len(row['Scores']) == 0:
                return []
            
            new_Z = []
            for ror, score in zip(row['ROR'], row['Scores']):
                entry = {'RORid': ror, 'Confidence': score}
                new_Z.append(entry)
            return new_Z

        matching = final_df.apply(update_Z, axis=1)

        unique_matching = []
    
        for x in matching: 
            list_of_dicts = x


            max_values = {}
            result_list = []

            for d in list_of_dicts:
                value1 = d['RORid']
                value2 = d['Confidence']

                # Check if value1 is already in max_values dictionary
                if value1 in max_values:
                    # If value2 is greater, update max_values
                    if value2 > max_values[value1]:
                        max_values[value1] = value2
                        # Replace the dictionary in the result_list with the one with higher value2
                        result_list = [item for item in result_list if item['RORid'] != value1]
                        result_list.append(d)
                else:
                    # If value1 is not in max_values, add it with its value2
                    max_values[value1] = value2
                    result_list.append(d)
            unique_matching.append(result_list)
        final_df['Matchings'] = matching

        
        doi_df_output = final_df[['DOI','Matchings']]
        facts_json = doi_df_output.to_json(orient='records', lines=True)
        
        return facts_json
            
            
                

if __name__ == "__main__":

    csv_file = sys.argv[1]


    with open('facts.json', 'w') as f:  # specify the filename here, e.g., 'output.json'
        f.write(facts_ror(csv_file))
