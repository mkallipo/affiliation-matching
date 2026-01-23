##import functions
import sys
from helpers.functions import *
from helpers.create_input import *
from helpers.matching import *
from helpers.find_name import *
from helpers.find_id import *
from helpers.disambiguation import *



dix_id = load_json('jsons/dix_id.json.gz')
dix_name = load_json('jsons/dix_name.json.gz')

def produce_result(input, simU, simG, limit):
    best_name = find_name(input, dix_name, simU, simG, limit)
    id_result = find_id(input, best_name, dix_name)
    result = disamb(input, id_result, dix_id)

    return result

    
def build_result_list(id_, name_, country_, status_):
    """
    Helper function to build the result list, reducing code duplication.
    """
    if 'openorgs' in id_:
        return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'openorgs', 'value': id_,  'name': name_, 'confidence': 1, 'status': 'active',  'country': country_}]
    else:
        if status_[0] == 'active':
            # print('active')
            return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'ror', 'value': id_, 'name': name_, 'confidence': 1, 'status': 'active',  'country': country_}]
        elif status_[0]== '':
            return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'ror', 'value':id_, 'name': name_, 'confidence': 1, 'status': status_[0],  'country': country_}]
        else:
            res = [{'provenance': 'affro', 'version' : VERSION, 'pid' : 'ror', 'value': id_, 'name': name_, 'confidence': 1, 'status': status_[0],  'country': country_}]
            for successor in  status_[1]:
                if successor != '':
                    res.append({'provenance': 'affro', 'version' : VERSION, 'pid' : 'ror', 'value': successor, 'name': dix_id[successor]['name'], 'confidence': 1, 'status': 'active',  'country':dix_id[successor]['country']})
            return res

def run_affro(raw_aff_string):
    lucky_guess = clean_string_lucky(raw_aff_string) 
    # print(lucky_guess)
    try:
        if lucky_guess in dix_name:
            # print('lucky guess hit', lucky_guess)
            # print('lucky guess found', dix_name[lucky_guess])
            if len(dix_name[lucky_guess]) == 1:
                id_ =  dix_name[lucky_guess][0]['id']
                name_ =  dix_id[id_]['name']
                country_ =  dix_id[id_]['country']
                status_ = dix_id[id_]['status']
                return build_result_list(id_, name_, country_, status_)
            else:
                # print('multiple candidates')
                ids = [x['id'] for x in dix_name[lucky_guess]]
                cand_ids = [id for id in ids if is_first(id, lucky_guess) == 'y']
                # print('cand_ids', cand_ids)
            # pick the ror id where 'first' == 'y' (None if not found)
                if len(cand_ids) !=1:
                    # print('secondary conditions')
                    conditions = [
                    lambda key: ("ror" in key and dix_id[key]['status'][0] == "active"
                                and dix_id[key]['top_level'][0] == 'y') \
                                or ("openorgs" in key),

                    lambda key: ("ror" in key and dix_id[key]['status'][0] == "active"
                                and dix_id[key]['parent'][0] == 'y') \
                                or ("openorgs" in key),

                    lambda key: ("ror" in key and dix_id[key]['status'][0] == "active") \
                                or ("openorgs" in key)
                                ]

                    for cond in conditions:
                        cand_ids = [key for key in ids if cond(key)]
                        if cand_ids:
                            # print('break')
                            break
                        
                        if len(cand_ids) == 0:
                            # print('check result')
                            result = produce_result(create_df_algorithm(raw_aff_string, 10), 0.42, 0.82, 500)

                            return result

                # print('cand_ids',cand_ids)
                if len(cand_ids) == 1:# or num_countries == 1:
                    id_ = cand_ids[0]
                    # print('id',id_)
                    name_ =  dix_id[id_]['name']
                    country_ =  dix_id[id_]['country']
                    status_ = dix_id[id_]['status']
                    return build_result_list(id_, name_, country_, status_)
                
                else: 
                    found = False
                    for triplet in dix_name[lucky_guess]:
                        if triplet['first'] == 'y':
                            found = True
                            id_ = triplet['id']
                            name_ =  dix_id[id_]['name']
                            country_ =  dix_id[id_]['country']
                            status_ = dix_id[id_]['status']
                            return build_result_list(id_, name_, country_, status_)
                        
                    if found == False:
                        return []
        else:
            # print('lucky guess miss')
            result = produce_result(create_df_algorithm(raw_aff_string, 3), 0.42, 0.82, 500)

            return result

    except Exception as e:
        # Return some indication of an error, or log the row
        print(f"Error end: {str(e)}")
        print(raw_aff_string)
        pass
    

        
if __name__ == "__main__":
    print(run_affro(sys.argv[1]))
