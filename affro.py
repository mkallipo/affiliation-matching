import sys 
##import functions
from functions import *
from matching import *
from create_input import *
import json

path_dict = "dictionaries/"
#path_dict = ""
#version = '_jan24'
#version = '_apr25_pub'

dict_org_ror = load_json(path_dict + 'dict_acad'+version+'.json')
dict_mult_ror = load_json(path_dict + 'dict_mult'+version+'.json')
dict_city_ror = load_json(path_dict + 'dict_city'+version+'.json')
dict_country_ror = load_json(path_dict + 'dict_country'+version+'.json')
dict_org_oaire = load_json(path_dict + 'dict_acad_oaire.json')
dict_mult_oaire = load_json(path_dict + 'dict_mult_oaire.json')
dict_city_oaire = load_json(path_dict + 'dict_city_oaire.json')
dict_country_oaire = load_json(path_dict + 'dict_country_oaire.json')
dict_status = load_json(path_dict + 'dict_status'+version+'.json')
#dict_grids = load_json('dictionaries/dict_grids_rors.json')
dict_id_country_ror = load_json(path_dict + 'dict_id_country.json')
dict_id_country_oaire = load_json(path_dict + 'dict_id_country_oaire.json')

dict_country_legalnames = load_json(path_dict + 'dict_country_legalnames'+version+'.json')
dict_org = dict(dict_org_ror)  
dict_org.update(dict_org_oaire)

dict_mult = dict(dict_mult_ror)  
dict_mult.update(dict_mult_oaire)

dict_city = dict(dict_city_ror)  
dict_city.update(dict_city_oaire)

dict_country = dict(dict_country_ror)  
dict_country.update(dict_country_oaire)



dict_id_country_nc = dict(dict_id_country_ror)  
dict_id_country_nc.update(dict_id_country_oaire)

# dict_mult = dict_mult_ror | dict_mult_oaire
# dict_country = dict_country_ror | dict_country_oaire
# dict_city = dict_city_ror | dict_city_oaire
# dict_id_country_nc = dict_id_country_ror | dict_id_country_oaire
dict_id_country = {x:remove_stop_words(replace_double_consonants(dict_id_country_nc[x])) for x in list(dict_id_country_nc.keys())}


#dict_org1 = {x.replace('clinique', 'center').replace('centers', 'center') : dict_org[x] for x in dict_org}

# dict_mult1 = {x.replace('clinique', 'center').replace('centers', 'center') : dict_mult[x] for x in dict_mult}
# dict_city1 = {x.replace('clinique', 'center').replace('centers', 'center') : dict_city[x] for x in dict_city}
# dict_country1 = {x.replace('clinique', 'center').replace('centers', 'center') : dict_country[x] for x in dict_country}

dict_status_new = {k :[dict_status[k][0], dict_status[k][1].split(', ')] for k in dict_status}


def find_ror_new(input, simU, simG, limit):
    light_aff = input[0]
    result = Aff_Ids(input, dict_org, dict_mult, dict_city, dict_country, simU, simG, limit)        
 #   print('res', result)
    results_upd = []
    
    for r in result:
         
        if  "openorgs" in r[2]:
            results_upd.append([r[1], 'OpenOrgs', r[2], 'active'])
            
        else:
            if  dict_status_new[r[2]][0] == 'active':
                results_upd.append([r[1], 'ROR', r[2], 'active'])
            else:
                if dict_status_new[r[2]][1][0] == '':
                    results_upd.append([r[1], 'ROR', r[2], dict_status_new[r[2]][0]])
                
                # elif len(dict_status[r[2]][1]) == 1:
                        
                #         results_upd.append([r[1], 'ROR', r[2], dict_status[r[2]][0]])

                #         results_upd.append([r[1], 'ROR', dict_status[r[2]][1][0], 'active'])
                        
                else:
                    results_upd.append([r[1], 'ROR', r[2], dict_status_new[r[2]][0]])
                    for link in (dict_status_new[r[2]][1]):
                        results_upd.append([r[1], 'ROR', link, 'active'])
     
  #  print('results_upd',results_upd)     
    if len(results_upd) > len(set(description(light_aff)[1])):

        final_matching = []
        light_aff_tokens = set(light_aff.split())

        for id_ in results_upd:
            country = dict_id_country[id_[2]]
   #         print(id_, country)


            if country == 'united states':
                if 'united states' in light_aff or 'usa' in light_aff_tokens:
                    final_matching.append(id_)

            elif country == 'united kingdom':
                if 'united kingdom' in light_aff or 'uk' in light_aff_tokens:
                    final_matching.append(id_)
            
            elif 'korea' in country:
          
                if 'korea' in light_aff_tokens:
                    final_matching.append(id_)

            elif country in light_aff:
                final_matching.append(id_)

            
        if len(final_matching)>0:
            result_dict =  [{'Provenance': 'AffRo', 'PID':'OpenOrgs', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} if "openorgs" in x[2] else {'Provenance': 'AffRo', 'PID':'ROR', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} for x in final_matching]
            return result_dict
        else:

            return  [{'Provenance': 'AffRo', 'PID':'OpenOrgs', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} if "openorgs" in x[2] else {'Provenance': 'AffRo', 'PID':'ROR', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} for x in results_upd]
        
    elif len(results_upd)>0:
        return  [{'Provenance': 'AffRo', 'PID':'OpenOrgs', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} if "openorgs" in x[2] else {'Provenance': 'AffRo', 'PID':'ROR', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} for x in results_upd]
    else:
        result_dict =  []

    return result_dict

    
