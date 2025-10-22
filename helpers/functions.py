import re
import unicodedata
import html
from unidecode import unidecode
from collections import defaultdict
import json   
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_txt(file_path):
    with open(file_path, 'r',  encoding='utf-8') as file:
        list_ = [line.strip() for line in file]
        return list_
    

def load_json(file_path): 
    with open(file_path, 'r') as json_file:
        json_dict = json.load(json_file)
        return json_dict
        
categ_string = 'Academia|Hospitals|Foundations|Specific|Government|Company|Acronyms'

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

dix_name = load_json('./jsons/dix_name.json')

dix_country_legalnames = load_json('./jsons/dix_country_legalnames.json')

def replace_double_consonants(text):
    # This regex pattern matches any double consonant
    pattern = r'([bcdfghjklmnpqrstvwxyz])\1'
    # The replacement is the first captured group (the single consonant)
    result = re.sub(pattern, r'\1', text, flags=re.IGNORECASE)
    return result


#stop_words = ['from', 'the', 'of', 'at', 'de','for','et','für','des', 'in','as','a','and','fur','for','und','di']

def remove_stop_words(text):
    words = text.split()
    filtered_words = []
    
    for word in words:
        if word.endswith(","):
            core = word[:-1]  # remove the comma
            if core not in stop_words:
                filtered_words.append(core + ",")
            else:
                filtered_words.append(",")  # keep only the comma
        else:
            if word not in stop_words:
                filtered_words.append(word)
    
    result = " ".join(filtered_words)
    # remove spaces before commas
    result = result.replace(" ,", ",")
    return result


stop_words = load_txt('txts/stop_words.txt')
  
dix_id = load_json('jsons/dix_id.json')

categ_dicts = load_json('jsons/dix_categ.json')
replacements = load_json('jsons/replacements.json')
key_words = list(categ_dicts.keys()) + ['univer', 'labora']
countries =  load_txt('txts/country_names.txt')
remove_list = [replace_double_consonants(x) for x in load_txt('txts/remove_list.txt')]
stop_words.remove('and')
stop_words.remove('at')
university_terms = [replace_double_consonants(x) for x in load_txt('txts/university_terms.txt')]
city_names = [replace_double_consonants(x) for x in load_txt('txts/city_names.txt')]



def get_candidates(country_list):
    if len(country_list) >0:
        cand =  [dix_country_legalnames[country] for country in country_list if country in dix_country_legalnames]
        return list(set([item for sublist in cand for item in sublist]))
    else:
        return list(dix_name.keys())


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

def split_sub(s: str) -> str:
    # Add comma after certain word pairs
    pattern = r'\b((?:univer))\s+(department|faculty|institu)\b'
    return re.sub(pattern, r'\1, \2', s, flags=re.IGNORECASE)


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

