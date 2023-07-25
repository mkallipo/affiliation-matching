"""
# Import packages
"""
import tarfile
import logging


import pandas as pd
import sys



import re
import unicodedata
import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,ALL_COMPLETED


from functions import *
from main_functions import *


def do(name, crossref_df):
    try: 
        print("processing file:" + name)

        crossref_df = pd.read_json(file, orient='records')

        authors = [i for i in range(len(crossref_df)) if 'author'  in crossref_df['items'][i]]

        crossref_auth = crossref_df.iloc[authors].copy()

        crossref_auth.reset_index(inplace= True)
        crossref_auth.drop(columns = ['index'], inplace = True)

        crossref_auth.loc[:, 'DOI'] = crossref_auth['items'].apply(lambda x: x['DOI'])
        crossref_auth.loc[:,'authors'] = crossref_auth['items'].apply(lambda x: x['author'])

        num_authors = [len(crossref_auth.iloc[i]['authors']) for i in range(len(crossref_auth))]

        crossref_auth.loc[:,'# authors'] = num_authors


        def getAff(k):
            return [crossref_auth['authors'][k][j]['affiliation'] for j in range(len(crossref_auth['authors'][k]))]
            
        affiliations = [getAff(k) for k in range(len(crossref_auth))]

        crossref_auth.loc[:,'affiliations'] = affiliations

        num_affil = [len(affiliations[i]) for i in range(len(crossref_auth))]

        crossref_auth.loc[:,'# Affil'] = num_affil


        # Clean 'empty' affiliations

        possible_empty_aff = []

        for k in range(len(crossref_auth)):
            if len(crossref_auth['affiliations'][k][0]) == 0:
                possible_empty_aff.append(k)
                
        non_empty_aff = []

        for k in possible_empty_aff:
            for j in range(len(crossref_auth['affiliations'].iloc[k])):
                if len(crossref_auth['affiliations'].iloc[k][j]) != 0:
                    non_empty_aff.append(k)
            
        final_emptyy_aff =  [x for x in possible_empty_aff if x not in non_empty_aff] 
        final_non_empty_aff = [x for x in range(len(crossref_auth)) if x not in final_emptyy_aff]


        # doi_df: crossref_auth subdataframe with nonpempty affiliation lists

        doi_df = crossref_auth.iloc[final_non_empty_aff].copy()
        doi_df.reset_index(inplace = True)
        doi_df.drop(columns = ['index'], inplace = True)

        # (still some cleaning: cases with empty brackets [{}])

        empty_brackets = [k for k in range(len(doi_df)) if len(doi_df['affiliations'][k][0]) != 0 and doi_df['affiliations'][k][0][0] == {}]
        doi_df.iloc[empty_brackets]
        doi_df.drop(empty_brackets, inplace = True)

        doi_df.reset_index(inplace = True)
        doi_df.drop(columns = ['index'], inplace = True)


        # 1. "Unique" affiliations --- number of unique affiliations

        unique_aff = []
        error_indices =[] # New list to store error indices
        for i in range(len(doi_df)):
            try:
                unique_aff.append(list(set([x[0] for x in [list(d.values()) for d in [item for sublist in doi_df['affiliations'].iloc[i] for item in sublist if sublist !=[{}] and item !={}]]])))
            except TypeError:
                print("Error occurred for i =", i)
                error_indices.append(i)  # Save the index where the error occurred
            #except IndexError:
            #   print("IndexError occurred for i =", i)
            #  error_indices.append(i)  # Save the index where the IndexError occurred

        doi_df.drop(error_indices, inplace = True)
        doi_df.reset_index(inplace = True)
        doi_df.drop(columns = ['index'], inplace = True)

        doi_df.loc[:,'unique_aff'] = unique_aff

        num_unique_aff = [len(doi_df['unique_aff'].iloc[i]) for i in range(len(doi_df))]

        doi_df.loc[:,'# unique_aff'] = num_unique_aff



        doi_df.loc[:,'unique_aff1'] = doi_df['unique_aff'].apply(lambda x: [s.lower() for s in x])


        academia_df = create_df_algorithm(doi_df)[1]




        with open('dix_ror_acad.pkl', 'rb') as f:
            dix_ror_acad = pickle.load(f)
            
            
        result = Aff_Ids(len(academia_df), academia_df, dix_ror_acad, 0.7,0.82)

                
        if len(result) == 0:
            return
        

        dict_aff_open = {x: y for x, y in zip(result[1]['Original affiliations'], result[1]['Matched openAIRE names'])}
        dict_aff_id = {x: y for x, y in zip(result[1]['Original affiliations'], result[1]['ROR'])}

        dict_aff_score = {}
        for i in range(len(result[1])):
            if type(result[1]['Similarity score'].iloc[i]) == list:
                dict_aff_score[result[1]['Original affiliations'].iloc[i]] = result[1]['Similarity score'].iloc[i]
            else:
                dict_aff_score[result[1]['Original affiliations'].iloc[i]] = [result[1]['Similarity score'].iloc[i]]
                

        pids = []
        for i in range(len(doi_df)):
            pidsi = []
            for aff in doi_df['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_id.keys()):
                    pidsi = pidsi + dict_aff_id[aff]
                elif 'unmatched organization(s)' not in pidsi:
                    pidsi = pidsi + ['unmatched organization(s)']
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
            
            
        doi_df['Matched openAIRE names'] = names
        doi_df['ROR'] = pids
        doi_df['Scores'] = scores
                
        
       
        
        unmatched = [i for i in range(len(doi_df)) if doi_df['Matched openAIRE names'].iloc[i] == []]
        
        matched = [i for i in range(len(doi_df))  if i not in unmatched]


        final_df0 =  doi_df.iloc[matched].copy()
        final_df0.reset_index(inplace = True)

        final_df = final_df0[['DOI',"Unique affiliations",'Matched openAIRE names','ROR', 'Scores']].copy()

        def update_Z(row):
            new_Z = []
            for i in range(len(row['IDs'])):
                entry = {'RORid': row['IDs'][i], 'Confidence': row['Scores'][i]}
                new_Z.append(entry)
            return new_Z

        def update_Z(row):
            if len(row['ROR']) == 0 or len(row['Scores']) == 0:
                return []
    
            new_Z = []
            for ror, score in zip(row['ROR'], row['Scores']):
                entry = {'RORid': ror, 'Confidence': score}
                new_Z.append(entry)
            return new_Z

        matching = final_df.apply(update_Z, axis=1)

        final_df['Matchings'] = matching


      
        
        # Output
        
        doi_df_output = final_df[['DOI','Matchings']]

        dois_match = doi_df_output.to_json(orient='records', lines=True)


        # Save the JSON to a file
        with open('output/' + name, 'w') as f:
            f.write(dois_match)
    except Exception as Argument:
        logging.exception("Error in thred code for file: " + name)


i = 1
data = []
numberOfThreads = int(sys.argv[2])
executor = ProcessPoolExecutor(max_workers=numberOfThreads)

with tarfile.open(sys.argv[1], "r:gz") as tar:
    while True:
        member = tar.next()
        # returns None if end of tar
        if not member:
            break
        if member.isfile():
            
            print("reading file: " + member.name)

            current_file = tar.extractfile(member)

            crossref_df = pd.read_json(current_file, orient='records')
            # print(crossref_df)
            data.append((member.name, crossref_df))
            i += 1

            if (i > numberOfThreads):
                print("execute batch: " + str([name for (name, d) in data]))
                futures = [executor.submit(do, name, d) for (name, d) in data]
                done, not_done = wait(futures)
                
                # print(done)
                print(not_done)

                data = []
                i = 0

    futures = [executor.submit(do, name, d) for (name, d) in data]
    done, not_done = wait(futures)
    print(not_done)

    print("Done")








