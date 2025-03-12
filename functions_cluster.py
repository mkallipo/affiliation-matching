import re
import unicodedata
import html
from unidecode import unidecode
from collections import defaultdict
import json   
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

path_dict = "dictionaries/"
#path_dict = ""
path_txt = 'txt_files/'
#path_txt = ""

def load_txt(file_path):
    with open(file_path, 'r',  encoding='utf-8') as file:
        list_ = [line.strip() for line in file]
        return list_
    

def load_json(file_path): 
    with open(file_path, 'r') as json_file:
        json_dict = json.load(json_file)
        return json_dict
        
#categ_string = 'Laboratory|Univ/Inst|Hospital|Foundation|Museum|Government|Company'
categ_string = 'Laboratory|Univ/Inst|Hospital|Foundation|Specific|Museum|Government|Company'
dix_org = load_json(path_dict + 'dix_acad_new.json')


def replace_double_consonants(text):
    # This regex pattern matches any double consonant
    pattern = r'([bcdfghjklmnpqrstvwxyz])\1'
    # The replacement is the first captured group (the single consonant)
    result = re.sub(pattern, r'\1', text, flags=re.IGNORECASE)
    return result


    
dix_id_country = load_json(path_dict + 'dix_id_country.json')
categ_dicts = load_json(path_dict + 'dix_categ_new.json')
key_words = list(categ_dicts.keys()) + ['universi']
countries =  load_txt(path_txt + 'country_names.txt')
remove_list = [replace_double_consonants(x) for x in load_txt(path_txt + 'remove_list.txt')]
stop_words = load_txt(path_txt + 'stop_words.txt')
stop_words.remove('and')
university_terms = [replace_double_consonants(x) for x in load_txt(path_txt + 'university_terms.txt')]
city_names = [replace_double_consonants(x) for x in load_txt(path_txt + 'city_names.txt')]


def is_contained(s, w):
    """
    Checks if all words in the string 's' are present in the iterable 'w'.

    Parameters:
        s (str): A string containing words to check.
        w (iterable): An iterable (e.g., list, set) containing words to search in.

    Returns:
        bool: True if all words in 's' are found in 'w', otherwise False.
    """
    words = s.split()  # Split the string 's' into a list of words
    for word in words:
        if word not in w:  # If a word from 's' is not found in 'w'
            return False  # Return False immediately
    return True  # If all words from 's' are found in 'w', return True


def starts_with_any(string, prefixes):
    """
    Checks if the given string starts with any prefix from a list.

    Parameters:
        string (str): The string to check.
        prefixes (iterable of str): A list or tuple of prefixes to match against.

    Returns:
        list: [True, prefix] if a match is found, where 'prefix' is the matching prefix.
        bool: False if no prefix matches.
    """
    for prefix in prefixes:
        if string.startswith(prefix):
            return [True, prefix]
    return False


def remove_leading_numbers(s):
    return re.sub(r'^\d+', '', s)

def remove_multi_digit_numbers(text):
    return re.sub(r'\b\d{2,}\b', '', text).strip()

def remove_outer_parentheses(string):
    """Remove outer parentheses from the string if they enclose the entire string."""
    if string.startswith('(') and string.endswith(')'):
        return string[1:-1].strip()
    return string

def replace_roman_numerals(text):
    # Replace only whole words 'iii', 'ii', and 'I'
    text = re.sub(r'\biii\b', '3', text)  
    text = re.sub(r'\bii\b', '2', text)  
    text = re.sub(r'\bi\b', '1', text)  
    return text


