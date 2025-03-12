from functions_cluster import *

# tokenization

def create_df_algorithm(raw_aff_string, radius_u):
    clean_aff = clean_string(remove_outer_parentheses(remove_leading_numbers(raw_aff_string)))
    aff_no_symbols_d =  substrings_dict(reduce(clean_aff))
    substring_list = [remove_stop_words(x) for x in list(aff_no_symbols_d.values())]
    # aff_no_symbols_d =  substrings_dict(reduce(clean_string(remove_outer_parentheses(remove_leading_numbers(raw_aff_string)))))
    # substring_list = list(aff_no_symbols_d.values())

    i = 0

    while i < len(substring_list) - 1:
        if 'progr' in substring_list[i]: # and 'dep' in substring_list[i+1]:
            substring_list.pop(i)

            
        elif ('assistant' in substring_list[i] or 'researcher' in substring_list[i] or 'phd' in substring_list[i] or 'student' in substring_list[i] or 'section' in substring_list[i] or 'prof' in substring_list[i] or 'director' in substring_list[i]) and (not 'school' in substring_list[i+1] or 'univ', substring_list[i+1] or 'inst' in substring_list[i+1] or 'lab' in substring_list[i+1] or 'fac' in substring_list[i+1]):
            substring_list.pop(i)

        elif ('engineer' in substring_list[i] or 'progr'in substring_list[i] or 'unit' in substring_list[i]  or 'dep' in substring_list[i] or  'school' in substring_list[i] or 'lab' in substring_list[i] # or 'inst' in substring_list[i] #or is_contained('hosp', substring_list[i]) 
            or 'fac' in substring_list[i]) and 'univ' in substring_list[i+1]:
            if not 'univ' in substring_list[i]:
                substring_list.pop(i)
            else:
                i = i+1
                continue

        elif 'lab' in substring_list[i] and ('colege' in substring_list[i+1] or 'dep' in substring_list[i+1] or 'school' in substring_list[i+1]):
            if not 'univ' in substring_list[i]: #'inst' in substring_list[i+1] or 
                substring_list.pop(i)
            else:
                i = i+1
                continue

        # elif is_contained('dep', substring_list[i]) and (is_contained('tech', substring_list[i+1]) or is_contained('colege', substring_list[i+1]) or is_contained('inst', substring_list[i+1]) or  is_contained('hosp', substring_list[i+1]) or  is_contained('school', substring_list[i+1]) or  is_contained('fac', substring_list[i+1])):
        #     if not is_contained('univ', substring_list[i]):
        #         substring_list.pop(i)
        #     else:
        #         i = i+1
        #         continue

        # elif is_contained('inst',substring_list[i]) and (is_contained('school', substring_list[i+1]) or is_contained('dep', substring_list[i+1]) or is_contained('acad', substring_list[i+1]) or is_contained('hosp', substring_list[i+1]) or is_contained('clin', substring_list[i+1]) or is_contained('klin', substring_list[i+1])  or is_contained('fak', substring_list[i+1]) or is_contained('fac', substring_list[i+1]) or is_contained('cent', substring_list[i+1]) or is_contained('div', substring_list[i+1])):
        #     if not is_contained('univ', substring_list[i]):
        #         substring_list.pop(i)
        #     else:
        #         i = i+1
        #         continue


        # elif is_contained('school',substring_list[i]) and is_contained('colege', substring_list[i+1]):
        #     if not is_contained('univ', substring_list[i]):
        #         substring_list.pop(i)
        #     else:
        #         i = i+1
        #         continue

        else:
            i += 1

    light_aff = (', '.join((substring_list)))
    for x in substring_list:
        if x in city_names+remove_list:
            substring_list.remove(x)


    substring_list0 = [shorten_keywords([x], radius_u) for x in substring_list if len(shorten_keywords([x],radius_u))>0]
    substring_list1 = [inner for outer in substring_list0 for inner in outer]
    
    def valueToCategory(value):
        flag = 0

        for k in categ_dicts:
            if k in value and categ_dicts[k] in categ_string.split('|'): 
                flag = 1
        return flag
    
    aff_list = [{"index": i, "keywords": substring_list1[i], "category": valueToCategory(substring_list1[i])} for i in range(len(substring_list1))]

    filtered_list = [entry for entry in aff_list if entry.get("category") == 1]

    return   [clean_aff, light_aff, filtered_list]