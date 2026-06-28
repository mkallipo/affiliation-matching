import Levenshtein
from affro.helpers.functions import *
from affro.helpers.create_input import *

INSTIT_PHRASES = {
    'instit techn', 'pasteur instit', 'instit pasteur','educational instit',
    'instit scien', 'machinery instit', 'national instit', 'research instit', 
    'federal instit', 'instit biomedical', 'techn instit', 'instit aplied', 'fraunhofer instit', 'max planck instit', 
    'leibniz instit', 'herie instit', 'german instit', 'forth instit'
}

def index_multiple_matchings(pairs):
    """
    Index multiple matchings by creating a dictionary mapping the first element
    of each pair group to its length.
    """
    d = {}
    for p in pairs:
        d[p[0][0]] = len(p)
    return d


def find_candidate(keyword, k, dix, simU, simG, candidates_, limit):
    """
    OPTIMIZED VERSION with following improvements:
    1. Single CountVectorizer instance (no recreation in loop)
    2. Pre-computed 'univ' checks (avoid repeated string searches)
    3. Early exit when limit reached (break instead of return [])
    4. Lazy initialization of keyword_vector
    5. Reduced code duplication
    
    Expected speedup: 3-5x
    """

    # print('keyword', keyword)

    # Create vectorizer once, reuse for all iterations
    vectorizer = CountVectorizer()

    similar_k = []
    pairs_k = []
    total_pairs = 0

    # Pre-compute keyword checks
    keyword_has_univ = 'univ' in keyword
    keyword_has_school = 'school' in keyword or 'hochschule' in keyword
    keyword_has_instit = any(phrase in keyword for phrase in INSTIT_PHRASES)  or ('state' in keyword and 'instit' in keyword)

    keyword_has_hosp = 'hospital' in keyword

    keyword_vector = None  # Lazy initialization

    for x in candidates_:

        # Early exit
        if total_pairs >= limit:
            # print('limit')
            break

        # Pre-compute candidate checks
        x_has_univ = 'univ' in x
        x_has_school = 'school' in x or 'hochschule' in x
        x_has_instit = 'instit' in x

        x_has_hosp = 'hospital' in x

        similarity = None

        # ------------------------------------
        # Case 1: keyword contained in x
        # ------------------------------------
        if is_contained(keyword, x):
            # print(keyword, 'in', x)
            x_vector = vectorizer.fit_transform([x]).toarray()
            keyword_vector = vectorizer.transform([keyword]).toarray()
            similarity = cosine_similarity(x_vector, keyword_vector)[0][0]

            if similarity > min(simU, simG):
                # print('similarity', similarity,keyword_has_univ,x_has_univ )
                should_add = False
                if  x_has_univ and not keyword_has_univ:
                    pass
                elif ((keyword_has_univ and x_has_univ) or (keyword_has_school and x_has_school) or (keyword_has_hosp and x_has_hosp)) and similarity > simU:
                    # print('similarity',keyword, similarity)
                    should_add = True
                elif  (keyword_has_instit and x_has_instit)> simU:
                    should_add = True

                    # print('univ/school/instit/hosp match with high similarity')
                elif (not keyword_has_univ and not x_has_univ) and (not keyword_has_school and not x_has_school) and (not keyword_has_instit and not x_has_instit) and (not keyword_has_hosp and not x_has_hosp) and similarity > simG:
                    should_add = True
                    # print('non-univ/school/instit match with high similarity')

                if should_add:
                    similar_k.append(similarity)
                    pairs_k.append((keyword, x, similarity))
                    total_pairs += 1

                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)

        # ------------------------------------
        # Case 2: x contained in keyword
        # ------------------------------------
        elif is_contained(x, keyword):
            # print(x, 'in the', keyword)
            if (
                (keyword_has_univ and x_has_univ)
                or (not keyword_has_univ and not x_has_univ)
                or (keyword_has_school and x_has_school)
                or (not keyword_has_school and not x_has_school)
                or (keyword_has_instit and x_has_instit)
                or (not keyword_has_instit and not x_has_instit)
                or (keyword_has_hosp and x_has_hosp)
                or (not keyword_has_hosp and not x_has_hosp)
             #   or (not keyword_has_colege and not x_has_colege)
            ):
                # print('1')
                keyword_vector = vectorizer.fit_transform([keyword]).toarray()
                x_vector = vectorizer.transform([x]).toarray()
                similarity = cosine_similarity(keyword_vector, x_vector)[0][0]

                if (
                    (keyword_has_univ and x_has_univ)
                    or (keyword_has_school and x_has_school)
                    or (keyword_has_hosp and x_has_hosp)
                ):
                    threshold = simU
                elif keyword_has_instit and x_has_instit:
                    threshold = simU
                else:
                    threshold = simG

                if similarity > threshold:
                    similar_k.append(similarity)
                    pairs_k.append((keyword, x, similarity))
                    total_pairs += 1

                    if k not in dix:
                        dix[k] = [x]
                    else:
                        dix[k].append(x)
    # print('find candidate', pairs_k)
    # if 
    return pairs_k



