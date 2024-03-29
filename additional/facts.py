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


sys.path.append('..')

from helper_functions import *
from main_functions import *

with open('../dictionaries/dix_acad.pkl', 'rb') as f:
    dix_acad = pickle.load(f)

with open('../dictionaries/dix_mult.pkl', 'rb') as f:
    dix_mult = pickle.load(f)

with open('../dictionaries/dix_city.pkl', 'rb') as f:
    dix_city = pickle.load(f)
    
with open('../dictionaries/dix_country.pkl', 'rb') as f:
    dix_country = pickle.load(f)

with open('../dictionaries/dix_acad_facts.pkl', 'rb') as f:
    dix_acad_facts = pickle.load(f)

with open('../dictionaries/dix_mult_facts.pkl', 'rb') as f:
    dix_mult_facts = pickle.load(f)

with open('../dictionaries/dix_country_facts.pkl', 'rb') as f:
    dix_country_facts = pickle.load(f)



def union2(dict1, dict2):
    return dict(list(dict1.items()) + list(dict2.items()))


dix_acad_full = union2(dix_acad, dix_acad_facts)
dix_mult_full = union2(dix_mult, dix_mult_facts)
dix_country_full = union2(dix_country, dix_country_facts)



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


def output(result, doi_df):
    dict_aff_open = {x: y for x, y in zip(result['Original affiliations'], result['Matched organizations'])}
    dict_aff_id = {x: y for x, y in zip(result['Original affiliations'], result['unique ROR'])}
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
    return doi_df_output
    
    
def facts_ror(csv_file):
    facts_df = pd.read_csv(csv_file)
    facts_df['country'] = facts_df['country'].replace(countries)
    facts_df['Unique affiliations'] = list(facts_df['institution'])

    for i,name in enumerate(list(facts_df['institution'])):
        if name[-2:] == ' U':
            facts_df.at[i,'Unique affiliations'] = clean_string_facts(name) + 'niversity' + ', ' + facts_df['country'].iloc[i]
            
        elif name[:3] == 'TU ':
            facts_df.at[i,'Unique affiliations'] = 'Technische Universitat'+ clean_string_facts(name)[2:] + ', ' + facts_df['country'].iloc[i]
            
        elif name[:3] == 'TH ':
            facts_df.at[i,'Unique affiliations'] = 'Technische Hochschule'+ clean_string_facts(name)[2:] + ', ' + facts_df['country'].iloc[i]
              
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


    result = Aff_Ids(len(academia_df), academia_df,dix_acad, dix_mult, dix_city, dix_country, 0.8,0.8)

    doi_df_output = output(result, doi_df)
    
    nf_df = facts_df[~facts_df['doi'].isin( list(doi_df_output['DOI']))]
    nf_df.reset_index(inplace = True)
    
    
    nf_df_short = nf_df.drop_duplicates(subset = 'institution')
    nf_df_short.reset_index(inplace = True)
    new_rows = []
    add = {}
    for i, country in enumerate(list(nf_df_short['country'])):
        ins = (nf_df_short['institution'].iloc[i]).lower()
        if ins in list(dix_acad_full.keys()):
            if dix_mult_full[ins] == 'unique':
                add[ins]= [{'RORid':dix_acad_full[ins], 'Confidence':1}]
    
            else:
                for pair in dix_country_full[ins]:
                    if  pair[0] == country:
                        add[ins]= [{'RORid':pair[1], 'Confidence':1}]

                    
    for i in range(len(nf_df)):
        if nf_df['institution'].iloc[i].lower() in list(add.keys()):
            new_rows.append({'DOI':nf_df['doi'].iloc[i], 'Matchings': add[nf_df['institution'].iloc[i].lower()]})

        
    new_df = pd.DataFrame(new_rows)  
    
    final_df1 = pd.concat([new_df,doi_df_output])
    
    facts_json = final_df1.to_json(orient='records', lines=True)
    
    return facts_json

#if __name__ == "__main__":

#    csv_file = sys.argv[1]


with open('facts.json', 'w') as f:  # specify the filename here, e.g., 'output.json'
    f.write(facts_ror('https://olap.openapc.net/cube/transformative_agreements/facts?format=csv&header=names&cut='))
