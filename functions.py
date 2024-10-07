import re
import unicodedata
import html
import json
from unidecode import unidecode
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_txt(file_path):
    with open(file_path, 'r') as file:
        list_ = [line.strip() for line in file]
        return list_
    
def load_json(file_path): 
    with open(file_path, 'r') as json_file:
        json_dict = json.load(json_file)
        return json_dict

categ_string = 'Laboratory|Univ/Inst|Hospital|Foundation|Specific|Museum'

remove_list = load_txt('remove_list.txt')
stop_words = load_txt('stop_words.txt')
university_terms = load_txt('university_terms.txt')
city_names = load_txt('city_names.txt')

categ_dicts = load_json('dictionaries/dix_categ.json')

def replace_double_consonants(text):
    # This regex pattern matches any double consonant
    pattern = r'([bcdfghjklmnpqrstvwxyz])\1'
    # The replacement is the first captured group (the single consonant)
    result = re.sub(pattern, r'\1', text, flags=re.IGNORECASE)
    return result

def is_contained(s, w):
    words = s.split()  # Split the string 's' into a list of words
    for word in words:
        if word not in w:  # If a word from 's' is not found in 'w'
            return False  # Return False immediately
    return True  # If all words from 's' are found in 'w', return True

def starts_with_any(string, prefixes):
    for prefix in prefixes:
        if string.startswith(prefix):
            return [True, prefix]
    return False

def remove_leading_numbers(s):
    return re.sub(r'^\d+', '', s)

def remove_outer_parentheses(string):
    """Remove outer parentheses from the string if they enclose the entire string."""
    if string.startswith('(') and string.endswith(')'):
        return string[1:-1].strip()
    return string

def insert_space_between_lower_and_upper(s):
    """
    Inserts a space between a lowercase letter followed by an uppercase letter in a string.

    Parameters:
    s (str): The input string.

    Returns:
    str: The modified string with spaces inserted.
    """
    # Use regex to insert space between lowercase and uppercase letters
    modified_string = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
    return modified_string

def avg_string(df, col):
    avg = [] 
    for i in range(len(df)):
        avg.append(sum(len(s) for s in df[col].iloc[i])/len(df[col].iloc[i]))
    return sum(avg)/len(avg)

stop_words = ['from', 'the', 'of', 'at', 'de','for','et','für','des', 'in','as','a','and','fur','for','und']


def remove_stop_words(text):
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words]
    return ' '.join(filtered_words)


def remove_parentheses(text):
   return re.sub(r'\([^()]*\)', '', text)


# def replace_umlauts(text):
#     normalized_text = unicodedata.normalize('NFKD', text)
#     replaced_text = ''.join(c for c in normalized_text if not unicodedata.combining(c))
#     return replaced_text

def protect_phrases(input_string, phrases):
    # Replace phrases with placeholders
    placeholder_map = {}
    for i, phrase in enumerate(phrases):
        placeholder = f"__PLACEHOLDER_{i}__"
        placeholder_map[placeholder] = phrase
        input_string = input_string.replace(phrase, placeholder)
    return input_string, placeholder_map

def replace_comma_spaces(text):
    return text.replace('  ', ' ').replace(' , ', ', ')

def restore_phrases(split_strings, placeholder_map):
    # Restore placeholders with original phrases
    restored_strings = []
    for s in split_strings:
        for placeholder, phrase in placeholder_map.items():
            s = s.replace(placeholder, phrase)
        restored_strings.append(s)
    return restored_strings

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
        'university california, {x}',
    #    'university california , {x}',

        'university colege hospital, {x}',
    #    'university colege hospital , {x}',
        
        'national univ ireland, {x}',
    #    'national univ ireland , {x}',

        'national university ireland, {x}',
    #    'national university ireland , {x}',

        'university colege, {x}',
    #    'university colege , {x}',
        
        'university hospital, {x}', 
    #    'university hospital , {x}', 

        'imperial colege, {x}',
    #    'imperial colege , {x}'
        
        'city university, {x}', 
    #    'city university , {x}'

        
    ]
]

