import pandas as pd
import json
from itertools import chain
import sys 
import os
from concurrent.futures import ProcessPoolExecutor,wait,ALL_COMPLETED
import pickle


##import Levenshtein
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

##import functions

from create_input import *
from affro import *


with open('dictionaries/dix_acad.pkl', 'rb') as f:
    dix_acad = pickle.load(f)

with open('dictionaries/dix_mult.pkl', 'rb') as f:
    dix_mult = pickle.load(f)

with open('dictionaries/dix_city.pkl', 'rb') as f:
    dix_city = pickle.load(f)
    
with open('dictionaries/dix_country.pkl', 'rb') as f:
    dix_country = pickle.load(f)

with open('dictionaries/dix_status.json', 'rb') as f:
    dix_status = json.load(f)
    
folder_path = '/data/crossref/datacite_dump'

df_list = [ folder_path + "/" + filename for filename in os.listdir(folder_path)]

def parquet_to_json(p):
    print(p)
    datacite = pd.read_parquet(p)
    affiliations = [json.loads(datacite['json'].iloc[i])['attributes']['creators'] for i in range(len(datacite))]

    affiliations1 = []
    for i in range(len(affiliations)):
        if len(affiliations[i]) == 0: 
            affiliations1.append([])
        else:
            aff_i = []
            for  j in range(len(affiliations[i])):
                if affiliations[i][j]['affiliation'] not in aff_i:
                    aff_i.append(affiliations[i][j]['affiliation'])
            affiliations1.append(aff_i)
                
    affiliations2 = [list(chain.from_iterable(aff)) for aff in affiliations1]

    datacite['Unique affiliations'] = affiliations2
    
    doi_df = datacite[['doi','Unique affiliations']]
    
    doi_df = doi_df.rename(columns = {'doi':'DOI'})

    
    academia_df = create_df_algorithm(doi_df)
    
    result = Aff_Ids(len(academia_df), academia_df, dix_acad, dix_mult, dix_city, dix_country, 0.65, 0.867)
    
    if len(result)>0:
    
        affs_match = result[['Original affiliations','Matched organizations', 'unique ROR']]

        dict_aff_open = {x: y for x, y in zip(result['Original affiliations'], result['Matched organizations'])}
        dict_aff_id = {x: y for x, y in zip(result['Original affiliations'], result['ROR'])}
        #dict_aff_score = {x: y for x, y in zip(result['Original affiliations'], result['Similarity score'])}

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

        final_df = final_df0[['DOI',"Unique affiliations",'Matched organizations','ROR', 'Scores']].copy()

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

            new_matching = []
            for x in unique_matching:
                new_x = []
                for y in x:
                    if  dix_status[y['RORid']][0] == 'active':
                        y['Status'] = 'active'
                        new_x.append(y)
                else:
                    if dix_status[y['RORid']][1] == '':
                        y['Status'] = dix_status[y['RORid']][0]
                        new_x.append(y)
                    else:
                        y['Status'] = dix_status[y['RORid']][0]
                        new_x.append(y)
                        new_x.append({'RORid':dix_status[y['RORid']][1], 'Confidence': y['Confidence'], 'Status':'active'})
                new_matching.append(new_x)
                    

        final_df['Matchings'] = new_matching
        # 3. JSON [Final output]

        doi_df_output = final_df[['DOI','Matchings']]
        
        doi_json = doi_df_output.to_json(orient='records', lines=True)
        
    
        output = f'file{p}.json'

        with open("datacite-output/" + output, 'w') as f:
            f.write(doi_json)
    
    

if __name__ == '__main__':
    numberOfThreads = int(sys.argv[1])
    executor = ProcessPoolExecutor(max_workers=numberOfThreads)

    futures = [executor.submit(parquet_to_json, p) for p in df_list]
    done, not_done = wait(futures)
    print(not_done)
    
    

