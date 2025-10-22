##import functions
import sys
from helpers.functions import *
from helpers.matching import *
from helpers.create_input import *
from helpers.disambiguation import *


dix_id = load_json('jsons/dix_id.json')
dix_name = load_json('jsons/dix_name.json')


def produce_result(input, simU, simG, limit):
    best_name = find_name(input, dix_name, simU, simG, limit)
    id_result = find_id(input, best_name, dix_name)
    result = disamb(input, id_result, dix_id)

    return result

    
def run_affro(raw_aff_string):
    lucky_guess = clean_string_ror(raw_aff_string) 
    try:
        if lucky_guess in dix_name:
            if len(dix_name[lucky_guess]) == 1:
                id_ =  dix_name[lucky_guess][0]['id']
                name_ =  dix_id[id_]['name']
                country_ =  dix_id[id_]['country']
                status_ = dix_id[id_]['status']
                if 'openorgs' in id_:
                            
                    return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'openorgs', 'value': id_,  'name': name_, 'confidence': 1, 'status': 'active',  'country': country_}]
                else:
                    if status_[0] == 'active':
                        return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'ror', 'value': id_, 'name': name_, 'confidence': 1, 'status': 'active',  'country': country_}]
                    elif status_[0]== '':
                        return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'ror', 'value':id_, 'name': name_, 'confidence': 1, 'status': status_[0],  'country': country_}]
                    else:
                        res = [{'provenance': 'affro', 'version' : VERSION, 'pid' : 'ror', 'value': id_, 'name': name_, 'confidence': 1, 'status': status_[0],  'country': country_}]
                        for successor in  status_[1]:
                            if successor != '':
                                res.append({'provenance': 'affro', 'version' : VERSION, 'pid' : 'ror', 'value': successor, 'name': dix_id[successor]['name'], 'confidence': 1, 'status': 'active',  'country':dix_id[successor]['name']})
                        return res
            else:
                cand_ids = [
                    key
                    for key in [x['id'] for x in  dix_name[lucky_guess]]
                    if ("ror" in key and dix_id[key]['status'][0] == "active") or ("openorgs" in key)
                ]

                if len(cand_ids) == 1:# or num_countries == 1:
                    id_ = dix_name[lucky_guess][0]['id']
                    name_ =  dix_id[id_]['name']
                    country_ =  dix_id[id_]['country']
                    status_ = dix_id[id_]['status']
                    if 'openorgs' in id_:
                        return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'openorgs', 'value': id_, 'name': name_, 'confidence': 1, 'status': 'active', 'country': country_}]
                    else:
                        return [{'provenance': 'affro', 'version' : VERSION, 'pid': 'ror', 'value': id_, 'name': name_, 'confidence': 1, 'status': 'active', 'country':country_}]
                    
                else:
                    return []
        else:
            result = produce_result(create_df_algorithm(raw_aff_string, 3), 0.42, 0.82, 500)

            return result

    except Exception as e:
        # Return some indication of an error, or log the row
        print(f"Error end: {str(e)}")
        print(raw_aff_string)
        pass
    

        
if __name__ == "__main__":
    print(run_affro(sys.argv[1]))