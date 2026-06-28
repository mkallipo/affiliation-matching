from affro.helpers.functions import *

def valueToCategory(value):
    
    keys = []
    values = []
    for k in categ_dicts:
        if k in value and categ_dicts[k] in _CATEG_SET:
            if k not in keys:
                keys.append(k)
            values.append(categ_dicts[k])
  
    return [keys, values[0]] if len(values) > 0 else [[], '']


# Pre-compute category set once at module level (avoids rebuilding on every call)
_CATEG_SET = frozenset(categ_string.split('|'))

# Pre-compute protect set for O(1) lookup
protect = {
    'national univer ireland', 
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
    'st patricks colege',
    'instit techn',
    'trinity colege',
    'st johns colege',
    'wiliam beaumont hospital',
    'american colege',
    'univer studi'
}

keep = {'univer','trinity colege','imperial colege' ,'colege surgeons'}

# Pre-compute city_names and countries as sets for O(1) lookup
city_names_set = None
countries_set = None
remove_list_set = None

def _init_sets():
    """Initialize sets on first call for O(1) lookups."""
    global city_names_set, countries_set, remove_list_set
    if city_names_set is None:
        city_names_set = set(city_names)
        countries_set = set(countries)
        remove_list_set = set(remove_list)

def _check_author_words(text):
    """Pre-compile exclusion word checks."""
    author_words = {'asistant', 'researcher', 'phd', 'student', 'section', 'prof', 'director'}
   # required_words = {'school', 'univ', 'inst', 'lab', 'fac','hospital'}
    
    return any(word in text for word in author_words)#, any(word in text for word in required_words)


def create_df_algorithm(raw_aff_string, radius_u):
    """
    OPTIMIZED VERSION:
    - Pre-compute sets for O(1) lookups instead of repeated 'in' checks
    - Avoid redundant valueToCategory() calls by caching results
    - Combine string operations where possible
    - Use set operations for filtering
    """
    _init_sets()
    # print("raw_aff_string:", raw_aff_string)
    clean_aff = clean_string(remove_outer_parentheses(remove_leading_numbers(raw_aff_string)))
    # print("clean_aff:", clean_aff)
    countries_list = description(clean_aff)[1]
    aff_no_symbols_d = substrings_dict(reduce(clean_aff))
    # print("aff_no_symbols_d:", aff_no_symbols_d)
    substring_list = [replace_abbr_univ(x) for x in list(aff_no_symbols_d.values())]
    # print("substring_list after replace_abbr_univ:", substring_list)
    i = 0
    while i < len(substring_list) - 1:
        current = substring_list[i]
        next_item = substring_list[i + 1]
        
        # OPTIMIZATION: Use set membership for O(1) checks
        if current in protect and any(
            name in next_item#.split()
            for name in (city_names_set | countries_set)
         #   if name != "univer"
        ):
            # print('Merging protected:', current, 'with next:', next_item)
            substring_list[i] = current + ' ' + next_item
            i += 2
            continue
        
        # OPTIMIZATION: Pre-compute exclusion checks
        has_exclusion = _check_author_words(current)
        #has_exclusion, has_required = _check_exclusion_words(current)
        
        # print(has_exclusion, has_required)
        if (has_exclusion and (not 'school' in next_item or any(w in next_item for w in {'univ', 'inst', 'lab', 'fac','colege'}))) or ('colege' in current and 'univ' in next_item): #if not 'univ' in current and 'trinity colege' not in current and 'colege surgeons' not in current:
            if not any(sub in current for sub in keep):

                substring_list.pop(i)
            else:
                i += 1
                
        elif any(word in current for word in {'engineer', 'progr', 'unit', 'dep', 'school', 'fac'}) and 'univ' in next_item:
            if not 'univ' in current and not 'hospital' in current:
                substring_list.pop(i)
            else:
                i += 1
                continue
        else:
            i += 1
    # print("substring_list before merging:", substring_list)
    light_aff = ', '.join(substring_list)
    # print("light_aff:", light_aff)
    # OPTIMIZATION: Use set for filtering instead of list comprehension
    substring_list = [x for x in substring_list if x.replace(' gmbh', '') not in city_names_set | remove_list_set]
    
    # OPTIMIZATION: Cache valueToCategory results to avoid recomputation
    # OPTIMIZATION: compute shorten_keywords once per element (was called twice: once for guard, once for value)
    substring_list1 = []
    for x in substring_list:
        shortened = shorten_keywords([x], radius_u)
        if shortened:
            substring_list1.extend(shortened)
    
    # OPTIMIZATION: Single pass through valueToCategory instead of multiple passes
    aff_list = []
    keys_list_raw = []
    
    for i, keyword in enumerate(substring_list1):
        category_result = valueToCategory(keyword)
        if category_result[1] != '':
            aff_list.append({
                "index": i, 
                "keywords": keyword, 
                "category": category_result[1]
            })
        if len(category_result[0]) > 0:
            keys_list_raw.extend(category_result[0])
    
    # OPTIMIZATION: Use set to remove duplicates O(n) instead of nested list comprehension
    keys_list = list(set(keys_list_raw))
    
    return [clean_aff, light_aff, aff_list, countries_list, keys_list]
