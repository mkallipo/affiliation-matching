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

excluded = {'univ', 'inst', 'national', 'nacional', 'colege', 'center', 'organization', 'hospital'}


    
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
    # print(input)
    clean_aff = input[0]
    light_aff = input[1]
    id_list = []   
    # print("best_names", best_names)
                    
    for org_list in best_names:
        # print('org_list',org_list)
        org = org_list[0]
        # print('org:', org)
        conf = org_list[1]
                        
        if len(dix_name[org]) == 1:
            # print('unique')
            id_ = dix_name[org][0]['id']
            city_ = dix_name[org][0]['city']
            country_ = dix_name[org][0]['country']
            country_set = {
            synonym
            for country in country_
            for synonym in country_synonyms.get(country, [])}
     


            
            # print(city_, 'country_', country_)
            # print('c',country_set)
            # print('l',set(light_aff.split()))
            if org == light_aff:
                id_list.append([org, conf, id_])

            elif    (
                # ('univ' in org and 'institu' in org)
                # or
                (
                   not any(city in light_aff for city in city_) \
                    and not country_set & set(light_aff.split())

                    # and 'univ' not in org
                    # and 'inst' not in org
                    # and 'national' not in org
                    # and 'nacional' not in org
                    # and 'colege' not in org
                    and not any(word in org for word in excluded)

                    and valueToCategory(org)[1] not in {'Company', 'Acronyms', 'Specific'}
                  
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
                
                if any(c in clean_aff for c in city_):
                    if not any(city in org for city in city_): 
                        id_list.append([org, conf, id_])
                        match_found = True
                        # break
                    else:
                        if any(clean_aff.count(city) > 1 for city in city_):
                            id_list.append([org, conf, id_])
                            match_found = True
                            # print('done')
                            # break
                        
            if not match_found:
                # print('no city helped', len(dix_name[org]), quadruple['country'])
       
                countries_ids = {country
                for quadruple in dix_name[org]
                for country in quadruple['country']}
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

                        if (('united states' in country_  and ('united states' in text or {'usa', 'usa.'} & tokens or 'u.s.a.' in text)) or 
                            ('germany' in country_ and ('deutschland' in text )) or 
                            ('united kingdom' in country_ and ('united kingdom' in text or ({'uk', 'uk.'} & tokens) or 'u.k.' in text)) or 
                            ('turkey' in country_ and ('turkiye' in text)) or 
                            ('china' in country_  and ('chinese' in text or 'prc' in text))):
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
                        if any(country.split()[0] in clean_aff for country in country_):
                            # print('no specific found')
                            if not any(country in org for country in country_):
                                id_list.append([org, conf, id_])
                                match_found = True
                                break

                 
                if not match_found:                        
                    for quadruple in dix_name[org]:
                        country_ = quadruple['country']
                        id_ = quadruple['id']   
                        if any(c in clean_aff for c in country_) and any(c in org for c in country_):
                            id_list.append([org, conf, id_])
                            match_found = True
                            # break  
                        
                if not match_found:
                    # print('no country helped')
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
                            match_found = True

                            break
                # if not match_found:
                #     print('nichts')
                #     break


    # print('id_list',id_list)       
    id_list_final = keep_highest_score(id_list)
    # print('end find_id', id_list_final)
    return id_list_final
