import sys 
##import functions
from affro.helpers.functions import *
from affro.helpers.matching import *
from affro.helpers.create_input import *
from affro.helpers.find_name import *
from affro.helpers.find_id import *
from affro.helpers.disambiguation import *
from affro.helpers.direct_mapping import *

from . import __version__

VERSION = __version__


dix_id = load_json('jsons/dix_id.json.gz')
dix_name = load_json('jsons/dix_name.json.gz')


def produce_result(input, simU, simG, limit):
    best_name = find_name(input, dix_name, simU, simG, limit)
    id_result = find_id(input, best_name, dix_name, simG)
    result = disamb(input, id_result, dix_id)

    return result

def _make_entry(pid, value, name, confidence, status, country):
    """Build a single result dictionary."""
    return {
        'provenance': 'affro',
        'version': VERSION,
        'pid': pid,
        'value': value,
        'name': name,
        'confidence': confidence,
        'status': status,
        'country': country,
    }

    
def build_result_list(id_, name_, country_, status_):
    """
    Helper function to build the result list, reducing code duplication.
    """
    pid = 'openorgs' if 'openorgs' in id_ else 'ror'

    # For openorgs or active ROR entries, return a single active entry
    if 'openorgs' in id_ or status_[0] == 'active':
        return [_make_entry(pid, id_, name_, 1, 'active', country_)]

    # Build primary entry with its current status
    res = [_make_entry(pid, id_, name_, 1, status_[0], country_)]

    # Append active successors (if any)
    if len(status_) > 1:
        for successor in status_[1]:
            if successor != '':
                res.append(_make_entry(
                    'ror', successor,
                    dix_id[successor]['name'], 1,
                    'active', dix_id[successor]['country'],
                ))
    return res


def _apply_secondary_conditions(ids):
    """
    Apply progressive filtering conditions to find best candidate.
    Optimized version: Pre-fetches dictionary entries to avoid repeated O(N) access.
    """
    # Separate openorgs immediately (they bypass all ror logic)
    openorgs = [k for k in ids if 'openorgs' in k]
    
    # Pre-fetch active rors once to avoid heavy dictionary spam
    active_rors = [k for k in ids if 'ror' in k and dix_id[k]['status'][0] == 'active']
    
    if openorgs:
        active_top = [k for k in active_rors if dix_id[k]['top_level'][0] == 'y']
        return openorgs + active_top

    if not active_rors:
        return []
        
    # Condition 1: Check Top level
    top_level = [k for k in active_rors if dix_id[k]['top_level'][0] == 'y']
    if top_level: 
        return top_level
        
    # Condition 2: Check Parents
    parents = [k for k in active_rors if dix_id[k]['parent'][0] == 'y']
    if parents: 
        return parents
        
    # Condition 3: Return any active rors
    return active_rors

        

