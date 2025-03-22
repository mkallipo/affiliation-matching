import Levenshtein
from functions_cluster import *
from create_input_cluster import *


    
specific = [k for k in categ_dicts if categ_dicts[k] == 'Specific']

def index_multiple_matchings(pairs):
    d = {}
    for p in pairs:
        d[p[0][0]] = len(p)

    return d

def keep_highest_url(lst):
    best = {}

    for item in lst:
        name, score, url = item
        if name not in best or url > best[name][2]:  # Keep the highest URL
            best[name] = item  # Store the full entry

    return list(best.values())  # Convert dictionary values back to list

def find_candidate(keyword, k, dix, simU, simG, dix_org, limit): 
   
    vectorizer = CountVectorizer()

    similar_k = []
    pairs_k = []
    total_pairs = 0
    for x in dix_org:
    #    print(x,total_pairs)
        if  is_contained(keyword, x):

            x_vector = vectorizer.fit_transform([x]).toarray()
            keyword_vector = vectorizer.transform([keyword]).toarray()

            # Compute similarity between the vectors
            similarity = cosine_similarity(x_vector, keyword_vector)[0][0]
            if similarity > min(simU, simG):
                if ('univ' in keyword and 'univ' in x) and similarity > simU:
                    similar_k.append(similarity)
                    pairs_k.append((keyword,x,similarity,dix_org[x], dix_id_country[dix_org[x]]))
                    total_pairs += 1  # Track total number of pairs


                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)
                        
    
                elif (not 'univ'in keyword and not 'univ' in x) and similarity > simG:
                    similar_k.append(similarity)
                    pairs_k.append((keyword,x,similarity,dix_org[x], dix_id_country[dix_org[x]]))
                    total_pairs += 1  # Track total number of pairs


                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)
            
                    
                        
        elif is_contained(x, keyword):
            if ('univ'in keyword and 'univ' in x):

                keyword_vector = vectorizer.fit_transform([keyword]).toarray()
                x_vector = vectorizer.transform([x]).toarray()

                # Compute similarity between the vectors
                similarity = cosine_similarity(keyword_vector, x_vector)[0][0]
                if similarity > simU: #max(0.82,sim):
                    similar_k.append(similarity)
                    pairs_k.append((keyword,x,similarity,dix_org[x], dix_id_country[dix_org[x]]))
                    total_pairs += 1  # Track total number of pairs

                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)
                        
                
                    
            elif not 'univ' in keyword and not 'univ' in x:

                keyword_vector = vectorizer.fit_transform([keyword]).toarray()
                x_vector = vectorizer.transform([x]).toarray()

                # Compute similarity between the vectors
                similarity = cosine_similarity(keyword_vector, x_vector)[0][0]
                if similarity > simG: #max(0.82,sim):
                    similar_k.append(similarity)
                    pairs_k.append((keyword,x,similarity,dix_org[x], dix_id_country[dix_org[x]]))
                    total_pairs += 1  # Track total number of pairs

                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)  
                    #    total_pairs += len(pairs_k)  # Track total number of pairs
        if total_pairs >= limit:  # Stop if we reach 
            return [] 

    return  pairs_k



def best_sim_score(clean_aff, light_raw, candidate_num, pairs_list, multi, simU, simG):
    """
    Finds the best match between a keyword (clean_aff) and legal names from the PID database.
    """
    
    vectorizer = CountVectorizer()
    univ_num = light_raw.lower().count('univ')  
    result = []
    best = []

    # Step 1: Reduce pairs_list based on country match
    country_check = {'usa' if 'united states' in clean_aff else None,
                     'uk' if 'united kingdom' in clean_aff else None}
    country_check.discard(None)  # Remove None values

    pairs_list_reduced = [
        [item for item in pair if item[4] in country_check or item[4] in clean_aff]
        for pair in pairs_list
    ]

    # Remove empty lists
    pairs_list_reduced = [pair for pair in pairs_list_reduced if pair]

