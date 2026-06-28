import re
import unicodedata
import html
from unidecode import unidecode
from collections import defaultdict
import json   
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from importlib.resources import files
import gzip

# ---------------------------------------------------------------------------
# Pre-compiled regexes used by normalize_organization_names (called many
# times per run_affro invocation — compiling once avoids repeated parsing).
# ---------------------------------------------------------------------------
_RE_UNIVER        = re.compile(r'univer\w*',                re.IGNORECASE)
_RE_EUROP         = re.compile(r'europ\w*',                 re.IGNORECASE)
_RE_INSTIT        = re.compile(r'instit\w*',                re.IGNORECASE)
_RE_HOPITAL       = re.compile(r'hopital\b',                re.IGNORECASE)
_RE_HOSPITAL      = re.compile(r'hospital(?!s)\w*',         re.IGNORECASE)
_RE_GEN_HOSPITAL  = re.compile(r'\bgeneral hospital\b',     re.IGNORECASE)
_RE_GEN_UNI_HOSP  = re.compile(r'\bgeneral univer hospital\b', re.IGNORECASE)
_RE_SCIENCES      = re.compile(r'sciences\b',               re.IGNORECASE)
_RE_SCIENZE       = re.compile(r'scienze\b',                re.IGNORECASE)
_RE_SCIENZA       = re.compile(r'scienza\b',                re.IGNORECASE)
_RE_LABORA        = re.compile(r'labora\w*',                re.IGNORECASE)
_RE_CENTRE        = re.compile(r'centre\b',                 re.IGNORECASE)
_RE_CENTRUM       = re.compile(r'centrum\b',                re.IGNORECASE)
_RE_MEDISCH       = re.compile(r'medisch\b',                re.IGNORECASE)
_RE_SAINT         = re.compile(r'\bsaint\b',                re.IGNORECASE)
_RE_TRINITY       = re.compile(r'\btrinity col\b',          re.IGNORECASE)
_RE_TECHNISCHE    = re.compile(r'\btechnische\b',           re.IGNORECASE)
_RE_TEKNOLOGI     = re.compile(r'\bteknologi\b',            re.IGNORECASE)
_RE_POLITEHNICA   = re.compile(r'\bpolitehnica\b',          re.IGNORECASE)
_RE_POLITE        = re.compile(r'\bpolite\w*',              re.IGNORECASE)
_RE_POLYTE        = re.compile(r'\bpolyte\w*',              re.IGNORECASE)
_RE_PANEPIST      = re.compile(r'panepist\w*',              re.IGNORECASE)
_RE_ARISTOT       = re.compile(r'\baristot\w*',             re.IGNORECASE)
_RE_TECHN         = re.compile(r'\btechn\w*',               re.IGNORECASE)
_RE_CZECHOSLOVAK  = re.compile(r'\bczechoslovak\b',         re.IGNORECASE)
_RE_MACAU         = re.compile(r'\bmacau\b',                re.IGNORECASE)
_RE_MUNCHEN       = re.compile(r'\bmunchen\b',              re.IGNORECASE)
_RE_ORGANISATION  = re.compile(r'organisation\b',           re.IGNORECASE)
_RE_XI_AN         = re.compile(r'\bxi an\b',               re.IGNORECASE)
_RE_MULTI_SPACE   = re.compile(r'\s+')

        
def load_json(relative_path, package="affro"):
    """
    Safely load a gzipped JSON file from the package.
    relative_path: path relative to the package root, e.g. 'jsons/dix_acad.json.gz'
    package: name of the top-level package
    """
    full_path = files(package).joinpath(relative_path)
    with gzip.open(full_path, "rt", encoding="utf-8") as f:
        return json.load(f)
    
    
def load_txt(relative_path, package="affro"):
    """
    Safely load a text file from the package.
    Returns a list of stripped lines.
    """
    full_path = files(package).joinpath(relative_path)
    with full_path.open("r", encoding="utf-8") as file:
        return [line.strip() for line in file]

_replacements_cache = None

def get_replacements():
    global _replacements_cache
    if _replacements_cache is None:
        _replacements_cache = load_json('jsons/replacements.json.gz')
    return _replacements_cache

categ_string = 'Academia|Hospitals|Foundations|Specific|Government|Company|Acronyms'

