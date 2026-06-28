from affro.helpers.functions import *
from affro.helpers.create_input import *
from affro.helpers.matching  import *


def find_name(input, dix_name, simU, simG, limit):
    # print('start find_name')
    # print('input',input)
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
    keys_list = input[4]
  
    dix = {}    # will store indeces and legalnames of organizations of the DOI { i : [legalname1, legalname2,...]}
    result = {}
    pairs = []
 
    keywords =  [entry["keywords"].replace(' gmbh', ' ').strip() for entry in df_list] 

    candidates = get_candidates(countries_list, keys_list)
    
    # print('candidates found for keywords:', len(candidates))
    if len(keywords) > 1 or len(keywords) == 1 and len(keywords[0])>1:
        for k,s in enumerate(keywords):
            if len(s) >1 and s not in countries:
                pairs_k = []
                # print(s)          
        #--end september 2025
                if s in candidates:
                    # print('lucky', s)
                    pairs_k.append((s,s,1, dix_name[s][0]['id'],dix_name[s][0]['country']))
                    if k not in dix:
                        dix[k] = [s]
                    else:
                        dix[k].append(s)
                        
                else:
            # else: 
                    # print('not lucky')  
                    
                    try:         
                        pairs_k = find_candidate(s, k , dix,  simU, simG, candidates, limit)
                    except:
                        pairs_k = []
                result[k] = pairs_k
                if len(pairs_k)>0:
                    pairs.append(pairs_k)
                # else:
                #     other_candidates = candidates_-candidates
                #     if s in other_candidates:
                #         # print('lucky', s)
                #         pairs_k.append((s,s,1, dix_name[s][0]['id'],dix_name[s][0]['country']))
                #         if k not in dix:
                #             dix[k] = [s]
                #         else:
                #             dix[k].append(s)
                            
                #     else:
                # # else: 
                #         # print('not lucky')  
                        
                #         try:         
                #             pairs_k = find_candidate(s, k , dix,  simU, simG, other_candidates, limit)
                #         except:
                #             pairs_k = []
                #     result[k] = pairs_k
                #     if len(pairs_k)>0:
                #         pairs.append(pairs_k)
                
    # print('pairs', pairs)
    multi = index_multiple_matchings(pairs)
    # print('multi', multi)
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
        except Exception as e:
            print('ERROR, find_name', e)
            pass
 
    pairs_check = [ pair for pair in pairs if pair[0][0] in need_check_keys ]
    # print('pairs_check',pairs_check)
    if len(need_check_keys)>0:
        # print(' len(need_check_keys)', len(need_check_keys))
        best0 =  best_sim_score(clean_aff, light_aff, len(keywords), pairs_check, multi, simU, simG)
        # print('best0', best0)
        best1 = {x[0]:dix_name[x[0]][0]['id'] for x in best0 }
        # print('best1', best1)

        best01 = unique_subset(best0, best1)
        best = best01 + ready_best
    else:
        best = ready_best
    # print('end find_name', best) 
    return best
