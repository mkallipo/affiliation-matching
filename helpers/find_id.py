from .functions import *
from .create_input import *

specific = [k for k in categ_dicts if categ_dicts[k] == 'Specific' or  categ_dicts[k] == 'Acronyms']

country_synonyms = {x: [x] for x in countries}
country_synonyms["united states"] = ["united states", "u.s.a.", "usa", "usa.","states"]
country_synonyms["germany"] = ["germany","deutschland"]
country_synonyms["united kingdom"] = ["united kingdom", "u.k.", "uk", "uk.","kingdom","england"]
country_synonyms["turkey"] = ["turkey","turkiye", "cyprus"]
country_synonyms["china"] = ["china", "prc","chinese"]
country_synonyms["ireland"] = ["eire", "ireland"]
country_synonyms["south korea"] = ["south korea", "korea"]

special_countries = {'united states', 'united kngdom', 'germany', 'china','turkey'}

excluded = ['univ', 'inst', 'national', 'nacional', 'colege']


    
def keep_highest_score(data):
    """"
    Keeps only one inner list for each unique last value.
    The kept list is the one with the greatest second value.
    If multiple have the same greatest second value, one is kept arbitrarily.
    """
    best = {}
    for lst in data:
        key = lst[-1]
        value = lst[1]
        if key not in best or value > best[key][1]:
            best[key] = lst
    return list(best.values())


def find_id(input, best_names, dix_name):
    # print('start find_id')
    # print(best_names)
    # print(input)
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
            # print(city_, country_)
            # print('c',set(country_synonyms[country_]))
            # print('l',set(light_aff.split()))
            if org == light_aff:
                id_list.append([org, conf, id_])

            elif    (
                # ('univ' in org and 'institu' in org)
                # or
                (
                    city_ not in light_aff
                    and not set(country_synonyms[country_]) & set(light_aff.split())
                    # and 'univ' not in org
                    # and 'inst' not in org
                    # and 'national' not in org
                    # and 'nacional' not in org
                    # and 'colege' not in org
                    and not any(word in org for word in excluded)

                    and valueToCategory(org)[1] not in ['Company', 'Acronyms', 'Specific']
                  
                ) 
            ):
                # print('pass')
                pass
            else:
                # print(org)
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
                # print('no city helped', len(dix_name[org]))
       
                countries_ids = {quadruple['country'] for  quadruple in dix_name[org]}
                if countries_ids & special_countries:
                    # print('special country')
                    for quadruple in dix_name[org]:
                        country_ = quadruple['country']
                        # print(country_)
                        id_ = quadruple['id']    

                        tokens = set([x.replace(',','') for x in clean_aff.lower().split()])
                        # print('tokens',tokens)
                        text = clean_aff.lower()
                        # print('text', text)

                        if ((country_ == 'united states' and ('united states' in text or {'usa', 'usa.'} & tokens or 'u.s.a.' in text)) or 
                            (country_ == 'germany' and ('deutschland' in text )) or 
                            (country_ == 'united kingdom' and ('united kingdom' in text or ({'uk', 'uk.'} & tokens) or 'u.k.' in text)) or 
                            (country_ == 'turkey' and ('turkiye' in text)) or 
                            (country_ == 'china' and ('chinese' in text or 'prc' in text))):
                            # print('specific country found')
                            id_list.append([org, conf, id_])
                            match_found = True
                            break    
                

                if not match_found:
                    # print('no special country')
                    for quadruple in dix_name[org]:
                        country_ = quadruple['country']
                        id_ = quadruple['id']   
                        # print(country_)
                        if country_.split()[0] in clean_aff:
                            # print('no specific found')
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
                    # print('check sp')
                    for sp in specific:
                        if sp in org:
                            for rec in dix_name[org]:
                                if dix_id[rec['id']]['top_level'] == 'y':
                                    # print('top level found for specific')
                                    id_list.append([org, conf, rec['id']])
                                    match_found = True
                                    break
    
                            if  not match_found:
                                dix_id[rec['id']]['parent'] == 'y'
                                # print('parent found for specific')
                                id_list.append([org, conf, rec['id']])
                                match_found = True
                                break
                                
                if not match_found:
                    # print('check first y')
                    for quadruple in dix_name[org]:
                        if 'department' not in org and 'labora' not in org and quadruple['first'] == 'y':
                            id_list.append([org, conf, quadruple['id']])
                            break

    # print('id_list',id_list)       
    id_list_final = keep_highest_score(id_list)
    # print('end find_id', id_list_final)
    return id_list_final