us_states = {
    "alabama", "alaska", "arizona", "arkansas", "california",
    "colorado", "conecticut", "delaware", "florida", "georgia",
    "hawaii", "idaho", "ilinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland",
    "masachusets", "michigan", "minesota", "misisipi", "misouri",
    "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "carolina", "dakota", "ohio",
    "oklahoma", "oregon", "pensylvania", "rhode island",
    "dakota", "tenesee", "texas", "utah", "vermont",
    "virginia", "washington", "wisconsin", "wyoming","beth","boston","chicago","ucla"
}

low_prob_countries = {'st kits nevis', 'kenya','malaysia','philipines','burundi',
                      'cambodia','bangladesh','bolivia','azerbaijan', 
                      'bosnia herzegovina', 'iran','islamabad', 
                      'zimbabwe', 'oman', 'iraq', 'yemen', 'somalia', 'sri lanka','costa rica','indonesia'}

dix_name = load_json('./jsons/dix_name.json.gz')

dix_country_legalnames = load_json('./jsons/dix_country_legalnames.json.gz')
dix_key_legalnames = load_json('./jsons/dix_keys_names.json.gz')

def replace_double_consonants(text):
    # This regex pattern matches any double consonant
    pattern = r'([bcdfghjklmnpqrstvwxyz])\1'
    # The replacement is the first captured group (the single consonant)
    result = re.sub(pattern, r'\1', text, flags=re.IGNORECASE)
    return result


#stop_words = ['from', 'the', 'of', 'at', 'de','for','et','für','des', 'in','as','a','and','fur','for','und','di']

def remove_stop_words(text):
    text = text.replace('present adres', '')
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
  
dix_id = load_json('jsons/dix_id.json.gz')

categ_dicts = load_json('jsons/dix_categ.json.gz')
#replacements = load_json('jsons/replacements.json.gz')
key_words = list(categ_dicts.keys()) + ['univer', 'labora']
countries =  load_txt('txts/country_names.txt')
remove_list = [replace_double_consonants(x) for x in load_txt('txts/remove_list.txt')]
stop_words.remove('and')
stop_words.remove('at')
university_terms = [replace_double_consonants(x) for x in load_txt('txts/university_terms.txt')]
city_names = [replace_double_consonants(x) for x in load_txt('txts/city_names.txt')]

# Pre-compile abbreviation cache for faster lookup (thousands of times faster)
_abbr_univ_cache = {}
for _city in city_names:
    _abbr_univ_cache[_city + " u"] = _city + " univer"
    _abbr_univ_cache["u " + _city] = "univer " + _city
    _abbr_univ_cache["tu " + _city] = "techn univer " + _city

def is_first(id, name):
    for quadruple in dix_name[name]:
        if quadruple['id'] == id:
            return quadruple['first']


country_synonyms = {x: [x] for x in countries}
country_synonyms["united states"] = ["united states", "u.s.a.", "usa", "usa.", "states"] + [x for x in us_states]
country_synonyms["germany"] = ["germany", "deutschland"]
country_synonyms["united kingdom"] = ["united kingdom", "u.k.", "uk", "uk.", "kingdom", "england"]
country_synonyms["turkey"] = ["turkey", "turkiye", "cyprus"]
country_synonyms["china"] = ["china", "prc", "chinese"]
country_synonyms["ireland"] = ["eire", "ireland"]
country_synonyms["south korea"] = ["south korea", "korea"]
country_synonyms["new zealand"] = ["new zealand", "zealand"]
country_synonyms["italy"] = ["italy", "milan", "rome", "italia", "pisa"]

# 1️⃣ Define equivalence classes (each set is a group of mutually equivalent countries)
country_equivalence_groups = [
    {"united states", "u.s.a.", "usa", "usa.", "states","canada"},
    {"germany", "deutschland"},
    {"united kingdom", "u.k.", "uk", "uk.", "kingdom", "england","ireland", "eire"},
    {"turkey", "turkiye", "cyprus","greece", "macedonia"},
    {"china", "prc", "chinese"},
    {"south korea", "korea"},
    {"new zealand", "zealand"},
]


# 2️⃣ Build a symmetric lookup for all countries
country_to_group = {}
for group in country_equivalence_groups:
    for country in group:
        country_to_group[country] = group

        