#    print('PAIRS_LIST_REDUCED: ', pairs_list_reduced)
    
    if not any(pairs_list_reduced):
        pairs_list_reduced = pairs_list

    for pair_group in pairs_list_reduced:
        
        best_j = []
        affil = pair_group[0][0]  
        num_uni_p = affil.count('univ')  

#        print('AFFIL', affil)
        for p in pair_group:
            organization, confidence = p[1], p[2]

            # Skip duplicates
            if [organization, confidence] in result:
                continue
            
            # Check similarity conditions
            if multi[p[0]] == 1:
                if 'univ' in organization.lower() and confidence > simU:
                    result.append([organization, confidence])
                elif confidence > simG:
                    result.append([organization, confidence])

            elif confidence >= 0.98:
                result.append([organization, 1])
            else:
                if "univ" not in organization:
                    continue  # Skip if 'univ' is missing

                try:
                    s_vector = vectorizer.fit_transform([light_raw]).toarray()
                    x_vector = vectorizer.transform([organization]).toarray()
                    similarity = cosine_similarity(x_vector, s_vector)[0][0]

                    if similarity > 0.1:  #use Levenshtein to better handle misspellings 
                        similarity_l = 1 - Levenshtein.distance(organization, affil) / max(len(organization), len(affil))
                        best_j.append([organization, similarity, similarity_l])
                
                except Exception as ex:
                    print("Error:", ex)

        # Step 2: Keep only the best similarity per organization
        max_numbers = defaultdict(float)
        for org, sim, sim_l in best_j:
            max_numbers[org] = max(max_numbers[org], sim)

        reduced_best = [[org, sim, sim_l] for org, sim, sim_l in best_j if sim == max_numbers[org]]

        # Sort by similarity score (descending) and then lexicographically
        reduced_best.sort(key=lambda x: (x[1], x[2]), reverse=True)
    #    print('REDUCED BEST: ', reduced_best)

        result.extend(reduced_best)
    #    print('RESULT EXT: ', result)

        # Step 3: Limit university-related matches
        univ_list = [r for r in result if 'univ' in r[0]]
        other_list = [r for r in result if 'univ' not in r[0]]

        limit = min(num_uni_p, candidate_num)
        if len(univ_list) > limit:
            result = univ_list[:limit] + other_list

        best.append(best_j)

    # Step 4: Construct final dictionary **with highest confidence values**
    pairs_dict = {p[1]: p[2] for group in pairs_list_reduced for p in group}

    # Select the best confidence score for each organization
    result_dict = {}
    for res in result:
        org = res[0]
        similarity_score = res[1]
        if org in pairs_dict:
            best_confidence = pairs_dict[org]  # Original confidence score from pairs_list
            if org not in result_dict or similarity_score > result_dict[org][1]:
                result_dict[org] = [best_confidence, similarity_score]

    # Convert to list format
    final_result = [[key, value[0]] for key, value in sorted(result_dict.items(), key=lambda x: x[1][1], reverse=True)]

#    print("RESULT TO USE: ", final_result)
    return final_result



def Aff_Ids(input, dix_org, dix_mult, dix_city_ror, dix_country_ror, simU, simG, limit):
    
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
    clean_aff = input[0]
#    print('CLEAN_AFF (LVL1): ', clean_aff)
    light_aff = input[1]
#    print('LIGHT_AFF (LVL2): ', light_aff)

    df_list = input[2]
    vectorizer = CountVectorizer()

    dix = {}    # will store indeces and legalnames of organizations of the DOI { i : [legalname1, legalname2,...]}
    result = {}
    pairs = []
 
    keywords =  [entry["keywords"] for entry in df_list] 


