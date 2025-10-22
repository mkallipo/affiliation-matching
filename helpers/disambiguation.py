from .functions import *
from .create_input import *
from .__init__ import VERSION

specific = [k for k in categ_dicts if categ_dicts[k] == 'Specific' or  categ_dicts[k] == 'Acronyms']


country_synonyms = {
    "united states": ["united states", "u.s.a.", "usa", "usa."],
    "germany": ["germany","deutschland"],
    "united kingdom": ["united kingdom", "u.k.", "uk", "uk."],
    "turkey": ["turkey","turkiye"],
}
    
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


country_synonyms = {x: [x] for x in countries}
country_synonyms["united states"] = ["united states", "u.s.a.", "usa", "usa."]
country_synonyms["germany"] = ["germany","deutschland"]
country_synonyms["united kingdom"] = ["united kingdom", "u.k.", "uk", "uk."]
country_synonyms["turkey"] = ["turkey","turkiye", "cyprus"]
    


def contains_us_state(text):
    text = text.lower()
    return any(state in text for state in us_states)

def get_city(name, dix_name):
    return {x['city'] : x['id'] for x in dix_name[name]}
    
    
def keep_highest_url(lst):
    best = {}

    for item in lst:
        name, score, url = item
        if name not in best or url > best[name][2]:  # Keep the highest URL
            best[name] = item  # Store the full entry

    return list(best.values())  # Convert dictionary values back to list



def find_id(input, best_names, dix_name):
 #   print('start find_id')
    clean_aff = input[0]

    id_list = []   
                        
    for org_list in best_names:
        org = org_list[0]
        conf = org_list[1]
        
         
        
                    
        if len(dix_name[org]) == 1:
            id_ = dix_name[org][0]['id']
            city_ = dix_name[org][0]['city']
            country_ = dix_name[org][0]['country']
            if  'univ' in org and 'institu' in org:
                if city_ not in clean_aff and country_ not in clean_aff:
                    pass
                else:
                    id_list.append([org, conf, id_])
            else:
                id_list.append([org, conf, id_])

    
        else:
            if org in dix_name:
                match_found = False
                for triplet in dix_name[org]:
                    city_ = triplet['city']
                    id_ = triplet['id']
                    if city_ in clean_aff:
                        if city_ not in org: 
                            id_list.append([org, conf, id_])
                            match_found = True
                            break
                        else:
                            if clean_aff.count(city_) >1:
                                id_list.append([org, conf, id_])
                                match_found = True
                                break
                            
                if not match_found:
                     for triplet in dix_name[org]:
                        city_ = triplet['city']
                        id_ = triplet['id']
                        if city_ in   clean_aff and city_ not in org:
                            id_list.append([org, conf, id_])
                            break  
                    
                if not match_found:
                    match_found2 = False
                    match_found3 = False

                    all_countries = list(set([x['country'] for x in dix_name[org]]))
                    if len(all_countries) > 1:
                        for triplet in dix_name[org]:
                            country_ = triplet['country']
                            id_ = triplet['id']    

                            tokens = set(clean_aff.lower().split())
                            text = clean_aff.lower()

                            if (country_ == 'united states' and (
                                'united states' in text 
                                or {'usa', 'usa.'} & tokens 
                                or 'u.s.a.' in text)) or (country_ == 'germany' and (
                                'deutschland' in text )) or (country_ == 'united kingdom' and (
                                'united kingdom' in text 
                                or {'uk', 'uk.'} & tokens 
                                or 'u.k.' in text)) or (country_ == 'turkey' and ('turkiye' in text)):

                                id_list.append([org, conf, id_])
                                match_found2 = True
                                match_found3 = True
                                break    
                        

                            elif country_.split()[0] in clean_aff:

                                if country_ not in org:
                                    id_list.append([org, conf, id_])
                                    match_found2 = True
                                    match_found3 = True
                                    break

                    else:
                        single_country = all_countries[0]
                        if single_country in clean_aff:
                            id_list.append([org, conf, dix_name[org][0]['id']])
                            match_found2 = True
                            match_found3 = True
                            break
                        elif single_country in country_synonyms:
                            for v in country_synonyms[single_country]:
                                if v in  clean_aff:
                                    id_list.append([org, conf, dix_name[org][0]['id']])
                                    match_found2 = True
                                    match_found3 = True
                                    break
                        
                    if not match_found3:                        
                        for triplet in dix_name[org]:
                            country_ = triplet['country']
                            id_ = triplet['id']   
                            if country_ in clean_aff and country_ in org:
                                id_list.append([org, conf, id_])
                                match_found2 = True
                                break  
                            
                    if not match_found2:
                        for sp in specific:
                            if sp in org:
                                if len(dix_name[org]) == 1:
                                
                                    id_list.append([org, conf, dix_name[org][0]['id']])
                                else:
                                    for rec in dix_name[org]:
                                        if dix_id[rec['id']]['is_parent'] == 'y':
                                            id_list.append([org, conf, rec['id']])


    id_list_final = keep_highest_url(id_list)
    return id_list_final



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
            result_dict = [{'provenance': 'affro', 'version': VERSION,  'pid':'openorgs', 'value':x[2], 'name': dix_id[x[2]]['name'], 'confidence':x[0], 'status':x[3], 'country': dix_id[x[2]]['country']} if "openorgs" in x[2] else {'provenance': 'affro', 'version': VERSION,'pid':'ror', 'value':x[2], 'name': dix_id[x[2]]['name'], 'confidence':x[0], 'status':x[3], 'country': dix_id[x[2]]['country']} for x in final_matching]
            return result_dict
        
        else:
            result_dict = [{'provenance': 'affro', 'version': VERSION,  'pid':'openorgs', 'value':x[2], 'name': dix_id[x[2]]['name'],'confidence':x[0], 'status':x[3], 'country': dix_id[x[2]]['country']} if "openorgs" in x[2] else {'provenance': 'affro', 'version': VERSION, 'pid':'ror', 'value':x[2],  'name': dix_id[x[2]]['name'], 'confidence':x[0], 'status':x[3],  'country': dix_id[x[2]]['country']} for x in results_upd]
            return result_dict

    elif len(results_upd)>0:
        result_dict = [{'provenance': 'affro', 'version': VERSION,  'pid':'openorgs', 'value':x[2], 'name': dix_id[x[2]]['name'], 'confidence':x[0], 'status':x[3], 'country': dix_id[x[2]]['country']} if "openorgs" in x[2] else {'provenance': 'affro', 'version': VERSION, 'pid':'ror', 'value':x[2],  'name': dix_id[x[2]]['name'],  'confidence':x[0], 'status':x[3],  'country': dix_id[x[2]]['country']} for x in results_upd]
        return result_dict
    else:
        return  []
        