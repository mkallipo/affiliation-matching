import Levenshtein
from .functions import *
from .create_input import * 


def index_multiple_matchings(pairs):
    d = {}
    for p in pairs:
        d[p[0][0]] = len(p)
    return d

def find_candidate(keyword, k, dix, simU, simG, candidates_, limit): 
    vectorizer = CountVectorizer()
    
    similar_k = []
    pairs_k = []
    total_pairs = 0

    for x in candidates_:
        if  is_contained(keyword, x):
            x_vector = vectorizer.fit_transform([x]).toarray()
            keyword_vector = vectorizer.transform([keyword]).toarray()

            # Compute similarity between the vectors
            similarity = cosine_similarity(x_vector, keyword_vector)[0][0]
            if similarity > min(simU, simG):
                if ('univ' in keyword and 'univ' in x) and similarity > simU:
                    similar_k.append(similarity)
                    pairs_k.append((keyword,x,similarity))
                    total_pairs += 1  # Track total number of pairs


                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)
                        
    
                elif (not 'univ'in keyword and not 'univ' in x) and similarity > simG:
                    similar_k.append(similarity)
                    pairs_k.append((keyword,x,similarity))
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
                    pairs_k.append((keyword,x,similarity))
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
                    pairs_k.append((keyword,x,similarity))
                    total_pairs += 1  # Track total number of pairs

                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)  
        if total_pairs >= limit:  # Stop if we reach 
            return [] 
    return  pairs_k



def best_sim_score(clean_aff, light_raw, candidate_num, pairs_list, multi, simU, simG):
    """
    Finds the best match between a keyword (clean_aff) and legal names from the PID database.
    """
    
    vectorizer = CountVectorizer()
    result = []
    best = []

    for pair_group in pairs_list:
        
        best_j = []
        affil = pair_group[0][0]  
        num_uni_p = affil.count('univ')  

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

        result.extend(reduced_best)

        # Step 3: Limit university-related matches
        univ_list = [r for r in result if 'univ' in r[0]]
        other_list = [r for r in result if 'univ' not in r[0]]

        limit = min(num_uni_p, candidate_num)
        if len(univ_list) > limit:
            result = univ_list[:limit] + other_list

        best.append(best_j)

    # Step 4: Construct final dictionary **with highest confidence values**
    pairs_dict = {p[1]: p[2] for group in pairs_list for p in group}

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

    return final_result



def find_name(input, dix_name, simU, simG, limit):
 #   print('start find_name')
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
    light_aff = input[1].replace(' gmbh', ' ').strip()
    df_list = input[2]
    
    countries_list = input[3]
  
    dix = {}    # will store indeces and legalnames of organizations of the DOI { i : [legalname1, legalname2,...]}
    result = {}
    pairs = []
 
    keywords =  [entry["keywords"].replace(' gmbh', ' ').strip() for entry in df_list] 

    candidates = get_candidates(countries_list)
    if len(keywords) > 1 or len(keywords) == 1 and len(keywords[0])>1:
        for k,s in enumerate(keywords):
            pairs_k = []
            try:
                pairs_k.append((s,s,1, dix_name[s][0]['id'],dix_name[s][0]['country']))

                if k not in dix:
                    dix[k] = [s]
                else:
                    dix[k].append(s)
                    
            except Exception as e:
                pairs_k = find_candidate(s, k , dix,  simU, simG, candidates, limit)
        
            result[k] = pairs_k
            if len(pairs_k)>0:

                pairs.append(pairs_k)
    multi = index_multiple_matchings(pairs)
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
 
    pairs_check = [ pair for pair in pairs if pair[0][0] in need_check_keys ]
    
    if len(need_check_keys)>0:
        best0 =  best_sim_score(clean_aff, light_aff, len(keywords), pairs_check, multi, simU, simG)
        best1 = {x[0]:dix_name[x[0]][0]['id'] for x in best0 }
        best01 = unique_subset(best0, best1)
        best = best01 + ready_best
    else:
        best = ready_best
 #   print('end find_name', best) 
    return best