replacements =  {'saint' : 'st',
                'aghia' : 'agia', 
                'universitatsklinikum' : 'universi hospital',
                'universitetshospital' : 'universi hospital',
                'universitatskinderklinik' : 'universi childrens hospital',
                'universitatskliniken': 'universi hospital',
                'Universitätsklinik': 'universi hospital',
                'universitatsmedizin': 'universi medicine',
                'universitatsbibliothek' : 'universi library',
                'nat.':'national',
                'uni versity':'university',
                'unive rsity': 'university',
                'univ ersity': 'university',
                'inst ':'institute ',
                'adv ':'advanced ',
                'univ ':'university ',
                'stud ': 'studies ',
                'inst.':'institute',
                'adv.':'advanced',
                'univ.':'university',
                'stud.': 'studies',                 
                'univercity':'university', 
                'univerisity':'university', 
                'universtiy':'university', 
                'univeristy':'university',
                'universirty':'university', 
                'universiti':'university', 
                'universitiy':'university',
                'universty' :'university',
                'univ col': 'university colege',
                'univ. col.': 'university colege',
                'univ. coll.': 'university colege',
                'col.':'colege',
                'army' : 'military',
                'hipokration' : 'hipocration',
                'belfield, dublin': 'dublin',
                'balsbridge, dublin': 'dublin', #ballsbridge
                'earlsfort terrace, dublin': 'dublin',
                'bon secours hospital, cork' : 'bon secours hospital cork',
                'bon secours hospital, dublin' : 'bon secours hospital dublin',
                'bon secours hospital, galway' : 'bon secours hospital galway',
                'bon secours hospital, tralee' : 'bon secours hospital tralee',
                'bon secours health system' : 'bon secours hospital dublin',
                'bon secours hospital, glasnevin' : 'bon secours hospital dublin',
                'imperial colege science, technology medicine' : 'imperial colege science technology medicine',
                'ucl queen square institute neurology' : 'ucl, london',
                'ucl institute neurology' : 'ucl, london',
                'royal holoway, university london' : 'royal holoway universi london', #holloway
                'city, university london' : 'city universi london',
                'city university, london' : 'city universi london',
                'aeginition':'eginition',
                'national technical university, athens' : 'national technical university athens' 
            # 'harvard medical school' : 'harvard univers
}


def substrings_dict(string):
    # Split the input string and clean each substring
   # split_strings =  split_string_with_protection(string.replace('univ coll', 'university college').replace('belfield, dublin', 'dublin').replace('ballsbridge, dublin', 'dublin').replace('earlsfort Terrace, dublin', 'dublin'), protected_phrases1)
    
    for old, new in replacements.items():
        string = string.replace(old, new)
        string = string.replace('hospitalum','hospital').replace('hospitalen','hospital')
    split_strings = split_string_with_protection(string, protected_phrases1)
    
    # Define a set of university-related terms for later use


    dict_string = {}
    index = 0    
    for value in split_strings:
        value = value.replace('.', ' ')

        # Check if the substring contains any university-related terms
        if not any(term in value.lower() for term in university_terms):
            # Apply regex substitutions for common patterns
   
            modified_value = re.sub(r'universi\w*', 'universi', value, flags=re.IGNORECASE)
            modified_value = re.sub(r'institu\w*', 'institu', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'centre*', 'center', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'\bsaint\b', 'st', modified_value, flags=re.IGNORECASE) 
            modified_value = re.sub(r'\btrinity col\b', 'trinity colege', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'\btechnische\b', 'technological', modified_value, flags=re.IGNORECASE)

            

            # Add the modified substring to the dictionary
                     
            dict_string[index] = modified_value.lower().strip()
            index += 1
       # elif 'universitetskaya' in value.lower():
       #     index += 1


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
    input_string = replace_comma_spaces(replace_double_consonants(unidecode(remove_parentheses(html.unescape(input_string.replace("'", ""))))).strip())
    
    # Replace `–` with space (do not replace hyphen `-`)
    result = re.sub(r'[\-]', ' ', input_string)
    
    # Replace "saint" with "st"
    result = re.sub(r'\bSaint\b', 'St', result)
    result = re.sub(r'\bAghia\b', 'Agia', result)
    result = re.sub(r'\bAghios\b', 'Agios', result)

    
    # Remove characters that are not from the Latin alphabet, or allowed punctuation
    result = replace_comma_spaces(re.sub(r'[^a-zA-Z\s,;/.]', '', result).strip())
    
    # Restore the " - " sequence from the placeholder
    result = result.replace(placeholder, " – ")
    
    # Replace consecutive whitespace with a single space
    result = re.sub(r'\s+', ' ', result)
    #result = result.replace('ss', 's')
    
    result = insert_space_between_lower_and_upper(result).lower()
    result = remove_stop_words(result)
    return result.strip()  # Strip leading/trailing spaces