# 3️⃣ Define the function
def get_candidates(country_list, key_list):
    # Candidate names from keys
    cand_names = {
        name
        for key in key_list
        if key in dix_key_legalnames
        for name in dix_key_legalnames[key]
    }

    # Remove empty/falsy country entries
    country_list = [c for c in country_list if c]

    if country_list:
        # Expand countries using equivalence classes
        expanded_countries = {
            synonym
            for c in country_list
            for synonym in country_to_group.get(c, {c})
        }

        # Collect legal names from expanded countries
        country_names = {
            name
            for country in expanded_countries
            if country in dix_country_legalnames
            for name in dix_country_legalnames[country]
        }

        return cand_names & country_names

    return cand_names


sp_all = [k for k in categ_dicts if categ_dicts[k] == 'Acronyms' or  categ_dicts[k] == 'Specific']


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
    pattern = r'\b((?:univer))\s+(department|faculty)\b'
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
    if 'inserm' in text or 'cnrs' in text:
        return re.sub(r'\b\d{5,}\b', '', text).strip()
    else:
        return re.sub(r'\b\d{4,}\b', '', text).strip()

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
    protected = ['DePaul',
        'AstraZeneca',
        'BioNTech',
        'GlaxoSmithKline',
        'LifeWatch',
        'SoBigData',
        'GmbH',
        'gGmbH',
        'gmbH',
        'OpenAIRE',
        'LaserVision',
        'PhD'
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
    """Optimized lookup using pre-compiled cache instead of linear iteration."""
    return _abbr_univ_cache.get(token, token)
            

def remove_parentheses(text):
   return re.sub(r'\([^()]*\)', '', text)

acronyms = [x for x, cat in categ_dicts.items() if cat == 'Acronyms']
L = ['univ', 'hospital', 'clinic', 'klinik', 'Univ', 'Hospital', 'Clinic', 'Klinik'] + [s.title() for s in countries] + countries + acronyms

word_pattern = "|".join(map(re.escape, L))

_RE_PAREN_REMOVE = re.compile(r'\((?![^)]*(' + word_pattern + r'))[^)]*\)')
_RE_PAREN_REPLACE = re.compile(r'\(([^)]*(' + word_pattern + r')[^)]*)\)')

def process_parentheses(text):
    """
    Processes parentheses in a given text by:
    1. Removing parentheses that do not contain any word from the list L.
    2. Replacing parentheses with commas if they contain a word from the list.

    Parameters:
        text (str): The input string containing parentheses.

    Returns:
        str: The modified string after processing parentheses.
    """
    text_lower = replace_double_consonants(text.lower())
    text_lower = _RE_PAREN_REMOVE.sub('', text_lower)
    text_lower = _RE_PAREN_REPLACE.sub(r', \1,', text_lower)

    return text_lower



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
    with `repl` (default: space), except:
      - '\r' (and '\\r') are replaced with ','

    Then collapse repeated whitespace to a single space and trim ends.
    """

    if text is None:
        return text

    text = html.unescape(text)

    # Replace carriage returns with comma
    text = re.sub(r"(\\r|\r)", ",", text)

    pattern = re.compile(
        r"""(
            \#r\#\#n\# | \#r\# | \#n\# |
            \^p | ¶ |
            <br\s*/?> |
            &#0*13; | &#0*10; |
            &#x0*0d; | &#x0*0a; |
            \\r\\n | \\n | \\u000a | \\u000d | \\x0a | \\x0d |
            \r\n | \n
        )""",
        flags=re.IGNORECASE | re.VERBOSE,
    )

    cleaned = pattern.sub(repl, text)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned

def replace_newlines_with_space1(text: str, repl: str = " ") -> str:
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

def normalize_organization_names(value, university_terms):
    """
    Normalize organization names by applying a series of regex substitutions
    and standardizations.
    
    Args:
        value (str): Organization name substring.
        university_terms (list of str): List of terms indicating a university.
        
    Returns:
        str: Normalized organization name.
    """
    
    # Replace dots with spaces and collapse multiple spaces
    modified_value = value.replace('.', ' ')
    modified_value = _RE_MULTI_SPACE.sub(' ', modified_value).strip()
    
    # Protect compound university terms (e.g. universitatszahnklinik) with placeholders
    # so that plain "universitat" etc. still get shortened to "univer" in the same string.
    placeholders = {}
    for i, term in enumerate(university_terms):
        if term.lower().startswith('univer') or term.lower().startswith('hospital'):
            key = f'__UNIV_{i}__'
            modified_value = re.sub(re.escape(term), key, modified_value, flags=re.IGNORECASE)
            placeholders[key] = term

    modified_value = _RE_UNIVER.sub('univer', modified_value)

    # General substitutions (all using pre-compiled patterns)
    modified_value = _RE_EUROP.sub('europ', modified_value)
    modified_value = _RE_INSTIT.sub('instit', modified_value)
    modified_value = _RE_HOPITAL.sub('hospital', modified_value)
    modified_value = _RE_HOSPITAL.sub('hospital', modified_value)
    modified_value = _RE_GEN_HOSPITAL.sub('hospital', modified_value)
    modified_value = _RE_GEN_UNI_HOSP.sub('univer hospital', modified_value)
    modified_value = _RE_SCIENCES.sub('science', modified_value)
    modified_value = _RE_SCIENZE.sub('science', modified_value)
    modified_value = _RE_SCIENZA.sub('science', modified_value)
    modified_value = _RE_LABORA.sub('labora', modified_value)
    modified_value = _RE_CENTRE.sub('center', modified_value)
    modified_value = _RE_CENTRUM.sub('center', modified_value)
    modified_value = _RE_MEDISCH.sub('medical', modified_value)
    modified_value = _RE_SAINT.sub('st', modified_value)
    modified_value = _RE_TRINITY.sub('trinity colege', modified_value)
    modified_value = _RE_TECHNISCHE.sub('technological', modified_value)
    modified_value = _RE_TEKNOLOGI.sub('technology', modified_value)
    modified_value = _RE_POLITEHNICA.sub('polytechnic', modified_value)
    modified_value = _RE_POLITE.sub('polytechnic', modified_value)
    modified_value = _RE_POLYTE.sub('polytechnic', modified_value)
    modified_value = _RE_PANEPIST.sub('univer', modified_value)
    modified_value = _RE_ARISTOT.sub('aristot', modified_value)
    modified_value = _RE_TECHN.sub('techn', modified_value)
    modified_value = _RE_CZECHOSLOVAK.sub('czech', modified_value)
    modified_value = _RE_MACAU.sub('macao', modified_value)
    modified_value = _RE_MUNCHEN.sub('munich', modified_value)
    modified_value = _RE_ORGANISATION.sub('organization', modified_value)
    modified_value = _RE_XI_AN.sub('xian', modified_value)

    # Restore all protected compound terms (universit- and hospital- prefixed)
    for key, original in placeholders.items():
        modified_value = modified_value.replace(key, original)

    return modified_value
    
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
    for old, new in get_replacements().items():
        string = string.replace(old, new)

    split_strings = [replace_acronyms(s).strip() for s in re.split(r' - | – |[,;/:|]', string) if s.strip()]

    # Define a set of university-related terms for later use


    dict_string = {}
    index = 0 
    
   
    for value in split_strings:
        modified_value = normalize_organization_names(value, university_terms)

            # Add the modified substring to the dictionary
                     
        dict_string[index] = modified_value.lower().strip()
        index += 1

            # Add the original substring to the dictionary
       
    return dict_string

countries_set = set(countries)


def split_country(text):
    parts = text.split(' ')

    if len(parts) < 2:
        return text

    if parts[-1] in countries_set and not parts[-2].startswith('univ'):
        return " ".join(parts[:-1]) + ", " + parts[-1]

    return text
    


def clean_string_lucky(input_string):

    input_string = replace_underscore(replace_comma_spaces(replace_double_consonants(unidecode(process_parentheses(fully_unescape(input_string.replace("’","'").replace(" ́e","e").replace("'s", "s").replace("'", "").replace('"', ' '))))))).strip()
    
    result = remove_stop_words(replace_roman_numerals(input_string.lower()))
    result = result.replace(' and ',' ')
    result = result.replace('general hospital', 'hospital')

    for old, new in get_replacements().items():
        result = result.replace(old, new)

    # Remove characters that are not from the Latin alphabet, or allowed punctuation
    result = remove_multi_digit_numbers(replace_comma_spaces(re.sub(r'[^a-zA-Z0-9\s,;/:.\-\—]', '', result).strip()))
    
    # Restore the " - " sequence from the placeholder
    #result = result.replace(placeholder, " – ")
    result = result.replace(':',' ').replace(';',' ').replace('-',' ').replace('—',' ').replace(',',' ')
    # Replace consecutive whitespace with a single space
    
    result = replace_acronyms(result).replace('.', ' ')
    result = normalize_organization_names(result, university_terms)

    return result.strip()

    
def clean_string_ror(input_string):

    input_string = replace_underscore(replace_comma_spaces(replace_double_consonants(unidecode(remove_parentheses(fully_unescape(input_string.replace("’","'").replace(" ́e","e").replace("'s", "s").replace("'", "").replace('"', ' '))))))).strip()
    
    result = remove_stop_words(replace_roman_numerals(input_string.lower()))
    result = result.replace(' and ',' ')

    # Remove characters that are not from the Latin alphabet, or allowed punctuation
    result = remove_multi_digit_numbers(replace_comma_spaces(re.sub(r'[^a-zA-Z0-9\s,;/:.\-\—]', '', result).strip()))
    
    # Restore the " - " sequence from the placeholder
    #result = result.replace(placeholder, " – ")
    result = result.replace(':',' ').replace(';',' ').replace('-',' ').replace('—',' ').replace(',',' ')
    # Replace consecutive whitespace with a single space

    
    result = replace_acronyms(result).replace('.', ' ')
    result = normalize_organization_names(result, university_terms)

    deutsch_replacements = {
        'universitatsklinikum': 'univer hospital',
        'universitetshospital': 'univer hospital',
        'universitatskinderklinik': 'univer childrens hospital',
        'universitatskliniken': 'univer hospital',
        'universitaetsklinikum': 'univer hospital',
        'universitatsklinik': 'univer hospital',
        'universiteitsmuseum': 'univer museum',
        'universitatspital': 'univer hospital',
        'universitatsmedizin': 'univer medicine',
        'universitatsbibliothek': 'univer library',
        'universitatsverlag': 'univer pres',
        'universitetsforlaget': 'univer pres',
        'universitatsaugenklinik': 'univer eye hospital',
        'univesitatsfrauenklinik': 'univer hospital',
        'universitetscentralsjukhus': 'univer hospital',
        'universitetsjukhuset': 'univer hospital',
        'pamantasan': 'univer'
    }
    
    words = result.split()
    updated_words = []
    for word in words:
        if word in deutsch_replacements:
            updated_words.append(deutsch_replacements[word])
        else:
            updated_words.append(word)
    
    result = ' '.join(updated_words)
    return result.strip()

def clean_string(input_string):
    input_string = replace_underscore(replace_comma_spaces(unidecode(process_parentheses(insert_space_between_lower_and_upper(fully_unescape(replace_newlines_with_space(input_string).replace("P.O. Box","").replace("’","'").replace(" ́e","e").replace("'s", "s").replace('"', ' '))))))).strip()
    
 #   result = re.sub(r'(?<! )[–—-](?! )', ' ', input_string)

  #  print('h',input_string)

    result = remove_stop_words(replace_double_consonants(replace_roman_numerals((input_string).lower().replace("'", ""))))

    
    # Remove characters that are not from the Latin alphabet, or allowed punctuation
    result = remove_multi_digit_numbers(replace_comma_spaces(re.sub(r'[^a-zA-Z0-9\s,;/:|.\-\—]', '', result).strip()))
    #result = normalize_organization_names(result, university_terms)

    
    # Restore the " - " sequence from the placeholder
    #result = result.replace(placeholder, " – ")
    
    # Replace consecutive whitespace with a single space
    result = re.sub(r'\s+', ' ', result)
    
    #result = replace_roman_numerals(remove_stop_words(insert_space_between_lower_and_upper(result).lower()))
    
    return result.strip() # Strip leading/trailing spaces

    return split_country(result.strip())  # Strip leading/trailing spaces

def description(aff_string):
    aff_string = aff_string.replace('turkiye', 'turkey').lower()
    aff_string = aff_string.replace('kirgizistan', 'kyrgyzstan')
    aff_string = aff_string.replace('u.s.a.', 'usa').replace('u.k.', 'uk').replace('macau','macao')
    descr = []
    countries_ = []
    words = re.split(r'[ ,;:/.-]', aff_string)
#    words = [word.strip() for word in re.split(r'[,;:]+', aff_string) if word.strip()]

    for w in words:
        # if w in city_names:
        #     descr.append('city')
        w = re.sub(r'[^A-Za-z\s]', '', w)
        if replace_acronyms(w) in countries:
            descr.append('country')
            countries_.append(w)
            
        if (
        replace_acronyms(w) in us_states
        or any(
            state in aff_string
            for state in ('new york', 'new hampshire', 'new jersey', 'new mexico')
        )
    ):

            
        # if replace_acronyms(w) in us_states or any(['new york', "new hampshire", "new jersey", "new mexico"] in aff_string.lower()):
            descr.append('country')
            countries_.append('usa')   
            countries_.append('mexico')   
      
        elif w in ['univer', 'instit', 'hospital', 'labora', 'colege', 'foundation'] or w in sp_all:
            
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
            if tok_no_sl1 not in dix_name:
                parts = re.split(r'\s*-\s*', token)
                if len(parts) >= 2:  # there is a dash in the current token
                    if ('basic_key' in description(parts[0])[0]
                            and 'basic_key' in description(parts[-1])[0]):
                        token = re.sub(r'\s*-\s*', ', ', token)
                    else:
                        token = tok_no_sl1
                # else: no dash in current token, leave it unchanged
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
    # print('aff_no_symbols_d',aff_no_symbols_d)
    substring_list = list(aff_no_symbols_d.values())
    light_aff_final = ', '.join((substring_list))
    # print('h', substring_list)
    light_aff_final = split_and(', '.join((substring_list)))
    # print('th', light_aff_final)
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
    n = len(str_list)
    result = []

    for i, x in enumerate(str_list):
        if 'univer' in x or 'colege' in x:
            s = str_list[max(0, i - radius_u): min(i + radius_u + 1, n)]
            result.append(' '.join(s))
    
    return result


sp_specific = [k for k in categ_dicts if categ_dicts[k] == 'Specific' and ' ' in k]

# only_specific = [k for k in categ_dicts if categ_dicts[k] == 'Specific']    
# #
# def str_radius_spec(string):
#     spec = False
#     for x in only_specific:
#         if x in string:# or categ_dicts[x] == 'Acronyms':
#             spec = True
#             return x
#     if spec ==False:
#         return string        

def str_radius_spec(string):
    spec = False
    for x in sp_specific:
        if x in string:# or categ_dicts[x] == 'Acronyms':
            spec = True
            return x
    if spec ==False:
        return string 


def shorten_keywords0(affiliations_simple, radius_u):
    affiliations_simple_n = []

    for aff in affiliations_simple:
        # print('check aff', aff)
        if aff in dix_name:
            affiliations_simple_n.append(aff)

        elif 'univer' in aff:
            affiliations_simple_n.extend(str_radius_u(aff, radius_u))
        elif 'colege' in aff:
            
            affiliations_simple_n.extend(str_radius_u(aff, radius_u))

        elif 'research' in aff:
            affiliations_simple_n.append(aff)

        affiliations_simple_n.append(str_radius_spec(aff))
            
    return list(set(affiliations_simple_n))

def shorten_keywords(affiliations_simple, radius_u):
    affiliations_simple_n = []

    for aff in affiliations_simple:
        # print('check aff', aff)
        
        if aff in dix_name:
            affiliations_simple_n.append(aff)
            
      
                   

        elif 'univer' in aff:
            affiliations_simple_n.extend(str_radius_u(aff, radius_u))
        elif 'colege' in aff:
            
            affiliations_simple_n.extend(str_radius_u(aff, radius_u))

        elif 'research' in aff:
            affiliations_simple_n.append(aff)

        else:
            for x in aff.split():
                if categ_dicts.get(x) in {'Acronyms', 'Specific'}:
                    affiliations_simple_n.append(x)
                
        affiliations_simple_n.append(str_radius_spec(aff))

    return list(set(affiliations_simple_n))