def run_affro_(raw_aff_string):
    """
    Optimized version of run_affro with better performance.
    
    Optimizations:
    - Cache lucky_guess and dix_name lookups to avoid redundant access
    - Reuse candidate lists instead of recalculating
    - Streamline conditional logic
    - Improve final loop efficiency
    """
    
    lucky_guess = clean_string_lucky(raw_aff_string)
    
    try:
        # Check if lucky_guess exists in dix_name
        if lucky_guess not in dix_name:
            # Lucky guess miss: use algorithm fallback
            result = produce_result(create_df_algorithm(raw_aff_string, 3), 0.42, 0.82, 500)
            return result
        
        # Cache the dix_name entry to avoid repeated lookups
        # print('lucky')
        lucky_match = dix_name[lucky_guess]
        
        # Single exact match found
        if len(lucky_match) == 1:
            triplet = lucky_match[0]
            id_ = triplet['id']
            name_ = dix_id[id_]['name']
            country_ = dix_id[id_]['country']
            status_ = dix_id[id_]['status']
            return build_result_list(id_, name_, country_, status_)
        
        # -------------------------------------------------------------
        # Multiple candidates: filter natively
        # -------------------------------------------------------------
        ids = [x['id'] for x in lucky_match]
        
        # Local helper to avoid repeating the dictionary lookups and return logic
        def get_result(best_id):
            return build_result_list(
                best_id, 
                dix_id[best_id]['name'], 
                dix_id[best_id]['country'], 
                dix_id[best_id]['status']
            )

        # 1. Country Prioritization: If country is mentioned in lucky_guess, prioritize those candidates
        country_match_ids = [
            i for i in ids 
            if any(c and str(c) in lucky_guess for c in dix_id[i].get('country', []))
        ]
        
        if len(country_match_ids) == 1:
            return get_result(country_match_ids[0])
            
        # If there are multiple country matches, or NO country matches, restrict further checks
        working_ids = country_match_ids if country_match_ids else ids
        
        # 1.5 Exact Name Prioritization: If raw_aff_string matches the institution name exactly (case-insensitive)
        name_match_ids = [
            i for i in working_ids 
            if raw_aff_string.strip().lower() == dix_id[i].get('name', '').strip().lower()
        ]
        
        if len(name_match_ids) == 1:
            return get_result(name_match_ids[0])
            
        working_ids = name_match_ids if name_match_ids else working_ids
        
        # 2. Filter for 'first' == 'y' among the working_ids
        first_y_ids = [x['id'] for x in lucky_match if x.get('first') == 'y' and x['id'] in working_ids]
        
        if len(first_y_ids) == 1:
            return get_result(first_y_ids[0])
        
        # 3. Apply secondary conditions
        candidates_to_filter = first_y_ids if len(first_y_ids) > 1 else working_ids
        cand_ids = _apply_secondary_conditions(candidates_to_filter)
        
        # 4. If no candidates remain, fall back to algorithm
        if not cand_ids:
            return produce_result(create_df_algorithm(raw_aff_string, 10), 0.42, 0.82, 500)
        
        # 5. If EXACTLY one remains after secondary conditions, return it
        if len(cand_ids) == 1:
            return get_result(cand_ids[0])
        
        # 6. Multiple candidates STILL remain after secondary conditions.
        # If the affiliation string is a University, we are allowed to pick a best-effort result
        if 'university' in lucky_guess:
            for c_id in cand_ids:
                if c_id in first_y_ids:
                    return get_result(c_id)
            return get_result(cand_ids[0])
            
        # To avoid making a blind guess between identical ties for other institutions, return no result.
        return []

    except Exception as e:
        print(f"Error in run_affro: {str(e)}")
        print(f"Input: {raw_aff_string}")
        return []

def run_affro(aff):
#    lucky_guess = clean_string_lucky(aff)
    direct = direct_mapping(aff)
    if not direct[0]:      
        return run_affro_(aff)
    else:
        combined = direct[0] + run_affro_(direct[1])
        # Deduplicate by 'value' (ROR ID), keeping first occurrence
        seen = set()
        deduped = []
        for entry in combined:
            if entry['value'] not in seen:
                seen.add(entry['value'])
                deduped.append(entry)
        return deduped
        
    
def matchings_affro(aff_string):
   # global operation_counter
    try:
        matchings = run_affro(aff_string)
   #     operation_counter += 1

        # Ensure matchings is a list, even if affro returns a single dict
        if not isinstance(matchings, list):
            matchings = [matchings]

        # Create the result as a tuple that matches matchings_schema
        result = []
        for matching in matchings:
        # Assuming 'matching' is a dictionary that contains 'provenance', 'affro', 'value', 'confidence', 'status'
            result.append((
                matching.get("provenance", None),
                matching.get("version", None),
                matching.get("pid", None),
                matching.get("value", None),
                matching.get("name", None),
                float(matching.get("confidence", None)),
                matching.get("status", None),
                matching.get("country", None)
            ))
        if len(result)>0:
            return result
        

    except Exception as e:
        print(f"Error processing affiliation string {aff_string}: {str(e)}")
        return ()
    
    
    
