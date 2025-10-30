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
        if  is_contained(keyword, x):# and ('univ' in x or 'inst' in x or len(get_candidates([])) < len(dix_name)):
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
    # print('end find_candidate', pairs_k)   
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



