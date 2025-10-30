from .functions import *
from .create_input import *

specific = [k for k in categ_dicts if categ_dicts[k] == 'Specific' or  categ_dicts[k] == 'Acronyms']

country_synonyms = {
    "united states": ["united states", "u.s.a.", "usa", "usa."],
    "germany": ["germany","deutschland"],
    "united kingdom": ["united kingdom", "u.k.", "uk", "uk."],
    "turkey": ["turkey","turkiye"],
}

country_synonyms = {x: [x] for x in countries}
country_synonyms["united states"] = ["united states", "u.s.a.", "usa", "usa."]
country_synonyms["germany"] = ["germany","deutschland"]
country_synonyms["united kingdom"] = ["united kingdom", "u.k.", "uk", "uk."]
country_synonyms["turkey"] = ["turkey","turkiye", "cyprus"]
country_synonyms["china"] = ["china", "prc","chinese"]
    
    
def keep_highest_url(lst):
    best = {}

    for item in lst:
        name, score, url = item
        if name not in best or url > best[name][2]:  # Keep the highest URL
            best[name] = item  # Store the full entry

    return list(best.values())  # Convert dictionary values back to list


def find_id(input, best_names, dix_name):
    # print('start find_id')
    clean_aff = input[0]
    light_aff = input[1]
    id_list = []   
                        
    for org_list in best_names:
        org = org_list[0]
        # print('org:', org)
        conf = org_list[1]
                        
        if len(dix_name[org]) == 1:
            # print('unique')
            id_ = dix_name[org][0]['id']
            city_ = dix_name[org][0]['city']
            country_ = dix_name[org][0]['country']
            # if  'univ' in org and 'institu' in org:
            if  ('univ' in org and 'institu' in org) or ((city_ not in light_aff and not bool(set(country_synonyms[country_ ]) & set(light_aff.split()))) and 'univ' not in org and  valueToCategory(org) not in ['Company', 'Acronyms','Specific']):
                pass
            else:
                id_list.append([org, conf, id_])
            # else:
            #     id_list.append([org, conf, id_])
    
        else:
            # print('multiple')
            match_found = False
            for quadruple in dix_name[org]:
                city_ = quadruple['city']
                # print('city', city_)
                id_ = quadruple['id']
                
                if city_ in clean_aff:
                    if city_ not in org: 
                        id_list.append([org, conf, id_])
                        match_found = True
                        # break
                    else:
                        if clean_aff.count(city_) >1:
                            id_list.append([org, conf, id_])
                            match_found = True
                            # break
                        
            if not match_found:
                # print('no city helped')
                # all_countries = list(set([x['country'] for x in dix_name[org]]))
                # if len(all_countries) > 1:
                for quadruple in dix_name[org]:
                    country_ = quadruple['country']
                    id_ = quadruple['id']    

                    tokens = set(clean_aff.lower().split())
                    text = clean_aff.lower()

                    if (country_ == 'united states' and (
                        'united states' in text 
                        or {'usa', 'usa.'} & tokens 
                        or 'u.s.a.' in text)) or (country_ == 'germany' and (
                        'deutschland' in text )) or (country_ == 'united kingdom' and (
                        'united kingdom' in text 
                        or {'uk', 'uk.'} & tokens 
                        or 'u.k.' in text)) or (country_ == 'turkey' and ('turkiye' in text)) or (country_ == 'china' and ('chinese' in text or 'prc' in text)):

                        id_list.append([org, conf, id_])
                        match_found = True
                        break    
                

                    elif country_.split()[0] in clean_aff:
                        if country_ not in org:
                            id_list.append([org, conf, id_])
                            match_found = True
                            break

                 
                if not match_found:                        
                    for quadruple in dix_name[org]:
                        country_ = quadruple['country']
                        id_ = quadruple['id']   
                        if country_ in clean_aff and country_ in org:
                            id_list.append([org, conf, id_])
                            match_found = True
                            # break  
                        
                if not match_found:
                    for sp in specific:
                        if sp in org:
                            for rec in dix_name[org]:
                                if dix_id[rec['id']]['is_parent'] == 'y':
                                    id_list.append([org, conf, rec['id']])
                                    # break
                if not match_found:
                    for quadruple in dix_name[org]:
                        if 'department' not in org and 'labora' not in org and quadruple['is_first'] == 'y':
                            id_list.append([org, conf, quadruple['id']])
                            break

            
    id_list_final = keep_highest_url(id_list)
    # print('end find_id', id_list_final)
    return id_list_final
