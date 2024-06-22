import re
import unicodedata
import html
from unidecode import unidecode
import pickle   
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_txt(file_path):
    with open(file_path, 'r') as file:
        list_ = [line.strip() for line in file]
        return list_
    
def load_pickled_dict(file_path): 
    with open(file_path, 'rb') as file: 
        pickled_dict = pickle.load(file) 
        return pickled_dict

categ_string = 'Laboratory|Univ/Inst|Hospital|Foundation|Specific'

remove_list = load_txt('remove_list.txt')
stop_words = load_txt('stop_words.txt')
university_terms = load_txt('university_terms.txt')
city_names = load_txt('city_names.txt')

categ_dicts = load_pickled_dict('dictionaries/categ_dicts.pkl')


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


def replace_umlauts(text):
    normalized_text = unicodedata.normalize('NFKD', text)
    replaced_text = ''.join(c for c in normalized_text if not unicodedata.combining(c))
    return replaced_text

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

def split_string_with_protection(input_string, protected_phrases):
    # Step 1: Protect specific phrases
    input_string, placeholder_map = protect_phrases(input_string, protected_phrases)
    
    # Step 2: Split the string on specified delimiters
    split_strings = [s.strip() for s in re.split(r'[,;/]| – ', input_string) if s.strip()]
    
    # Step 3: Restore protected phrases
    split_strings = restore_phrases(split_strings, placeholder_map)
    
    return split_strings

protected_phrases1 = ["university california, "+x for x in city_names] + ['national university ireland, '+x for x in city_names] + ['university college, '+x for x in city_names]

def substrings_dict(string):
    # Split the input string and clean each substring
    split_strings =  split_string_with_protection(string.replace('univ coll', 'university college'), protected_phrases1)

    # Define a set of university-related terms for later use
    university_terms = {'universitetskaya', 'universitatsklinikum', 'universitatskinderklinik',
        'universitatsspital', 'universitatskliniken', 'universitetshospital',
        'universitatsmedizin', 'universitatsbibliothek'
    }

    dict_string = {}
    index = 0
     
    for value in split_strings:
        # Check if the substring contains any university-related terms
        if not any(term in value.lower() for term in university_terms):
            # Apply regex substitutions for common patterns
   
            modified_value = re.sub(r'universi\w*', 'universi', value, flags=re.IGNORECASE)
            modified_value = re.sub(r'institu\w*', 'institu', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'centre*', 'center', modified_value, flags=re.IGNORECASE)
            modified_value = re.sub(r'\bsaint\b', 'st', modified_value, flags=re.IGNORECASE) 
            modified_value = re.sub(r'\btrinity coll\b', 'trinity college', modified_value, flags=re.IGNORECASE)

            # Add the modified substring to the dictionary
            dict_string[index] = modified_value.lower() 
            index += 1
       # elif 'universitetskaya' in value.lower():
       #     index += 1

                
            # Add the original substring to the dictionary
        else:
            dict_string[index] = value.lower() 
            index += 1
    return dict_string


def clean_string(input_string):
    # Temporarily replace " - " with a unique placeholder
    placeholder = "placeholder"
  #  input_string = input_string.replace(" - ", placeholder)
    input_string = input_string.replace(" – ", placeholder)

    # Unescape HTML entities and convert to lowercase
    input_string = remove_stop_words(replace_umlauts(unidecode(remove_parentheses(html.unescape(input_string.lower())))))
    
    # Normalize unicode characters (optional, e.g., replace umlauts)
    input_string = unidecode(input_string)
    
    # Replace `/` and `–` with space (do not replace hyphen `-`)
    result = re.sub(r'[/\-]', ' ', input_string)
    
    # Replace "saint" with "st"
    result = re.sub(r'\bsaint\b', 'st', result)
    
    # Remove characters that are not from the Latin alphabet, numbers, or allowed punctuation
    result = re.sub(r'[^a-zA-Z0-9\s,;/]', '', result)
    
    # Restore the " - " sequence from the placeholder
    result = result.replace(placeholder, " – ")
    
    # Replace consecutive whitespace with a single space
    result = re.sub(r'\s+', ' ', result)
    
    return result.strip()  # Strip leading/trailing spaces


def clean_string_facts(input_string):
    # Replace specified characters with space
    input_string = remove_stop_words(replace_umlauts(unidecode(remove_parentheses(html.unescape(input_string.lower())))))
    result = re.sub(r'[/\-,]', ' ', input_string)
    result = re.sub(r'\bsaint\b', 'st', result) 

    # Remove characters that are not from the Latin alphabet or numbers
    result = re.sub(r'[^a-zA-Z0-9\s;/-]', '', result)
    
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
        if is_contained('coll',x):
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
        if is_contained('hospital',x):
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
            elif 'coll' in str and 'trinity' in str:
                inner.extend(str_radius_coll(str))
            elif 'hospital' in str or 'hopita' in str:
                inner.extend(str_radius_h(str))
            elif 'clinic' in str or 'klinik' in str:
                inner.extend(str_radius_c(str))
            else:
                inner.append(str)

        affiliations_simple_n.append(inner)

    return affiliations_simple_n
