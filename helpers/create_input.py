from .functions import *

def valueToCategory(value):
   # flag = 0

    for k in categ_dicts:
        if k in value and categ_dicts[k] in categ_string.split('|'): 
    #        flag = 1
            return  categ_dicts[k]
    

# tokenization
protect = ['national univer ireland', 
           'univer', 
           'univer california', 
           'univer colege hospital', 
           'univer colege', 
           'univer hospital', 
           'imperial colege', 
           'city univer', 
           'univer medical school',
           'california state univer',
           'national techn univer',
           'techn univer',
           'islamic azad univer',
           'univer nevada',
           'univer maryland',
           'state univer',
           'rijksuniver',
           'rijks univer',
           'univer medical center',
           'royal colege surgeons',
           'st patricks colege'
]

def create_df_algorithm(raw_aff_string, radius_u):
    clean_aff = clean_string(remove_outer_parentheses(remove_leading_numbers(raw_aff_string)))
    countries_list = description(clean_aff)[1]
    aff_no_symbols_d =  substrings_dict(reduce(clean_aff))
    substring_list = [replace_abbr_univ(x) for x in list(aff_no_symbols_d.values())]
    i = 0

    while i < len(substring_list) - 1:
        if substring_list[i] in protect and any(name in substring_list[i+1] for name in city_names): #substring_list[i+1] in city_names:
            substring_list[i] = substring_list[i] + ' ' + substring_list[i+1]
            i = i+2
            continue
                       
        elif ('assistant' in substring_list[i] or 'researcher' in substring_list[i] or 'phd' in substring_list[i] or 'student' in substring_list[i] or 'section' in substring_list[i] or 'prof' in substring_list[i] or 'director' in substring_list[i]) and (not 'school' in substring_list[i+1] or 'univ', substring_list[i+1] or 'inst' in substring_list[i+1] or 'lab' in substring_list[i+1] or 'fac' in substring_list[i+1]):
            if not 'univ' in substring_list[i]:
                substring_list.pop(i)
            else:
                i = i+1
                
        elif ('engineer' in substring_list[i] or 'progr'in substring_list[i] or 'unit' in substring_list[i]  or 'dep' in substring_list[i] or  'school' in substring_list[i] #or 'lab' in substring_list[i] # or 'inst' in substring_list[i] #or is_contained('hosp', substring_list[i]) 
            or 'fac' in substring_list[i]) and 'univ' in substring_list[i+1]:
            if not 'univ' in substring_list[i]:
                substring_list.pop(i)
            else:
                i = i+1
                continue

        else:
            i += 1
  
    light_aff = (', '.join((substring_list)))
                       
    substring_list = [x for x in substring_list  if x.replace(' gmbh','') not in city_names+remove_list]
  
    substring_list0 = [shorten_keywords([x], radius_u) for x in substring_list if len(shorten_keywords([x],radius_u))>0]
  
    substring_list1 = [inner for outer in substring_list0 for inner in outer]
  
    aff_list = [{"index": i, "keywords": substring_list1[i], "category": valueToCategory(substring_list1[i])} for i in range(len(substring_list1))]

    filtered_list = [entry for entry in aff_list if type(entry.get("category")) == str]

    return   [clean_aff, light_aff, filtered_list, countries_list]