def insert_space_between_lower_and_upper(s):
    """
    Inserts a space between a lowercase letter followed by an uppercase letter in a string.

    Parameters:
    s (str): The input string.

    Returns:
    str: The modified string with spaces inserted.
    """
 # Temporarily replace 'AstraZeneca' to prevent modification
    s = s.replace('AstraZeneca', 'ASTRAZENECA_TEMP')
    s = s.replace('BioNTech', 'BIONTECH_TEMP')

    
    # Exclude cases where 'Mc' is followed by a capital letter
    modified_string = re.sub(r'(?<!Mc)([a-z])([A-Z])', r'\1 \2', s)
    
    # Ensure no spaces are inserted within 'Mc' sequences
    modified_string = re.sub(r'(Mc) ([A-Z])', r'\1\2', modified_string)
    
    # Restore 'AstraZeneca'
    modified_string = modified_string.replace('ASTRAZENECA_TEMP', 'AstraZeneca')
    modified_string = modified_string.replace('BIONTECH_TEMP', 'BioNTech')

    
    return modified_string




#stop_words = ['from', 'the', 'of', 'at', 'de','for','et','für','des', 'in','as','a','and','fur','for','und','di']


def remove_stop_words(text):
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words]
    return ' '.join(filtered_words)


def remove_parentheses(text):
   return re.sub(r'\([^()]*\)', '', text)

L = ['univ', 'hospital', 'clinic', 'klinik', 'Univ', 'Hospital', 'Clinic', 'Klinik']
word_pattern = "|".join(map(re.escape, L))

def process_parentheses(text):
    """
    Processes parentheses in a given text by:
    1. Removing parentheses that do not contain any word from a the list L =  ['univ', 'hospital', 'clinic', 'klinik', 'Univ', 'Hospital', 'Clinic', 'Klinik'].
    2. Replacing parentheses with commas if they contain a word from the list.

    Parameters:
        text (str): The input string containing parentheses.

    Returns:
        str: The modified string after processing parentheses.
    """

    text = re.sub(r'\((?![^)]*(' + word_pattern + r'))[^)]*\)', '', text)

    # Replace `(` with `,` and `)` with `,` if a word from L is inside
    text = re.sub(r'\(([^)]*(' + word_pattern + r')[^)]*)\)', r', \1,', text)

    return text



def protect_phrases(input_string, phrases):
    # Replace phrases with placeholders
    placeholder_map = {}
    for i, phrase in enumerate(phrases):
        placeholder = f"__PLACEHOLDER_{i}__"
        placeholder_map[placeholder] = phrase
        input_string = input_string.replace(phrase, placeholder)
    return input_string, placeholder_map

def restore_phrases(split_strings, placeholder_map):
    # Restore placeholders with original phrases
    restored_strings = []
    for s in split_strings:
        for placeholder, phrase in placeholder_map.items():
            s = s.replace(placeholder, phrase)
        restored_strings.append(s)
    return restored_strings

def replace_comma_spaces(text):
    return text.replace('  ', ' ').replace(' , ', ', ')

def replace_underscore(text):
    if 'University-' in text and 'University-Hospital' not in text:
        return text.replace('-',',')
    else:
        return text

def split_string_with_protection(input_string, protected_phrases):
    # Step 1: Protect specific phrases
    input_string, placeholder_map = protect_phrases(input_string, protected_phrases)
    
    # Step 2: Split the string on specified delimiters
    split_strings = [s.strip() for s in re.split(r'[,;/]| – ', input_string) if s.strip()]
    
    # Step 3: Restore protected phrases
    split_strings = restore_phrases(split_strings, placeholder_map)
    
    return split_strings



protected_phrases1 =  [
    phrase.format(x=x)
    for x in city_names
    for phrase in [
        'university, {x}',
        
        'univ, {x}',
        
        'university california, {x}',

        'university colege hospital, {x}',
        
        'national univ ireland, {x}',

        'national university ireland, {x}',

        'university colege, {x}',
        
        'university hospital, {x}', 

        'imperial colege, {x}',
        
        'city university, {x}', 

        'university medical school, {x}'

    ]
]