def clean_string_facts(input_string):
    # Replace specified characters with space
    input_string = remove_stop_words(unidecode(remove_parentheses(html.unescape(input_string.lower()))))
    result = re.sub(r'[/\-,]', ' ', input_string)
    result = re.sub(r'\bsaint\b', 'st', result) 

    # Remove characters that are not from the Latin alphabet or numbers
    result = re.sub(r'[^a-zA-Z0-9\s;/-.]', '', result)
    
    # Replace consecutive whitespace with a single space
    result = re.sub(r'\s+', ' ', result)
    
    return result
    
    
def str_radius_u(string):
    string = string.lower()
    radius = 3
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if is_contained('univers',x):
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius)
        lmax =min(r0+radius, len(str_list))
        s = str_list[lmin:lmax+1]
        
        result.append(' '.join(s))
    
    return result 

def str_radius_coll(string):
    string = string.lower()
    radius = 1
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if is_contained('col',x):
            indices.append(i)
  
    for r0 in indices:
        lmin =max(0,r0-radius)
        lmax =min(r0+radius, len(str_list))
        s = str_list[lmin:lmax]
        
        result.append(' '.join(s))
    
    return result 

def str_radius_h(string):
    string = string.lower()
    radius = 3
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if is_contained('hospital',x) or is_contained('hopita',x):
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius-1)
        lmax =min(r0+radius, len(str_list))
        s = str_list[lmin:lmax]
        
        result.append(' '.join(s))
    
    return result 


def str_radius_c(string):
    string = string.lower()
    radius = 2
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if is_contained('clinic',x) or is_contained('klinik',x):
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius-1)
        lmax =min(r0+radius, len(str_list))
        s = str_list[lmin:lmax]
        
        result.append(' '.join(s))
    
    return result 

def str_radius_r(string):
    string = string.lower()
    radius = 2
    
    str_list = string.split()
    indices = []
    result = []

    for i, x in enumerate(str_list):
        if is_contained('research',x):
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
        
def avg_string(df, col):
    avg = [] 
    for i in range(len(df)):
        avg.append(sum(len(s) for s in df[col].iloc[i])/len(df[col].iloc[i]))
    return sum(avg)/len(avg)



        
                                
def shorten_keywords(affiliations_simple):
    affiliations_simple_n = []

    for aff in affiliations_simple:
        inner = []
        for str in aff:
            if 'universi' in str:
                inner.extend(str_radius_u(str))
            elif 'col' in str and 'trinity' in str:
                inner.extend(str_radius_coll(str))
            elif 'hospital' in str or 'hopita' in str:
                inner.extend(str_radius_h(str))
            elif 'clinic' in str or 'klinik' in str:
                inner.extend(str_radius_c(str))
            elif 'research council' in str:
                inner.extend(str_radius_r(str))
            else:
                inner.append(str_radius_spec(str))

        affiliations_simple_n.append(inner)

    return affiliations_simple_n