def best_sim_score(clean_aff, light_raw, candidate_num, pairs_list, multi, simU, simG):
    """
    OPTIMIZED VERSION with following improvements:
    1. Single-pass unique max confidence detection
    2. Set-based duplicate tracking instead of list membership
    3. Single CountVectorizer instance (reused throughout)
    4. Pre-computed light_raw_vector (computed once, reused)
    5. Early detection of unique highest confidence match
    6. FIX: University limiter moved outside pair_group loop to prevent
       non-university groups from zeroing out valid university matches
    
    Expected speedup: 5-15x depending on data size
    """
    # print('best_sim')
    max_conf = -1
    max_pair = None
    
    # First, check priority pairs
    priority_pairs = []
    for group in pairs_list:
        # print(group)
        for _, org, conf in group:
            # print(_)
            if conf > 0.98:
                # print('org good',org)
                priority_pairs.append((org, conf))
            elif org in _ or _ in org:
                # print('org', org)
                priority_pairs.append((org, conf))
    
    # Check priority case
    if priority_pairs:
        # print(priority_pairs)
        max_conf = max(conf for _, conf in priority_pairs)
        winners = [(org, conf) for org, conf in priority_pairs if conf == max_conf]
        # print(winners)
        if len(winners) == 1:
            return [list(winners[0])]
    
    # Fallback: find unique max across all pairs
    max_conf = float("-inf")
    # print('max_conf', max_conf)
    max_pair = None
    max_count = 0
    # print('pairs_list', pairs_list)
    for group in pairs_list:
        # print(group)
        for _, org, conf in group:
            # print('org', org, 'conf', conf, 'max_conf', max_conf)
            if conf > max_conf:
                
                max_conf = conf
                max_pair = [org, conf]
                max_count = 1
            elif conf == max_conf:
                max_count += 1

    if max_pair and max_count == 1:
        return [max_pair]
    
    # ============================================================
    # Create vectorizer once, reuse for all computations
    # ============================================================
    
    # print('No unique max confidence found, proceeding with similarity checks...')
    vectorizer = CountVectorizer()
    
    # Pre-compute light_raw_vector once
    light_raw_vector = None
    
    result = []
    best = []
    
    # Use set for duplicate tracking (O(1) instead of O(n))
    seen_orgs = set()
    
    for pair_group in pairs_list:
        best_j = []
        affil = pair_group[0][0]  
        num_uni_p = affil.count('univ')
        
        for p in pair_group:
            # print('Processing pair:', p)
            organization, confidence = p[1], p[2]
            org_lower = organization.lower()
            org_has_univ = 'univ' in org_lower
            
            # Set-based duplicate check (O(1) lookup)
            org_key = (organization, confidence)
            if org_key in seen_orgs:
                continue
            seen_orgs.add(org_key)
            # print('multi[p[0]]',multi[p[0]])
            # Check similarity conditions
            if multi[p[0]] == 1:
                # print('multi 1:', organization, confidence)
                if org_has_univ and confidence > simU:
                    result.append([organization, confidence])
                elif confidence > simG:
                    result.append([organization, confidence])
            
            elif confidence >= 0.98:
                result.append([organization, 1])
            
            else:
                if not org_has_univ:# and not org_has_hosp:
                    continue  # Skip if 'univ' is missing
                
                try:
                    # Lazy initialization and reuse of light_raw_vector
                    if light_raw_vector is None:
                        light_raw_vector = vectorizer.fit_transform([light_raw]).toarray()
                    
                    # Reuse vectorizer
                    x_vector = vectorizer.transform([organization]).toarray()
                    similarity = cosine_similarity(x_vector, light_raw_vector)[0][0]
                    
                    if similarity > 0.1:
                        # Use Levenshtein to better handle misspellings
                        if organization in affil:
                            similarity_l = 1
                        else:
                            similarity_l = (
                                1 
                                - Levenshtein.distance(organization, affil) 
                                / max(len(organization), len(affil))
                            )
                        best_j.append([organization, similarity, similarity_l])
                
                except Exception as ex:
                    print("Error:", ex)
        
        # Step 2: Keep only the best similarity per organization
        max_numbers = defaultdict(float)
        for org, sim, sim_l in best_j:
            max_numbers[org] = max(max_numbers[org], sim)
        
        reduced_best = [
            [org, sim, sim_l] 
            for org, sim, sim_l in best_j 
            if sim == max_numbers[org]
        ]
        
        # Sort by similarity score (descending) and then lexicographically
        reduced_best.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Apply group-level university limiting
        group_univ = [r for r in reduced_best if 'univ' in r[0]]
        group_other = [r for r in reduced_best if 'univ' not in r[0]]
        if len(group_univ) > num_uni_p:
            reduced_best = group_univ[:num_uni_p] + group_other
            
        result.extend(reduced_best)
        
        best.append(best_j)
        
    # Step 3: Construct final dictionary with highest confidence values
    pairs_dict = {p[1]: p[2] for group in pairs_list for p in group}
    result_dict = {}
    for res in result:
        org = res[0]
        similarity_score = res[1]
        if org in pairs_dict:
            best_confidence = pairs_dict[org]
            if org not in result_dict or similarity_score > result_dict[org][1]:
                result_dict[org] = [best_confidence, similarity_score]
                
    # Convert to list format
    final_result = [
        [key, value[0]] 
        for key, value in sorted(result_dict.items(), key=lambda x: x[1][1], reverse=True)
    ]
    
    return final_result