replacements = {#'cliniques':'center',
                # 'clinique':'center',
                # 'centres':'center',
                'czechoslovak':'czech',
                'saint' : 'st',
                'aghia' : 'agia', 
                'universitatsklinikum' : 'universi hospital',
                'universitetshospital' : 'universi hospital',
                'universitatskinderklinik' : 'universi childrens hospital',
                'universitatskliniken' : 'universi hospital',
                'Universitätsklinik' : 'universi hospital',
                'universitatsmedizin' : 'universi medicine',
                'universitatsbibliothek' : 'universi library',
                'nat.' : 'national',
                'hosp.':'hospital',
                'uni versity' : 'university',
                'unive rsity' : 'university',
                'univ ersity' : 'university',
                'inst ' : 'institute ',
                'adv ' : 'advanced ',
                'univ ' : 'university ',
                'stud ' : 'studies ',
                'inst.' : 'institute',
                'adv.' : 'advanced',
                'univ.' : 'university',
                'stud.' : 'studies',
                'univercity' : 'university', 
                'univerisity' : 'university', 
                'universtiy' : 'university', 
                'univeristy' : 'university',
                'universirty' : 'university', 
                'universiti' : 'university', 
                'universitiy' : 'university',
                'universty' : 'university',
                'techniche' : 'technological',
                'univ col' : 'university colege',
                'univ. col.' : 'university colege',
                'univ. coll.' : 'university colege',
                'col.' : 'colege',
                'hipokration' : 'hipocration', #sp
                'belfield, dublin' : 'dublin', #sp
                'balsbridge, dublin' : 'dublin', #sp #ballsbridge
                'earlsfort terace, dublin' : 'dublin', #sp #terrace
                'bon secours hospital, cork' : 'bon secours hospital cork', #sp
                'bon secours hospital, dublin' : 'bon secours hospital dublin', #sp
                'bon secours hospital, galway' : 'bon secours hospital galway', #sp
                'bon secours hospital, tralee' : 'bon secours hospital tralee', #sp
                'bon secours health system' : 'bon secours hospital dublin', #sp
                'bon secours hospital, glasnevin' : 'bon secours hospital dublin', #sp
                'imperial colege science, technology medicine' : 'imperial colege science technology medicine', #sp
                'ucl queen square institute neurology' : 'ucl, london', #sp
                'ucl institute neurology' : 'ucl, london', #sp
                'royal holoway, university london' : 'royal holoway universi london', #holloway #sp
                'city, university london' : 'city universi london', #sp
                'city university, london' : 'city universi london', #sp
                'aeginition' : 'eginition', #sp
                'national technical university, athens' : 'national technical university athens' #sp
            # 'harvard medical school' : 'harvard university'


    
}

def fully_unescape(text):
    """Recursively unescapes HTML-encoded text until fully decoded."""
    while True:
        new_text = html.unescape(text)
        if new_text == text:  # Stop when no more changes occur
            return new_text
        text = new_text


def substrings_dict(string):  
    """
    Processes a given string by performing the following transformations:
    1. Applies predefined replacements from a dictionary.
    2. Fixes common hospital-related misspellings.
    3. Splits the string while protecting certain phrases.
    4. Normalizes country abbreviations (e.g., 'u.s.a.' -> 'usa', 'u.k.' -> 'uk').
    5. Removes periods and standardizes various terms related to universities.
    6. Stores the processed substrings in a dictionary indexed by order of appearance.

    Parameters:
        string (str): The input string to process.

    Returns:
        dict: A dictionary where each key is an index, and the value is a processed substring.
    """
    
    for old, new in replacements.items():
        string = string.replace(old, new)
        string = string.replace('hospitalum','hospital').replace('hospitalen','hospital')
    split_strings0 = split_string_with_protection(string, protected_phrases1)
    split_strings = [x.replace(',',' ') if x.split(',')[0] == 'university' or  x.split(',')[0] == 'univ' else x for  x in split_strings0]
    
    # Define a set of university-related terms for later use


    dict_string = {}
    index = 0    
    for value in split_strings:
        if  'u.s.a.' in value:
            value = value.replace('u.s.a.', 'usa')
        if  'u.k.' in value:
            value = value.replace('u.k.', 'uk')
        if  'u.a.e' in value:
            value = value.replace('u.a.e.', 'uae')        
        
        value = value.replace('.', ' ')
        # Check if the substring contains any university-related terms
        if not any(term in value.lower() for term in university_terms):
            # Apply regex substitutions for common patterns
   
            modified_value = re.sub(r'universi\w*', 'universi', value, flags=re.IGNORECASE)
            modified_value = re.sub(r'institu\w*', 'institu', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'centre\b', 'center', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'\bsaint\b', 'st', modified_value, flags=re.IGNORECASE) 
            modified_value = re.sub(r'\btrinity col\b', 'trinity colege', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'\btechnische\b', 'technological', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'\bteknologi\b', 'technology', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'\bpolitehnica\b', 'polytechnic', modified_value, flags=re.IGNORECASE)

            

            # Add the modified substring to the dictionary
                     
            dict_string[index] = modified_value.lower().strip()
            index += 1

            # Add the original substring to the dictionary
        else:
            dict_string[index] = value.lower().strip()
            index += 1
            
    return dict_string




