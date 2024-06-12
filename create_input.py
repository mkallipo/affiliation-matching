import pandas as pd
import re
import unicodedata
from unidecode import unidecode
from collections import defaultdict
import html

import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from functions import *


################# Helper functions #################



def create_df_algorithm(gendf):
    all_affs_list = []

    for doi in list(gendf['Unique affiliations']):
        for aff in doi:
            if aff not in all_affs_list:
                all_affs_list.append(aff)


    gendf1 = gendf.copy()
    
    # Clean the affiliations by removing symbols and special characters.
    aff_no_symbols_d = {}
    for x in list(gendf1['Unique affiliations']):
        for y in x:
            if y!= 'inc' and y not in list(aff_no_symbols_d.keys()):
                aff_no_symbols_d[y] = clean_string(remove_outer_parentheses(y))

        
    aff_df = pd.DataFrame.from_dict(aff_no_symbols_d, orient='index')
    aff_df.reset_index(inplace = True)
    aff_df.rename(columns = {'index':'Original affiliations', 0:'Level1 affiliations'}, inplace = True)
    
    new_aff_komma = [substrings_dict(aff) for aff in list(aff_df['Level1 affiliations'])]

    new_aff_komma_1 = []
    for dict_ in new_aff_komma:
    
        if len(dict_)>1:
            for i in range(len(dict_)-1):
                if is_contained('progr', dict_[i]) and is_contained('dep', dict_[i+1]):
                    del dict_[i]
                elif (is_contained('assistant', dict_[i]) or is_contained('researcher', dict_[i]) or is_contained('phd', dict_[i]) or is_contained('student', dict_[i]) or is_contained('section', dict_[i]) or is_contained('prof', dict_[i]) or is_contained('director', dict_[i])) and (not is_contained('school', dict_[i+1]) or is_contained('univ', dict_[i+1]) or is_contained('inst', dict_[i+1]) or is_contained('lab', dict_[i+1]) or is_contained('fac', dict_[i+1])):
                    del dict_[i]
                elif (is_contained('engineer', dict_[i]) or is_contained('progr', dict_[i]) or is_contained('unit', dict_[i]) or is_contained('lab', dict_[i]) or is_contained('dep', dict_[i]) or  is_contained('school', dict_[i])  or is_contained('inst', dict_[i]) or is_contained('hosp', dict_[i]) or is_contained('fac', dict_[i])) and is_contained('univ', dict_[i+1]):
                    if not is_contained('univ', dict_[i]):
                        del dict_[i]
                elif is_contained('lab', dict_[i]) and (is_contained('college', dict_[i+1]) or is_contained('inst', dict_[i+1]) or is_contained('dep', dict_[i+1]) or is_contained('school', dict_[i+1])):
                    if not is_contained('univ', dict_[i]):
                        del dict_[i]
                elif is_contained('dep', dict_[i]) and (is_contained('tech', dict_[i+1]) or is_contained('college', dict_[i+1]) or is_contained('inst', dict_[i+1]) or  is_contained('hosp', dict_[i+1]) or  is_contained('school', dict_[i+1]) or  is_contained('fac', dict_[i+1])):
                    if not is_contained('univ', dict_[i]):
                        del dict_[i]
                elif is_contained('inst',dict_[i]) and (is_contained('school', dict_[i+1]) or is_contained('dep', dict_[i+1]) or is_contained('acad', dict_[i+1]) or is_contained('hosp', dict_[i+1]) or is_contained('clin', dict_[i+1]) or is_contained('klin', dict_[i+1])  or is_contained('fak', dict_[i+1]) or is_contained('fac', dict_[i+1]) or is_contained('cent', dict_[i+1]) or is_contained('div', dict_[i+1])):
                    if not is_contained('univ', dict_[i]):
                        del dict_[i]
    
        if len(dict_) > 1:
            dict_ = {i: list(dict_.values())[i] for i in range(len(dict_))}
            dict_[len(dict_)+1] = '.'

            i = 0
            while i < len(dict_) - 1:  # Ensure there's at least one element after the current one
                try:
                    if 'universi' in dict_[i] and starts_with_any(dict_[i + 1], ['dublin', 'cork', 'limerick', 'galway', 'waterford','maynooth'])[0] and dict_[i].split(' ')[-1] not in city_names and  starts_with_any(dict_[i + 1], ['dublin', 'cork', 'limerick', 'galway', 'waterford','maynooth'])[1] not in dict_[i]:
                        dict_[i] = dict_[i] + ' ' + dict_[i + 1]
                        dict_.pop(i + 1)
                        i += 2
                    else:
                        i += 1
                except:
                    i += 1  
        new_aff_komma_1.append(dict_)



    for dict_ in new_aff_komma_1:
        for i in list(dict_.keys()):

            if dict_[i] in city_names+remove_list:
                del dict_[i]

   # light_aff = []
   # for dict_ in new_aff_komma:
   #     light_aff.append(', '.join(list(dict_.values())))
        
    aff_df['Level2 affiliations'] = [', '.join(list(d.values())) for d in new_aff_komma_1]
    
    aff_df['Keywords'] =  [list(d.values()) for d in new_aff_komma_1]
    
    affiliations_dict = {}

    for i in range(len(aff_df)):
        affiliations_dict[i] = aff_df['Keywords'].iloc[i]
        
    d_new = {}

    # iterate over the keys of affiliations_dict
    for k in range(len(affiliations_dict)):
        # get the list associated with the current key in affiliations_dict
        L = affiliations_dict.get(k, [])
        mapped_listx = [[s, v] for s in L for k2, v in categ_dicts.items() if k2 in s]
        

        # add the mapped list to the new dictionary d_new
        d_new[k] = mapped_listx
        
    aff_df['Dictionary'] = list(d_new.values())
    
    
    aff_df.loc[:, 'Category'] = [', '.join(list(set([x[1] for x in aff_df['Dictionary'].iloc[i]]))) for i in range(len(aff_df))]
    
    # Create a comma-separated string of categories for each affiliation.
    aff_df['Category'] = [', '.join(list(set([x[1] for x in aff_df['Dictionary'].iloc[i]]))) for i in range(len(aff_df))]

    # Simplify the keywords by removing duplicates within each affiliation.
    affiliations_simple = [list(set([x[0] for x in d_new[i]])) for i in range(len(aff_df))]

    aff_df['Keywords'] = shorten_keywords(affiliations_simple)
    
    # Filter the affiliations based on the specified category string.
    filtered = aff_df[aff_df['Category'].str.contains(categ_string)].index.tolist()

    # Create a new DataFrame containing only the filtered affiliations.
    filtered_df = aff_df.iloc[filtered].copy()
    filtered_df.reset_index(inplace = True)
    filtered_df.drop(columns = ['index'], inplace = True)
    
    return filtered_df

    
