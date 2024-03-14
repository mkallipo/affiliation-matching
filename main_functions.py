import pandas as pd
import re
import unicodedata
import Levenshtein


from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from helper_functions import *

def best_sim_score(l1, l2, l3, l4, simU, simG):
    """
    Finds the best match between a 'key word' and several legal names from the ROR database (https://ror.org).
    ---> corrects special cases in the main map that follows

    Args:
        l1: List of light affiliations.
        l2: number of candidates.
        l3: List of pairs.
        l4: mult

    Returns:
        List: Resulting list containing organization names and their similarity scores.
    """
    
    vectorizer = CountVectorizer()
    numUniv = sum([(l1[i].lower()).count('univ') for i in range(len(l1))])
    result = []
    for i in range(len(l1)):
        best = [] 
        s = l1[i]

    
        for j in range(len(l3)):
            x = l3[j][1] 
           
            if [x, l3[j][2]] in result:
                    continue
            
            if l4[l3[j][0]] == 1:
               
                if  is_contained('univ', x.lower()) and  l3[j][2]> simU:
                    result.append([x, l3[j][2]])
                elif  l3[j][2] >simG:
                    result.append([x, l3[j][2]])

                
              
            elif l3[j][2] >=0.99:# and (is_contained("univ", x.lower()) or is_contained("college", x.lower()) or  is_contained("center", x.lower()) or  is_contained("schule", x.lower())): # If the similarity score of a pair (s,x) was 1, we store it to results list
                result.append([l3[j][1], 1])
                
            else:
                try:
                    if not is_contained("univ", x.lower()):
                        continue  # Skip if x does not contain "university" or "univ"
                    
                    if (is_contained('hosp', x.lower()) and not is_contained('hosp', s)) or (not is_contained('hosp', x.lower()) and is_contained('hosp', s)) or (is_contained('hopital', x.lower()) and not is_contained('hopital', s)) or (not is_contained('hopital', x.lower()) and is_contained('hopital', s)):
                        continue
                    s_vector = vectorizer.fit_transform([s]).toarray() #Else we compute the similarity of s with the original affiiation name
                    x_vector = vectorizer.transform([x]).toarray()
     
                    # Compute similarity between the vectors
                    similarity = cosine_similarity(x_vector, s_vector)[0][0]
                    if similarity> 0.1:
                        similarity_l = 1 - Levenshtein.distance(x, l3[j][0]) / max(len(x), len(l3[j][0]))
                        best.append([x, similarity,similarity_l])
   
                except:
                    KeyError
                    
        if best:
            max_numbers = defaultdict(float)
            for item in best:
                string, number1, number2 = item  # Unpack the three elements
                max_numbers[string] = max(max_numbers[string], number1)

            reduced_best = [[string, number1, number2] for string, number1, number2 in best if number1 == max_numbers[string]]

# Sort by number1 decreasingly and then by number2 in descending order
            reduced_best.sort(key=lambda x: (x[1], x[2]), reverse=True)
   
            result = result + reduced_best
                
    univ_list = []
    other_list = []
    
    for r in result:
        if is_contained('univ',r[0]):
            univ_list.append(r)
        else:
            other_list.append(r)
    
    limit =  min(numUniv, l2)

    if len(univ_list)> limit:
        result = univ_list[:limit] + other_list
        
    result_dict = {}
    pairs_dict = {}
    
    
    for l in l3:
        pairs_dict[l[1]] = l[2]
        
        
    for p in result:
        result_dict[p[0]]= pairs_dict[p[0]]
        
    
        
        
    result_dict_list = [[y[0],result_dict[y[0]]] for y in result]  
        
                
    return result_dict_list
                

def index_multiple_matchings(df):
    multiple_matchings = []
    mult = []

    for i in range(len(df)):
        result_dict = {}
        
        r_list = [y[3] for y in df.Pairs.iloc[i]]
        modified_list = [item for sublist in r_list for item in sublist]
        r = len(list(set(modified_list)))
            
        for t in [t[0] for t in df.Pairs.iloc[i]]:
            key = t
            if key in result_dict and r>1:
                result_dict[key] += 1
                multiple_matchings.append(i)
                
            else:
                result_dict[key] = 1
        mult.append(result_dict)
   
    return [list(set(multiple_matchings)), mult]