#    print('KEYWORDS: ', keywords)
    for k,s in enumerate(keywords):
        pairs_k = []
        
        if s in dix_org:
            
            pairs_k.append((s,s,1,dix_org[s],dix_id_country[dix_org[s]]))
           # pairs.append((s,s,similarity,dix_org[s], dix_id_country[dix_org[s]]))

            if k not in dix:
                dix[k] = [s]
            else:
                dix[k].append(s)
                
        else:
            pairs_k = find_candidate(s, k , dix,  simU, simG, dix_org, limit)

      
        result[k] = pairs_k
        if len(pairs_k)>0:
            pairs.append(pairs_k)
            
   # print('PAIRS: ', pairs)  
    multi = index_multiple_matchings(pairs)
   # print('MULTIL ',multi)

    need_check_keys = []
    ready_keys = []
    ready_best = []
    for keyword in multi:
        try: 
            if  multi[keyword]>1:
                need_check_keys.append(keyword)
            else:
                for p in pairs:
                    if keyword in p[0]:
                        if p[0][1] not in ready_keys:
                            ready_keys.append(p[0][1])

                            ready_best.append([p[0][1], p[0][2]])
        except:
            pass
#    print('READY KEYWORD: ', ready_keys)
#    print('READY BEST: ', ready_best)

#    print('NEED CHECK KEYWORD: ', need_check_keys)

    pairs_check = [ pair for pair in pairs if pair[0][0] in need_check_keys ]
   # print('NEED CHECK PAIRS: ', pairs_check)
    
    
    if len(need_check_keys)>0:
        best0 =  best_sim_score(clean_aff, light_aff, len(keywords), pairs_check, multi, simU, simG)
    #    print('OUTPUT BEST: ', best0)
        best1 = {x[0]:dix_org[x[0]] for x in best0 }
        best01 = unique_subset(best0, best1)
        matched_org = list(set([x[0] for x in best01])) +  ready_keys
        best = best01 + ready_best

            
    
    #    print('NEW BEST',best01)
    else:
        best = ready_best
        matched_org = ready_keys
        

  #  print('FINAL BEST: ', best)
#    print('MATCHED: ', matched_org)

    id_list = []
    
    for org_list in best:
        org = org_list[0]
        conf = org_list[1]
        if dix_mult[org] == 'unique':
#            print('unique:', org)
            if 'institu' in org and 'univ' in org:
#                print('yes')
                if dix_city_ror[org][0] not in clean_aff and dix_country_ror[org][0] not in clean_aff:
                    pass
                
            else:
                id_list.append([org, conf, dix_org[org]])

       
        else:
            if org in dix_city_ror:
                match_found = False

                for city in dix_city_ror[org]:
                    if city[0] in clean_aff:
                        if city[0] not in org: 
                            id_list.append([org, conf, city[1]])
                            match_found = True
                            break
                        else:
                            if clean_aff.count(city[0]) >1:
                                id_list.append([org, conf, city[1]])
                                match_found = True
                                break
                            
                if not match_found:
                    for city in dix_city_ror[org]:
                        if city[0] in   clean_aff and city[0] not in org:
                            id_list.append([org, conf, city[1]])
                            break  
                    
                if not match_found:
                    match_found2 = False
                    match_found3 = False

                    for country in dix_country_ror[org]:
                        if country[0] == 'united states' and (country[0] in clean_aff or 'usa'  in clean_aff or 'u.s.a' in clean_aff):
                            id_list.append([org, conf, country[1]])
                            match_found2 = True
                            match_found3 = True
                            break
                        
                        if country[0] == 'united kingdom' and (country[0] in clean_aff or 'uk'  in clean_aff or 'u.k.' in clean_aff):
                            id_list.append([org, conf, country[1]])
                            match_found2 = True
                            match_found3 = True
                            break

                        elif country[0] in clean_aff:

                            if country[0] not in org:
                                id_list.append([org, conf, country[1]])
                                match_found2 = True
                                match_found3 = True
                                break

                    if not match_found3:
                        for country in dix_country_ror[org]:
                            if country[0] in clean_aff and country[0] in org:
                                id_list.append([org, conf, country[1]])
                                match_found2 = True
                                break  
                    if not match_found2:
                        for sp in specific:
                            if sp in org:
                                id_list.append([org, conf, dix_org[org]])


#    print("RESULT: ", id_list)
    id_list_final = keep_highest_url(id_list)
        
    return id_list_final