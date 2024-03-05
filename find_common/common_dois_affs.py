import pandas as pd
import re
##import unicodedata
import html
import tarfile
import os 
import sys, getopt


from collections import defaultdict


import json
import logging

## Upload json files
#file0 = 'sample5000.json'


file_path = 'dois_comparisson.txt.txt'

with open(file_path, 'r') as file:
    common_list = [line.strip() for line in file]
    
def main(*args):
    # Check if we have the expected number of arguments
    if len(args) != 1:
        print("Usage: python script.py archive_file file_path")
        return

    archive_file = args[0]
    #file_path = args[1]


    # Open and read the file_path
  

    # Open the archive file for reading in gzip format
    with tarfile.open(archive_file, 'r:gz') as tar:
        for member in tar:
            if member.isfile():
                print("Reading file: " + member.name)

                # Extract the current file from the archive
                current_file = tar.extractfile(member)

                # Read JSON data into a DataFrame
                crossref_df = pd.read_json(current_file, orient='records')

                try:
                    print('Processing file: ' + member.name)
                    result = dois_affs(crossref_df)
                    if len(result)>0:

                    # Save the Excel file with a name corresponding to the input JSON file
                        output_csv_file = os.path.join("common_csv", member.name.replace('.json', '.csv'))
                        result.to_csv(output_csv_file, index=False)


                except Exception as e:
                    print(e)
                    logging.error("Error in processing file: " + member.name)


#common_list = ['10.1128/jcm.40.7.2408-2419.2002', '10.1105/tpc.12.8.1331','10.1104/pp.010931']

def dois_affs(crossref_df):

    authors = [i for i in range(len(crossref_df)) if 'author'  in crossref_df['items'][i]]

    crossref_auth = crossref_df.iloc[authors].copy()

    crossref_auth.reset_index(inplace= True)
    crossref_auth.drop(columns = ['index'], inplace = True)

    crossref_auth.loc[:, 'DOI'] = crossref_auth['items'].apply(lambda x: x['DOI'])
    crossref_auth.loc[:,'authors'] = crossref_auth['items'].apply(lambda x: x['author'])

    def getAff(k):
        return [crossref_auth['authors'][k][j]['affiliation'] for j in range(len(crossref_auth['authors'][k]))]
        
    affiliations = [getAff(k) for k in range(len(crossref_auth))]

    crossref_auth.loc[:,'affiliations'] = affiliations



    ## Clean 'empty' affiliations

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
    doi_df = doi_df[doi_df['DOI'].isin(common_list)]


    # 1. "Unique" affiliations --- number of unique affiliations

    unique_aff = []
    error_indices =[] # New list to store error indices
    for i in range(len(doi_df)):
        try:
            unique_aff.append(list(set([x[0] for x in [list(d.values()) for d in [item for sublist in doi_df['affiliations'].iloc[i] for item in sublist if sublist !=[{}] and item !={}]]])))
        except TypeError:
           # print("Error occurred for i =", i)
            error_indices.append(i)  # Save the index where the error occurred
        #except IndexError:
        #   print("IndexError occurred for i =", i)
        #  error_indices.append(i)  # Save the index where the IndexError o
        # ccurred
        
    doi_df.drop(error_indices, inplace = True)
    doi_df.reset_index(inplace = True)
    doi_df.drop(columns = ['index'], inplace = True)

    doi_df.loc[:,'unique_aff'] = unique_aff

    #num_unique_aff = [len(doi_df['unique_aff'].iloc[i]) for i in range(len(doi_df))]

    #doi_df.loc[:,'# unique_aff'] = num_unique_aff

    new_aff0 = []

    for k in range(len(doi_df)):
        
        L2 = []
        for s1 in doi_df['unique_aff'].iloc[k]:
            is_substring = False
            for s2 in doi_df['unique_aff'].iloc[k]:
                if s1 != s2 and s1 in s2:
                    is_substring = True
                    break
            if not is_substring:
                L2.append(s1)
        new_aff0.append(L2)
        
    new_aff_list = [list(set(new_aff0[k])) for k in range(len(new_aff0))]
    doi_df['Unique affiliations'] = new_aff_list

    dois_affs_common = doi_df[['DOI', 'Unique affiliations']]
    
    return dois_affs_common
    result = dois_affs_common.to_excel('dois_affs.xlsx', index=False) 
   # with open(file, 'w') as f:
    #        f.write(result)



                    
if __name__ == '__main__':
    import sys
    main(*sys.argv[1:])