def Aff_Ids(m, DF, dix_org, dix_mult, dix_city, dix_country, simU, simG):
    
    """
    Matches affiliations in DataFrame 'DF' with names from dictionary 'dix_org' and their ROR_ids based on similarity scores.

    Args:
        m (int): The number of DOIs to check.
        DF (DataFrame): The input DataFrame containing affiliation data.
        dix_org (dict): A dictionary of names of organizations and their ROR_ids.
        dix_mult, dix_city, dix_country (dict): Dictionaries that help distinguish between different organizations that have the same name.
        simU (float): Similarity threshold for universities.
        simG (float): Similarity threshold for non-universities.

    Returns:
        DataFrame: The final DataFrame with matched affiliations and their corresponding similarity scores.
    """
    vectorizer = CountVectorizer()

    lnamelist = list(dix_org.keys())
    dix = {}    # will store indeces and legalnames of organizations of the DOI { i : [legalname1, legalname2,...]}
    deiktes = []  # stores indeces where a match is found
    similarity_ab = [] # stores lists of similarity scores of the mathces 
    pairs = [] #  pairs[i] =  [ [s,x,t,r] ] where (s,x) is a match, t the corresponding similarity score and r thr ROR_id
    
    for k in range(m):
        similar_k = []
        pairs_k = []


        for s in DF['Keywords'].iloc[k]:

            if s in lnamelist:
                deiktes.append(k)
                similarity = 1
                similar_k.append(similarity)
                
                pairs_k.append((s,s,similarity,dix_org[s]))

                if k not in dix:
                    dix[k] = [s]
                else:
                    dix[k].append(s)
            else:

                for x in lnamelist:
                    
                    if  is_contained(s, x):

                        x_vector = vectorizer.fit_transform([x]).toarray()
                        s_vector = vectorizer.transform([s]).toarray()

                        # Compute similarity between the vectors
                        similarity = cosine_similarity(x_vector, s_vector)[0][0]
                        if similarity > min(simU, simG):
                         
                            if (is_contained('univ', s) and is_contained('univ', x)) and similarity > simU:
                                similar_k.append(similarity)
                                deiktes.append(k)
                                pairs_k.append((s,x,similarity,dix_org[x]))

                                if k not in dix:
                                    dix[k] = [x]
                                else:
                                    dix[k].append(x)
                            elif (not is_contained('univ', s) and not is_contained('univ', x)) and similarity > simG:
                                similar_k.append(similarity)
                                deiktes.append(k)
                                pairs_k.append((s,x,similarity,dix_org[x]))

                                if k not in dix:
                                    dix[k] = [x]
                                else:
                                    dix[k].append(x)
                                    
                    elif is_contained(x, s):
                        
                        if (is_contained('univ', s) and is_contained('univ', x)):
                        
                            s_vector = vectorizer.fit_transform([s]).toarray()
                            x_vector = vectorizer.transform([x]).toarray()

                            # Compute similarity between the vectors
                            similarity = cosine_similarity(s_vector, x_vector)[0][0]
                        
                            if similarity > simU: #max(0.82,sim):
                        
                                similar_k.append(similarity)
                                deiktes.append(k)
                                pairs_k.append((s,x,similarity,dix_org[x]))

                                if k not in dix:
                                    dix[k] = [x]
                                else:
                                    dix[k].append(x)
                        
                        elif not is_contained('univ', s) and not is_contained('univ', x):

                            s_vector = vectorizer.fit_transform([s]).toarray()
                            x_vector = vectorizer.transform([x]).toarray()

                            # Compute similarity between the vectors
                            similarity = cosine_similarity(s_vector, x_vector)[0][0]
                        
                            if similarity > simG: #max(0.82,sim):
                                similar_k.append(similarity)
                                deiktes.append(k)
                                pairs_k.append((s,x,similarity,dix_org[x]))

                                if k not in dix:
                                    dix[k] = [x]
                                else:
                                    dix[k].append(x)
                            
        similarity_ab.append(similar_k)   
        similarity_ab = [lst for lst in similarity_ab if lst != []]
        pairs.append(pairs_k)
        
 
    
    
## Define the new Dataframe
    
    aff_id_df = pd.DataFrame()
    aff_id_df['Original affiliations'] = list(DF['Original affiliations'].iloc[list(set(deiktes))])

    aff_id_df['Light affiliations'] = list(DF['Light affiliations'].iloc[list(set(deiktes))])

    aff_id_df['Candidates for matching'] = list(DF['Keywords'].iloc[list(set(deiktes))])


    aff_id_df['Matched organizations'] = list(dix.values())
    aff_id_df['# Matched organizations'] = [len(list(dix.values())[i]) for i in range(len(list(dix.values())))]
    

    aff_id_df['Similarity score'] = similarity_ab

    Pairs = [lst for lst in pairs if lst]
    aff_id_df['Pairs'] = Pairs
    aff_id_df['mult'] = index_multiple_matchings(aff_id_df)[1]




