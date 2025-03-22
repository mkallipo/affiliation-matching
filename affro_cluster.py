import sys 
##import functions
from functions_cluster import *
from matching_cluster import *
from create_input_cluster import *
import json

path_dict = "dictionaries/"
#path_dict = ""

dix_org = load_json(path_dict + 'dix_acad.json')
dix_mult = load_json(path_dict + 'dix_mult.json')
dix_city = load_json(path_dict + 'dix_city.json')
dix_country = load_json(path_dict + 'dix_country.json')
# dix_org_oaire = load_json(path_dict + 'dix_acad_oaire.json')
# dix_mult_oaire = load_json(path_dict + 'dix_mult_oaire.json')
# dix_country_oaire = load_json(path_dict + 'dix_country_oaire.json')
dix_status = load_json(path_dict + 'dix_status.json')
#dix_grids = load_json('dictionaries/dix_grids_rors.json')
dix_id_country = load_json(path_dict + 'dix_id_country.json')
#dix_org1 = {x.replace('clinique', 'center').replace('centers', 'center') : dix_org[x] for x in dix_org}

# dix_mult1 = {x.replace('clinique', 'center').replace('centers', 'center') : dix_mult[x] for x in dix_mult}
# dix_city1 = {x.replace('clinique', 'center').replace('centers', 'center') : dix_city[x] for x in dix_city}
# dix_country1 = {x.replace('clinique', 'center').replace('centers', 'center') : dix_country[x] for x in dix_country}

dix_status_new = {k :[dix_status[k][0], dix_status[k][1].split(', ')] for k in dix_status}


def find_ror(input, simU, simG):
    result = Aff_Ids(input, dix_org, dix_mult, dix_city, dix_country, simU, simG)    
    results_upd = []
    for r in result:
       
        if  dix_status[r[2]][0] == 'active':
            results_upd.append([r[1], 'ROR', r[2], 'active'])
        else:
            if dix_status[r[2]][1] == '':
                results_upd.append([r[1], 'ROR', r[2], dix_status[r[2]][0]])
            else:

                results_upd.append([r[1], 'ROR', r[2], dix_status[r[2]][0]])

                results_upd.append([r[1], 'ROR', dix_status[r[2]][1], 'active'])
    
        
    if len(results_upd)>0:
        result_dict =  [{'Provenance': 'AffRo', 'PID':'ROR', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} for x in results_upd]
    else:
        result_dict =  []

    return result_dict



def find_ror_new(input, simU, simG, limit):
    light_aff = input[0]
    result = Aff_Ids(input, dix_org, dix_mult, dix_city, dix_country, simU, simG, limit)    
    #print('RES', result)
    results_upd = []
    for r in result:
        if  dix_status_new[r[2]][0] == 'active':
            results_upd.append([r[1], 'ROR', r[2], 'active'])
        else:
            if dix_status_new[r[2]][1][0] == '':
                results_upd.append([r[1], 'ROR', r[2], dix_status_new[r[2]][0]])
            
            # elif len(dix_status[r[2]][1]) == 1:
                    
            #         results_upd.append([r[1], 'ROR', r[2], dix_status[r[2]][0]])

            #         results_upd.append([r[1], 'ROR', dix_status[r[2]][1][0], 'active'])
                    
            else:
                results_upd.append([r[1], 'ROR', r[2], dix_status_new[r[2]][0]])
                for link in (dix_status_new[r[2]][1]):
                    results_upd.append([r[1], 'ROR', link, 'active'])

    if  len(results_upd) > len(set(description(light_aff)[1])):
        final_matching = []
        for id_ in results_upd:
            if dix_id_country[id_[2]] == 'united states':
                if  dix_id_country[id_[2]] in light_aff or 'usa' in light_aff:
                    final_matching.append(id_)
            elif dix_id_country[id_[2]] == 'united kingdom':
                if dix_id_country[id_[2]] in light_aff or 'uk' in light_aff:
                    final_matching.append(id_)
            elif  dix_id_country[id_[2]] in light_aff:
                    final_matching.append(id_)
    
            
        if len(final_matching)>0:
            result_dict =  [{'Provenance': 'AffRo', 'PID':'ROR', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} for x in final_matching]
            return result_dict
        else:

            return  [{'Provenance': 'AffRo', 'PID':'ROR', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} for x in results_upd]
        
    elif len(results_upd)>0:
        return  [{'Provenance': 'AffRo', 'PID':'ROR', 'Value':x[2], 'Confidence':x[0], 'Status':x[3]} for x in results_upd]
    else:
        result_dict =  []

    return result_dict

    
def affro(raw_aff_string):
    try:
        result = find_ror_new(create_df_algorithm(raw_aff_string, 4), 0.55, 0.875, 500)
        return result
    except Exception as e:
        # Return some indication of an error, or log the row
        print(f"Error: {str(e)}")
        print(raw_aff_string)
        pass
    

def affro_config(raw_aff_string,  rad_u, sim_u, sim_g, limit):
    try:
        aff_string = create_df_algorithm(raw_aff_string, rad_u)
        result = find_ror_new(aff_string, sim_u, sim_g, limit)
        return result
    except Exception as e:
        # Return some indication of an error, or log the row
        print(f"Error: {str(e)}")
        print(raw_aff_string)
        pass


    
def matchings_affro(aff_string):
   # global operation_counter
    try:
        matchings = affro(aff_string)
   #     operation_counter += 1

        # Ensure matchings is a list, even if affro returns a single dict
        if not isinstance(matchings, list):
            matchings = [matchings]

        # Create the result as a tuple that matches matchings_schema
        result = []
        for matching in matchings:
        # Assuming 'matching' is a dictionary that contains 'Provenance', 'PID', 'Value', 'Confidence', 'Status'
            result.append((
                matching.get("Provenance", None),
                matching.get("PID", None),
                matching.get("Value", None),
                float(matching.get("Confidence", None)),
                matching.get("Status", None)
            ))
        if len(result)>0:
            return result
        

    except Exception as e:
        print(f"Error processing affiliation string {aff_string}: {str(e)}")
        return ()
    
    
       


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python affro_spark.py <string> <float1> <float2>")
        sys.exit(1)

    string_arg = sys.argv[1]
   # float_arg1 = float(sys.argv[2])
   # float_arg2 = float(sys.argv[3])

    print(affro(string_arg))
    
    
