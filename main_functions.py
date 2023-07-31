import pandas as pd
import re
import unicodedata

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from helper_functions import *

def best_sim_score(l1, l2, l3, l4, simU, simG):
    """
    Finds the best match between a 'key word' and several legal names from the OpenAIRE/ROR database.
    ---> corrects special cases in the main map that follows

    Args:
        l1: List of light affiliations.
        l2: number of candidates.
        l3: List of pairs.
        l4: mult

    Returns:
        List: Resulting list containing OpenAIRE names and their similarity scores.
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

                
              
            elif l3[j][2] >=0.99 and (is_contained("univ", x.lower()) or is_contained("college", x.lower()) or  is_contained("center", x.lower()) or  is_contained("schule", x.lower())): # If the similarity score of a pair (s,x) was 1, we store it to results list
                result.append([l3[j][1], 1])
                
            else:
                try:
                    if not is_contained("univ", x.lower()):
                        continue  # Skip if x does not contain "university" or "univ"
                    
                    if (is_contained('hosp', x.lower()) and not is_contained('hosp', s)) or (not is_contained('hosp', x.lower()) and is_contained('hosp', s)):
                        continue
                    s_vector = vectorizer.fit_transform([s]).toarray() #Else we compute the similarity of s with the original affiiation name
                    x_vector = vectorizer.transform([x]).toarray()
     
                    # Compute similarity between the vectors
                    similarity = cosine_similarity(x_vector, s_vector)[0][0]
                    if similarity> 0.1:
   
                        best.append([x, similarity])#(similarity+similarity2)/2])
                except:
                    KeyError
                    
        if best:
            max_numbers = defaultdict(float)
            for item in best:
                string, number = item
                max_numbers[string] = max(max_numbers[string], number)

# Create a new list with the elements having the maximum number for each string
            reduced_best = [[string, number] for string, number in best if number == max_numbers[string]]

            reduced_best.sort(key=lambda x: x[1], reverse=True)
   
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



def Aff_Ids(m, DF, dix_org, simU, simG):
    
    """
    Matches affiliations in DataFrame 'DF' with names from dictionary 'dix_org' and their ROR_ids based on similarity scores.

    Args:
        m (int): The number of DOIs to check.
        DF (DataFrame): The input DataFrame containing affiliation data.
        dix_org (dict): A dictionary of names of organizations and their ROR_ids.
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

                            if ' and ' in s:
                                list_s = s.split(' and ')
                                
                                if list_s:
                                    for q in list_s:
                                        if is_contained('univ', q):

                                            q_vector = vectorizer.fit_transform([q]).toarray()
                                            x_vector = vectorizer.transform([x]).toarray()

                                # Compute similarity between the vectors
                                            similarity = cosine_similarity(q_vector, x_vector)[0][0]
                                            if similarity > simU:
                                                similar_k.append(similarity)
                                                deiktes.append(k)
                                                pairs_k.append((s,x,similarity,dix_org[x]))

                                                if k not in dix:
                                                    dix[k] = [x]
                                                else:
                                                    dix[k].append(x)
                            
                            else: 

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


    aff_id_df['Matched openAIRE names'] = list(dix.values())
    aff_id_df['# Matched orgs'] = [len(list(dix.values())[i]) for i in range(len(list(dix.values())))]
    

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
    df_final1['Matched openAIRE names'] = best_o
    df_final1['Similarity score'] = best_s
    df_final1['# Matched orgs'] = num_mathced
    
    final_df =  pd.concat([df_final0, df_final1])
    final_df.set_index('index', inplace=True)
    final_df.sort_values('index', ascending=True, inplace = True)
    
    ids = [[dix_org[x] for x in v] for v in final_df['Matched openAIRE names']]
    
    new_ror = []
    for v in ids: 
        v1 = [item for sublist in v for item in sublist]
        new_ror.append(list(set(v1)))

    new_ror
    

    numIds = [len(x) for x in new_ror]


    final_df['ROR'] = ids 
    final_df['# unique RORs'] = numIds
    final_df = final_df[~(final_df['# Matched orgs'] == 0)]
    
    final_df = final_df.reset_index(drop=True)
    
    diff = [i for i in range(len(final_df)) if final_df['# Matched orgs'].iloc[i]> final_df['# unique RORs'].iloc[i]]
    
    for k in diff:
        final_df.at[k,'Matched openAIRE names']=(final_df['Matched openAIRE names'].iloc[k])[0]
        final_df.at[k,'# Matched orgs']=1
        final_df.at[k,'Similarity score']=(final_df['Similarity score'].iloc[k])[0]
        final_df.at[k,'ROR']=(final_df['ROR'].iloc[k])[0]

    perc = 100*len(final_df)/m



    
    
    return [perc,final_df]
    