def remove_repeated_end(text):
    words = text.strip().split()
    if len(words) >= 2 and words[-1] == words[-2]:
        words.pop()  # Remove the last word
    return ' '.join(words)




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
    Insert a space between a lowercase letter and a following uppercase letter,
    while protecting listed substrings (case-sensitive) and restoring them in lowercase.
    """
    protected = [
        'AstraZeneca',
        'BioNTech',
        'GlaxoSmithKline',
        'LifeWatch',
        'SoBigData',
        'GmbH',
        'gGmbH',
        'gmbH'
    ]

    # Replace protected words with placeholders mapping to their lowercase versions
    placeholders = {}
    for i, word in enumerate(protected):
        key = f"__PROT_{i}__"
        s = s.replace(word, key)
        placeholders[key] = word.lower()

    # Add space between lowercase and uppercase (except after 'Mc')
    s = re.sub(r'(?<!Mc)([a-z])([A-Z])', r'\1 \2', s)
    s = re.sub(r'(Mc) ([A-Z])', r'\1\2', s)

    # Restore placeholders to lowercase
    for key, lower_word in placeholders.items():
        s = s.replace(key, lower_word)

    return s




def replace_acronyms(text):
    # Regex matches:
    # 1. Single letters followed by dots (with optional spaces)
    # 2. Ends with a single letter and optional final dot
    # 3. Excludes cases where a dot is followed by a multi-letter word
    pattern = r'(?<!\w)(?:[A-Za-z]\s*\.\s*)+[A-Za-z]\s*\.?(?!\w)(?![A-Za-z]{2,})'
    
    def replacement(match):
        # Remove all dots and spaces between letters
        return re.sub(r'[\s\.]', '', match.group(0))
    
    return re.sub(pattern, replacement, text)



def replace_abbr_univ(token):
    for city in city_names:
        if token == city + " u":
            return city + " univer"
        elif token == "u " + city:
            return "univer " + city
        elif token == "tu " + city:
            return "technical univer " + city
    else:
        return token
            

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
  

def replace_comma_spaces(text):
    return text.replace('  ', ' ').replace(' , ', ', ')

def replace_underscore(text):
    if 'University-' in text and 'University-Hospital' not in text:
        return text.replace('-',',')
    else:
        return text

def fully_unescape(text):
    """Recursively unescapes HTML-encoded text until fully decoded."""
    while True:
        new_text = html.unescape(text)
        if new_text == text:  # Stop when no more changes occur
            return new_text
        text = new_text

def replace_newlines_with_space(text: str, repl: str = " ") -> str:
    """
    Replace many variants of newline/paragraph placeholders in `text`
    with `repl` (default: a single space), then collapse repeated
    whitespace to a single space and trim ends.

    Handles:
      - real newline chars: \r, \n, \r\n
      - escaped sequences: \\n, \\r, \\r\\n, \\u000A, \\x0a
      - HTML: <br>, <br/>, HTML entities like &#10;, &#13;, &#x0A;
      - placeholder tokens: #N#, #R#, #R##N#, ^p, ¶
      - HTML entities are unescaped first (so e.g. &amp;#10; -> &#10; -> removed)
    """
    if text is None:
        return text

    # Unescape HTML entities first so numeric entities become characters or sequences we can match
    text = html.unescape(text)

    # Combined regex to match many newline/placeholder forms
    pattern = re.compile(
        r"""(
            # explicit literal placeholder forms
            \#r\#\#n\#   |   \#r\#   |   \#n\#    |
            \^p         |   ¶                   |
            # HTML break tags
            <br\s*/?>   |
            # numeric HTML entities (decimal & hex)
            &#0*13;     |   &#0*10;     |
            &#x0*0d;    |   &#x0*0a;    |
            # escaped forms (backslash sequences as text)
            \\r\\n      |   \\n       |   \\r       |   \\u000a    |   \\u000d   |   \\x0a   |   \\x0d  |
            # actual control chars
            \r\n        |   \r        |   \n
        )""",
        flags=re.IGNORECASE | re.VERBOSE,
    )

    # Replace matches with the replacement (space by default)
    cleaned = pattern.sub(repl, text)

    # Collapse repeated whitespace to a single space and trim start/end
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


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
  #  print(0, string)
    for old, new in replacements.items():
        string = string.replace(old, new)
  #      split_strings = [s.strip() for s in re.split(r'[,;/]| – ', string) if s.strip()]
        split_strings = [replace_acronyms(s).strip() for s in re.split(r' - | – |[,;/:]', string) if s.strip()]

    # Define a set of university-related terms for later use


    dict_string = {}
    index = 0 
    
  #  print('split_strings',split_strings)
   
    for value in split_strings:
        modified_value = value.replace('.', ' ')
        modified_value = re.sub(r'\s+', ' ', modified_value)

        # Check if the substring contains any university-related terms
        if not any(term in modified_value.lower() for term in university_terms):
            # Apply regex substitutions for common patterns
   
            modified_value = re.sub(r'univer\w*', 'univer', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'institu\w*', 'institu', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'hospital(?!s)\w*', 'hospital', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'labora\w*', 'labora', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'centre\b', 'center', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'centrum\b', 'center', modified_value, flags=re.IGNORECASE)        
        modified_value = re.sub(r'\bsaint\b', 'st', modified_value, flags=re.IGNORECASE) 
        modified_value = re.sub(r'\btrinity col\b', 'trinity colege', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'\btechnische\b', 'technological', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'\bteknologi\b', 'technology', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'\bpolitehnica\b', 'polytechnic', modified_value, flags=re.IGNORECASE)

        modified_value = re.sub(r'\btechn\w*', 'techn', modified_value, flags=re.IGNORECASE)
        #modified_value = re.sub(r'techno\w*', 'techno', modified_value, flags=re.IGNORECASE)
        modified_value = re.sub(r'scien\w*', 'scien', modified_value, flags=re.IGNORECASE)

            

            # Add the modified substring to the dictionary
                     
        dict_string[index] = modified_value.lower().strip()
        index += 1

            # Add the original substring to the dictionary
       
    return dict_string

def split_country(text):
    try:
        if text.split(' ')[-1].lower() in countries and startswith(text.split(' ')[-2].lower()) != 'univ':
            return " ".join(text.split(' ')[0:-1])+", "+ text.split(' ')[-1].lower()
        else:
            return text
    except:
        return text
    
def clean_string_ror(input_string):

    input_string = replace_underscore(replace_comma_spaces(replace_double_consonants(unidecode(process_parentheses(fully_unescape(input_string.replace("’","'").replace(" ́e","e").replace("'s", "s").replace("'", " "))))))).strip()
    
    result = remove_stop_words(replace_roman_numerals(input_string.lower()))
    result = result.replace(' and ',' ')


    # Remove characters that are not from the Latin alphabet, or allowed punctuation
    result = remove_multi_digit_numbers(replace_comma_spaces(re.sub(r'[^a-zA-Z0-9\s,;/:.\-\—]', '', result).strip()))
    
    # Restore the " - " sequence from the placeholder
    #result = result.replace(placeholder, " – ")
    result = result.replace(':',' ').replace(';',' ').replace('-',' ').replace('—',' ').replace(',',' ')
    # Replace consecutive whitespace with a single space
    
    

    university_terms = {'universitatsklinikum', 'universitatskinderklinik',
        'universitatspital', 'universitatskliniken', 'universitetshospital',
        'universitatsmedizin', 'universitatsbibliothek','universitatszahnklinik'
    }
    
    result = replace_acronyms(result).replace('.', ' ')
    result = re.sub(r'\s+', ' ', result)

    # Replace consecutive whitespace with a single space
    if not any(term in result.lower() for term in university_terms):

        result = re.sub(r'universi\w*', 'univer', result, flags=re.IGNORECASE)
    result = re.sub(r'\bsaint\b', 'st', result,flags=re.IGNORECASE)
    result = re.sub(r'institu\w*', 'institu', result, flags=re.IGNORECASE)
    result = re.sub(r'labora\w*', 'labora', result, flags=re.IGNORECASE)
    result = re.sub(r'centre\b', 'center', result, flags=re.IGNORECASE)
    result = re.sub(r'centrum\b', 'center', result, flags=re.IGNORECASE)        
    
    result = re.sub(r'hopital\b', 'hospital', result, flags=re.IGNORECASE)
    result = re.sub(r'hospital(?!s)\w*', 'hospital', result, flags=re.IGNORECASE)

    #result = re.sub(r'centro\b', 'center', result, flags=re.IGNORECASE)

    result = re.sub(r'\btechnische\b', 'technological', result, flags=re.IGNORECASE)
    result = re.sub(r'\bteknologi\b', 'technological', result, flags=re.IGNORECASE)
    result = re.sub(r'\bpolitehnica\b', 'polytechnic', result, flags=re.IGNORECASE)
    result = re.sub(r'czechoslovak\b', 'czech', result, flags=re.IGNORECASE)

    result = re.sub(r'\btechn\w*', 'techn', result, flags=re.IGNORECASE)
    # result = re.sub(r'techno\w*', 'techno', result, flags=re.IGNORECASE)
    result = re.sub(r'scien\w*', 'scien', result, flags=re.IGNORECASE)
   # result = re.sub(r'\bsaint\b', 'st', result, flags=re.IGNORECASE)

    return result.strip()

def clean_string(input_string):
    input_string = replace_underscore(replace_comma_spaces(unidecode(process_parentheses(fully_unescape(replace_newlines_with_space(input_string).replace("P.O. Box","").replace("’","'").replace(" ́e","e").replace("'s", "s").replace("'", " ")))))).strip()
    
 #   result = re.sub(r'(?<! )[–—-](?! )', ' ', input_string)

  #  print('h',input_string)

    result = remove_stop_words(replace_double_consonants(replace_roman_numerals(insert_space_between_lower_and_upper(input_string).lower())))

    
    # Remove characters that are not from the Latin alphabet, or allowed punctuation
    result = remove_multi_digit_numbers(replace_comma_spaces(re.sub(r'[^a-zA-Z0-9\s,;/:.\-\—]', '', result).strip()))
    
    
    # Restore the " - " sequence from the placeholder
    #result = result.replace(placeholder, " – ")
    
    # Replace consecutive whitespace with a single space
    result = re.sub(r'\s+', ' ', result)
    
    #result = replace_roman_numerals(remove_stop_words(insert_space_between_lower_and_upper(result).lower()))
    

    return split_country(result.strip())  # Strip leading/trailing spaces

def description(aff_string):
    aff_string = aff_string.replace('turkiye', 'turkey').lower()
    aff_string = aff_string.replace('kirgizistan', 'kyrgyzstan')
    
    descr = []
    countries_ = []
    words = re.split(r'[ ,;:/]+', aff_string)
#    words = [word.strip() for word in re.split(r'[,;:]+', aff_string) if word.strip()]

    for w in words:
        # if w in city_names:
        #     descr.append('city')
        w = re.sub(r'[^A-Za-z\s]', '', w)
        if replace_acronyms(w) in countries:
            descr.append('country')
            countries_.append(w)
            
        if replace_acronyms(w) in us_states:
            descr.append('country')
            countries_.append('usa')   
        
        elif w in ['univer', 'institu', 'hospital', 'labora']:
            
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
        token_description = description(token)[0]

        tok_no_and = ' '.join(token.replace(' and ', ' ').split())
        tok_no_at = ' '.join(token.replace(' at ', ' ').split())
        tok_no_an = ' '.join(token.replace(' an ', ' ').split())
        tok_no_sl1 = ' '.join(token.replace('-', ' ').split())
        tok_no_sl2 = ' '.join(token.replace('—', ' ').split())
        tok_no = ' '.join(token.replace(' and ', ' ').replace(' at ', ' ').replace(' an ', ' ').replace('-', ' ').replace('—', ' ').split())
        if tok_no in dix_name:
            token = tok_no
        
        
        else:
            if tok_no_and not in dix_name:
              # Store once instead of calling multiple times

                if is_subsequence(replace_sequence, token_description):# and token.split(' and ', ' ') not in dix_org:
            
                    token = ' '.join(token.replace(' and ', ', ').split())
                else:
                    token = tok_no_and
            else:
                token = tok_no_and
                
            if  tok_no_at not in dix_name:
                token = ' '.join(token.replace(' at ', ', ').split())
            else:
                token = tok_no_at
                    
            if  tok_no_an not in dix_name:
                token = ' '.join(token.replace(' an ', ', ').split())
            else:
                token = tok_no_an
            if  tok_no_sl1 not in dix_name:
                token = ' '.join(token.replace('-', ',').split())
            else:
                token = tok_no_sl1
            if  tok_no_sl2 not in dix_name:
                token = ' '.join(token.replace('—', ',').split())
            else:
                token = tok_no_sl2
        if token.split(' ')[0] == 'and':
           # print('HERE', token)
            token = ' '.join(token.split(' ')[1:])
        processed_tokens.append(token)
    
    return ', '.join(processed_tokens)


def reduce(light_aff):    
        
    aff_no_symbols_d =  substrings_dict(light_aff)
    substring_list = list(aff_no_symbols_d.values())
    #light_aff_final = ', '.join((substring_list))
 #   print('h', substring_list)
    light_aff_final = split_and(', '.join((substring_list)))
 #   print('th', light_aff_final)
    return split_sub(light_aff_final)
    
        
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
        if 'univer' in x:
            indices.append(i)
            
    for r0 in indices:
        lmin =max(0,r0-radius_u)
        lmax =min(r0+radius_u, len(str_list))
        s = str_list[lmin:lmax+1]
        
        result.append(' '.join(s))
    
    return result 



def str_radius_spec(string):
    spec = False
    for x in string.split():
        try:
            if categ_dicts[x] == 'Specific':# or categ_dicts[x] == 'Acronyms':
                spec = True
                return x
        except:
            pass
    if spec == False:
        return string        
    

def shorten_keywords(affiliations_simple, radius_u):
    affiliations_simple_n = []

    for aff in affiliations_simple:
    #    print('check aff', aff)
        if aff in dix_name:
            affiliations_simple_n.append(aff)

        elif 'univer' in aff:
            affiliations_simple_n.extend(str_radius_u(aff, radius_u))
        

        else:
            affiliations_simple_n.append(str_radius_spec(aff))


    return affiliations_simple_n



