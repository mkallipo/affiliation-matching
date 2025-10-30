from .functions import *
#from .create_input import *
from .__init__ import VERSION

    
us_states = [
    "alabama", "alaska", "arizona", "arkansas", "california",
    "colorado", "conecticut", "delaware", "florida", "georgia",
    "hawaii", "idaho", "ilinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland",
    "masachusets", "michigan", "minesota", "misisipi", "misouri",
    "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pensylvania", "rhode island", "south carolina",
    "south dakota", "tennesee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming"
]


def contains_us_state(text):
    text = text.lower()
    return any(state in text for state in us_states)

# def get_city(name, dix_name):
#     return {x['city'] : x['id'] for x in dix_name[name]}


# weak_keywords = ['department']

def disamb(input, id_list_,dix_id):
    clean_aff = input[0]

    results_upd = []
    
    for r in id_list_:
         
        if  "openorgs" in r[2]:
            results_upd.append([r[1], 'openorgs', r[2], 'active', dix_id[r[2]]['country']])
            
        else:
            if  dix_id[r[2]]['status'][0] == 'active':
                results_upd.append([r[1], 'ror', r[2], 'active', dix_id[r[2]]['country']])
            else:
                if dix_id[r[2]]['status'][1][0] == '':
                    results_upd.append([r[1], 'ror', r[2], dix_id[r[2]]['status'][0], dix_id[r[2]]['country']])
                        
                else:
                    results_upd.append([r[1], 'ror', r[2], dix_id[r[2]]['status'][0], dix_id[r[2]]['country']])
                    for link in (dix_id[r[2]]['status'][1]):
                        results_upd.append([r[1], 'ror', link, 'active',dix_id[r[2]]['country'],dix_id[link]['country']])
     
    if len(results_upd) > len(set(description(clean_aff)[1])):
        # print('more results than countries')
        final_matching = []
        light_aff_tokens = [clean_string_ror(x) for x in set(clean_aff.split())]
        for id_ in results_upd:
            country = dix_id[id_[2]]['country']
            if country == 'united states':
                if 'united states' in clean_aff or 'usa' in light_aff_tokens or contains_us_state(clean_aff):
                    final_matching.append(id_)

            elif country == 'united kingdom':
                if 'united kingdom' in clean_aff or 'uk' in light_aff_tokens:
                    final_matching.append(id_)
            
            elif 'korea' in country:
          
                if 'korea' in light_aff_tokens:
                    final_matching.append(id_)

            elif country in clean_aff:
                final_matching.append(id_)
                    
            
        if len(final_matching)>0:
                
            result_dict = [{'provenance': 'affro', 'version': VERSION,  'pid':'openorgs', 'value':x[2], 'name': dix_id[x[2]]['name'], 'confidence':min(x[0],1), 'status':x[3], 'country': dix_id[x[2]]['country']} if "openorgs" in x[2] else {'provenance': 'affro', 'version': VERSION,'pid':'ror', 'value':x[2], 'name': dix_id[x[2]]['name'], 'confidence':min(x[0],1), 'status':x[3], 'country': dix_id[x[2]]['country']} for x in final_matching]
            return result_dict
        
        else:
            result_dict = [{'provenance': 'affro', 'version': VERSION,  'pid':'openorgs', 'value':x[2], 'name': dix_id[x[2]]['name'],'confidence':min(x[0],1), 'status':x[3], 'country': dix_id[x[2]]['country']} if "openorgs" in x[2] else {'provenance': 'affro', 'version': VERSION, 'pid':'ror', 'value':x[2],  'name': dix_id[x[2]]['name'], 'confidence':min(x[0],1), 'status':x[3],  'country': dix_id[x[2]]['country']} for x in results_upd]
            return result_dict

    elif len(results_upd)>0:
        result_dict = [{'provenance': 'affro', 'version': VERSION,  'pid':'openorgs', 'value':x[2], 'name': dix_id[x[2]]['name'], 'confidence':min(x[0],1), 'status':x[3], 'country': dix_id[x[2]]['country']} if "openorgs" in x[2] else {'provenance': 'affro', 'version': VERSION, 'pid':'ror', 'value':x[2],  'name': dix_id[x[2]]['name'],  'confidence':min(x[0],1), 'status':x[3],  'country': dix_id[x[2]]['country']} for x in results_upd]
        return result_dict
    else:
        return  []
        