def affro(raw_aff_string):
    try:
        result = find_ror_new(create_df_algorithm(raw_aff_string, 4, 'True'), 0.55, 0.875, 500)
        return result
    except Exception as e:
        # Return some indication of an error, or log the row
        print(f"Error: {str(e)}")
        print(raw_aff_string)
        pass
    


def affro_config_pub(raw_aff_string,  rad_u, sim_u, sim_g, specific):
    lucky_guess = clean_string_ror(raw_aff_string) 
    if lucky_guess in dict_org:
        if dict_mult[lucky_guess] == "unique":
            if 'OpenOrgs' in dict_org[lucky_guess]:
                return [{'Provenance': 'AffRo', 'PID': 'OpenOrgs', 'Value': dict_org[lucky_guess], 'Confidence': 1, 'Status': 'active'}]
            else:
                if dict_status_new[dict_org[lucky_guess]][0] == 'active':
                    return [{'Provenance': 'AffRo', 'PID': 'ROR', 'Value': dict_org[lucky_guess], 'Confidence': 1, 'Status': 'active'}]
                elif dict_status_new[dict_org[lucky_guess]][1] == '':
                    return [{'Provenance': 'AffRo', 'PID': 'ROR', 'Value': dict_org[lucky_guess], 'Confidence': 1, 'Status': dict_status_new[dict_org[lucky_guess]][0]}]
                else:
                    res = [{'Provenance': 'AffRo', 'PID' : 'ROR', 'Value': dict_org[lucky_guess], 'Confidence': 1, 'Status': dict_status_new[dict_org[lucky_guess]][0]}]
                    for successor in  dict_status_new[dict_org[lucky_guess]][1]:
                        res.append({'Provenance': 'AffRo', 'PID' : 'ROR', 'Value': successor, 'Confidence': 1, 'Status': 'active'})
                    return res
        else:
            cand_ids = [x[1] for x in dict_city_ror[lucky_guess]  if dict_status_new[x[1]][0] == 'active']
    #        print('cand_ids', cand_ids)
            if len(cand_ids) == 1:
                if 'OpenOrgs' in dict_org[lucky_guess]:
                    return [{'Provenance': 'AffRo', 'PID': 'OpenOrgs', 'Value': dict_org[lucky_guess], 'Confidence': 1, 'Status': 'active'}]
                else:
                    return [{'Provenance': 'AffRo', 'PID': 'ROR', 'Value': dict_org[lucky_guess], 'Confidence': 1, 'Status': 'active'}]
                
            else:
                return []

    else:
        try:
            
            result = find_ror_new(create_df_algorithm(raw_aff_string, rad_u, specific), sim_u, sim_g, 500)
            
            return result
        except Exception as e:
            # Return some indication of an error, or log the row
            print(f"Error: {str(e)}")
            print(raw_aff_string)
            pass
        



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python affro_spark.py <string> <float1> <float2>")
        sys.exit(1)

    string_arg = sys.argv[1]
   # float_arg1 = float(sys.argv[2])
   # float_arg2 = float(sys.argv[3])

    print(affro(string_arg))
    
    