def clean_string(input_string):
    # Temporarily replace " - " with a unique placeholder
    placeholder = "placeholder"
  #  input_string = input_string.replace(" - ", placeholder)
    input_string = input_string.replace(" – ", placeholder)

    # Unescape HTML entities and convert to lowercase
    input_string = replace_underscore(replace_comma_spaces(replace_double_consonants(unidecode(process_parentheses(fully_unescape(input_string.replace(" ́e","e").replace("'", ""))))))).strip()
    
    
    
    # Replace `–` with space (do not replace hyphen `-`)
    result = re.sub(r'[\-]', ' ', input_string)
    
    # Replace "saint" with "st"
    result = re.sub(r'\bSaint\b', 'St', result)
    result = re.sub(r'\bAghia\b', 'Agia', result)
    result = re.sub(r'\bAghios\b', 'Agios', result)

    
    # Remove characters that are not from the Latin alphabet, or allowed punctuation
    #result = replace_comma_spaces(re.sub(r'[^a-zA-Z\s,;/.]', '', result).strip())
    result = remove_multi_digit_numbers(replace_comma_spaces(re.sub(r'[^a-zA-Z0-9\s,;/.]', '', result).strip()))
    
    
    # Restore the " - " sequence from the placeholder
    result = result.replace(placeholder, " – ")
    
    # Replace consecutive whitespace with a single space
    result = re.sub(r'\s+', ' ', result)
    
    result = replace_roman_numerals(remove_stop_words(insert_space_between_lower_and_upper(result).lower()))
    

    return result.strip()  # Strip leading/trailing spaces

def description(aff_string):
    descr = []
    countries_ = []
    words = re.split(r'[ ,;]+', aff_string)
    for w in words:
        # if w in city_names:
        #     descr.append('city')
        if w in countries:
            descr.append('country')
            countries_.append(w)
        elif w in ['universi', 'institu', 'hospital' ,'hopital']:
            descr.append('basic_key')
        elif w == 'and':
            descr.append('and')

        elif w in key_words and categ_dicts[w] == 'Specific':
            descr.append('basic_key')
        # elif w in key_words:
        #     descr.append('key')
        else:
            descr.append('other')  # Optional: label words that don’t fit any category
        
    return [descr, countries_]


def is_subsequence(sublst, lst):
    it = iter(lst)
    return all(item in it for item in sublst)


def split_and(string):
    """
    Processes a given string by splitting it on commas and replacing specific occurrences 
    of 'and' with a comma when certain word sequences are detected.

    Parameters:
        string (str): The input string to process.

    Returns:
        str: The modified string with adjusted 'and' replacements.
    """
    tokens = string.split(',')
    
    replace_sequence = ["basic_key", "and", "basic_key"]

    processed_tokens = []
    
    for token in tokens:
        token = token.strip()
        token_description = description(token)[0]  # Store once instead of calling multiple times

        if is_subsequence(replace_sequence, token_description):
       
            token = ' '.join(token.replace(' and ', ', ').split())
        else:
            token = ' '.join(token.replace(' and ', ' ').split())

        processed_tokens.append(token)
    
    return ', '.join(processed_tokens)