## Correct the matchings
    need_check = list(set([i for i in range(len(aff_id_df)) for k in list(aff_id_df['mult'].iloc[i].values()) if k>1]))
    

    ready = [i for i in range(len(aff_id_df)) if i not in need_check]
    
   
    best = [ best_sim_score([aff_id_df['Light affiliations'].iloc[i]], len(aff_id_df['Candidates for matching'].iloc[i]), aff_id_df['Pairs'].iloc[i],aff_id_df['mult'].iloc[i], simU, simG) for i in need_check]
    best_o = []
    best_s = []
    
    for x in best:
        best_o.append([x[i][0]  for i in range(len(x))])
        best_s.append([round(x[i][1],2)  for i in range(len(x))])
    num_mathced = [len(best_s[i]) for i in range(len(need_check))]
    

    
    df_final0 = (aff_id_df.iloc[ready]).copy()
    df_final0['index'] = ready
    
    df_final1 = (aff_id_df.iloc[need_check]).copy()
    df_final1['index'] = need_check
    df_final1['Matched organizations'] = best_o
    df_final1['Similarity score'] = best_s
    df_final1['# Matched organizations'] = num_mathced
    
    final_df =  pd.concat([df_final0, df_final1])
    final_df.set_index('index', inplace=True)
    final_df.sort_values('index', ascending=True, inplace = True)
    
    #ids = [[dix_org[x] if dix_mult[x] == 'unique' else 'many'  for x in v ] for v in final_df['Matched organizations']]
    ids = []
    for i,v in enumerate(list(final_df['Matched organizations'])):
        id_list = []
        for x in v:
            if dix_mult[x] == 'unique':
                id_list.append(dix_org[x])
            else:
                if x in list(dix_city.keys()):
                    match_found0 = False
                    match_found = False

                    for city in dix_city[x]:
                        if city[0] in (final_df['Original affiliations'].iloc[i]).lower():
                            if city[0] not in x: 
                                id_list.append(city[1])
                                match_found0 = True
                                match_found = True
                                break
                    if not match_found:
                        for city in dix_city[x]:
                            if city[0] in   (final_df['Original affiliations'].iloc[i]).lower() and city[0] in x:
                                id_list.append(city[1])
                                match_found0 = True
                                break  
                    if not match_found0:
                        match_found2 = False
                        match_found3 = False

                        for country in dix_country[x]:
                            if country[0] == 'united states' and (country[0] in (final_df['Original affiliations'].iloc[i]).lower() or 'usa'  in (final_df['Original affiliations'].iloc[i]).lower()):
                                id_list.append(country[1])
                                match_found2 = True
                                match_found3 = True
                                break
                            
                            if country[0] == 'united kingdom' and (country[0] in (final_df['Original affiliations'].iloc[i]).lower() or 'uk'  in (final_df['Original affiliations'].iloc[i]).lower()):
                                id_list.append(country[1])
                                match_found2 = True
                                match_found3 = True
                                break

                            elif country[0] in (final_df['Original affiliations'].iloc[i]).lower():

                                if country[0] not in x:
                                    id_list.append(country[1])
                                    match_found2 = True
                                    match_found3 = True
                                    break

                        if not match_found3:
                            for country in dix_country[x]:
                                if country[0] in (final_df['Original affiliations'].iloc[i]).lower() and country[0] in x:
                                    id_list.append(country[1])
                                    match_found2 = True


                                    break                          
                        if not match_found2:
                            id_list.append(dix_org[x])
                else:
                    id_list.append(dix_org[x])
        ids.append(id_list)

                
            
        
    
    new_ror = []
    for v in ids: 
        v1 =list(set(v))
        new_ror.append(v1)

    
   

    numIds = [len(x) for x in new_ror]


    final_df['ROR'] = ids 
    final_df['# unique RORs'] = numIds
    final_df['unique ROR'] = new_ror

    final_df = final_df[~(final_df['# Matched organizations'] == 0)]
    
    final_df = final_df.reset_index(drop=True)
    
    return final_df
   