def reduce(aff_string):    

    light_aff =  remove_outer_parentheses(remove_leading_numbers(aff_string))
    
    
    aff_no_symbols_d =  substrings_dict(light_aff)
    substring_list = list(aff_no_symbols_d.values())
    #light_aff_final = ', '.join((substring_list))
    light_aff_final = split_and(', '.join((substring_list)))
    
    
    desc = description(light_aff_final)[0]
    if (
    ('universi' in desc and 'country' in desc and desc.index('universi') < desc.index('country')) or
   # ('hospital' in desc and 'country' in desc and desc.index('hospital') < desc.index('country')) or
    ('specific' in desc and 'country' in desc and desc.index('specific') < desc.index('country'))
    ):

        result_affil = ' '.join(light_aff_final.split()[:description(light_aff_final)[0].index('country')+1])+ ', '+' '.join(light_aff_final.split()[description(light_aff_final)[0].index('country')+1:])
    else:
        result_affil = light_aff_final
    return result_affil
    
        
def unique_subset(L, D):
    seen_values = set()
    result = []

    for key in L:
        value = D[key[0]]
        if value not in seen_values:
            seen_values.add(value)
            result.append(key)
    
    return result


def str_radius_u(string, radius_u):    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if 'univers' in x:
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius_u)
        lmax =min(r0+radius_u, len(str_list))
        s = str_list[lmin:lmax+1]
        
        result.append(' '.join(s))
    
    return result 


def str_radius_coll(string):
    radius = 1
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if 'col' in x:
            indices.append(i)
  
    for r0 in indices:
        lmin =max(0,r0-radius)
        lmax =min(r0+radius, len(str_list))
        s = str_list[lmin:lmax]
        
        result.append(' '.join(s))
    
    return result 


def str_radius_h(string, radius_h):
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if 'hospital' in x or 'hopita' in x:
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius_h-1)
        lmax =min(r0+radius_h, len(str_list))
        s = str_list[lmin:lmax]
        
        result.append(' '.join(s))
    
    return result 


def str_radius_c(string):
    radius = 2
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if 'clinic' in x or 'klinik' in x:
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius-1)
        lmax =min(r0+radius, len(str_list))
        s = str_list[lmin:lmax]
        
        result.append(' '.join(s))
    
    return result 

def str_radius_r(string):
    radius = 2
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if 'research' in x:
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius-1)
        lmax =min(r0+radius, len(str_list))
        s = str_list[lmin:lmax]
        
        result.append(' '.join(s))
    
    return result 

def str_radius_spec(string):
    spec = False
    for x in string.split():
        try:
            if categ_dicts[x] == 'Specific':
                spec = True
                return x
        except:
            pass
    if spec == False:
        return string        
        




def shorten_keywords(affiliations_simple, radius_u):
    affiliations_simple_n = []

    for aff in affiliations_simple:
        if aff in dix_org:
            affiliations_simple_n.append(aff)

        elif 'universi' in aff:
            affiliations_simple_n.extend(str_radius_u(aff, radius_u))
        
        # # elif 'col' in aff and 'trinity' in aff:
        # #     affiliations_simple_n.extend(str_radius_coll(aff))
        
        # elif 'hospital' in aff or 'hopita' in aff:
        #    affiliations_simple_n.extend(str_radius_h(aff, radius_h))
        # elif 'clinic' in aff or 'klinik' in aff:
        #     affiliations_simple_n.extend(str_radius_c(aff))
        # if 'research council' in aff:
        #     affiliations_simple_n.extend(str_radius_r(aff))
        else:
            affiliations_simple_n.append(str_radius_spec(aff))
        # else:
        #     affiliations_simple_n.append(aff)       


    return affiliations_simple_n



