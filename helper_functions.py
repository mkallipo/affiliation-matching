import pandas as pd
import re
import unicodedata
from unidecode import unidecode
from collections import defaultdict
import html

import pickle

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


################# Helper functions #################

def is_contained(s, w):
    words = s.split()  # Split the string 's' into a list of words
    for word in words:
        if word not in w:  # If a word from 's' is not found in 'w'
            return False  # Return False immediately
    return True  # If all words from 's' are found in 'w', return True


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


def substrings_dict(string):
    # Split the input string and clean each substring
    split_strings = [s.strip() for s in re.split(r'[,;/]', string) if s.strip()]

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


            # Add the modified substring to the dictionary
            dict_string[index] = modified_value.lower() 
            index += 1
        elif 'universitetskaya' in value.lower():
            index += 1

                
            # Add the original substring to the dictionary
        else:
            dict_string[index] = value.lower() 
            index += 1
                
    return dict_string


def clean_string(input_string):
    # Replace specified characters with space
    input_string = remove_stop_words(replace_umlauts(unidecode(remove_parentheses(html.unescape(input_string.lower())))))
    result = re.sub(r'[/\-]', ' ', input_string)
    result = re.sub(r'\bsaint\b', 'st', result) 

    # Remove characters that are not from the Latin alphabet or numbers
    result = re.sub(r'[^a-zA-Z0-9\s,;/-]', '', result)
    
    # Replace consecutive whitespace with a single space
    result = re.sub(r'\s+', ' ', result)
    
    return result


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



uni_list = ['research', 'institu', 'istitut', 'univ', 'coll', 'center','polytechnic','politecnico','centre' , 'cnrs', 
            'faculty','school' , 'academ' , 'akadem','école', 'hochschule' , 'ecole', 'tech', 'observ','escuela','escola', 'ku leuven', 'ucla', 'eth zurich','athena', 'openaire',
            'erasmus', 'ist austria']

lab_list = ['lab', 'science','cientific']

hosp_list = ['hospital' ,'clinic', 'hopital', 'klinik','oncol','medical','health', 'medicin']

gmbh_list = ['gmbh', 'company' , 'industr', 'etaireia' , 'corporation', 'inc']

mus_list =  ['museum', 'library']

found_list =  ['foundation' , 'association','organization' ,'society', 'group','royal' ]

dept_list = ['district' , 'federation'  , 'government' , 'municipal' , 'county','council', 'agency']
# miistry -> out

unknown_list = ['unknown']


#################   Dictionaries #################

uni_dict = {k: 'Univ/Inst' for k in uni_list}   

lab_dict = {k: 'Laboratory' for k in lab_list} 

hospl_dict = {k: 'Hospital' for k in hosp_list}   

gmbh_dict = {k: 'Company' for k in gmbh_list}   

mus_dict = {k: 'Museum' for k in mus_list}   

#schoolDict = {k: 'School' for k in schoolList}   

found_dict = {k: 'Foundation' for k in found_list}   

dept_dict = {k: 'Government' for k in dept_list}   

unknown_dict =  {k: 'Unknown' for k in unknown_list}   

categ_dicts_list = [uni_dict, lab_dict, hospl_dict, gmbh_dict, mus_dict,  
                  found_dict, dept_dict, unknown_dict]


################# Final Dictionary #################

categ_dicts = {}
i = 0
while i in range(len(categ_dicts_list)):
    categ_dicts.update(categ_dicts_list[i])
    i = i+1
    
    

################# Create df for the algorithm #################


def create_df_algorithm(gendf):
    all_affs_list = []

    for doi in list(gendf['Unique affiliations']):
        for aff in doi:
            if aff not in all_affs_list:
                all_affs_list.append(aff)


    gendf1 = gendf.copy()
    
    aff_no_symbols_d = {}

    for x in list(gendf1['Unique affiliations']):
        for y in x:
            if y!= 'inc' and y not in list(aff_no_symbols_d.keys()):
              #  aff_no_symbols_d[y] = (remove_stop_words(re.sub(r'[^\w\s,Α-Ωα-ωぁ-んァ-ン一-龯,;/]', '', replace_umlauts(unidecode(remove_parentheses(html.unescape(y)))))).lower()).replace("  ", " ")
                aff_no_symbols_d[y] = clean_string(y)

        
    aff_df = pd.DataFrame.from_dict(aff_no_symbols_d, orient='index')
    aff_df.reset_index(inplace = True)
    aff_df.rename(columns = {'index':'Original affiliations', 0:'Short affiliations'}, inplace = True)
    
    new_aff_komma = []

    for aff in list(aff_df['Short affiliations']):
        new_aff_komma.append(substrings_dict(aff))
        
        
    for dict in new_aff_komma:
    
        if len(dict)>1:
            for i in range(len(dict)-1):
                if is_contained('progr', dict[i]) and is_contained('dep', dict[i+1]):
                    del dict[i]
                elif (is_contained('assistant', dict[i]) or is_contained('researcher', dict[i]) or is_contained('phd', dict[i]) or is_contained('student', dict[i]) or is_contained('section', dict[i]) or is_contained('prof', dict[i]) or is_contained('director', dict[i])) and (not is_contained('school', dict[i+1]) or is_contained('univ', dict[i+1]) or is_contained('inst', dict[i+1]) or is_contained('lab', dict[i+1]) or is_contained('fac', dict[i+1])):
                    del dict[i]
                elif (is_contained('engineer', dict[i]) or is_contained('progr', dict[i]) or is_contained('unit', dict[i]) or is_contained('lab', dict[i]) or is_contained('dep', dict[i]) or  is_contained('school', dict[i])  or is_contained('inst', dict[i]) or is_contained('hosp', dict[i]) or is_contained('fac', dict[i])) and is_contained('univ', dict[i+1]):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
                elif is_contained('lab', dict[i]) and (is_contained('college', dict[i+1]) or is_contained('inst', dict[i+1]) or is_contained('dep', dict[i+1]) or is_contained('school', dict[i+1])):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
                elif is_contained('dep', dict[i]) and (is_contained('tech', dict[i+1]) or is_contained('college', dict[i+1]) or is_contained('inst', dict[i+1]) or  is_contained('hosp', dict[i+1]) or  is_contained('school', dict[i+1]) or  is_contained('fac', dict[i+1])):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
                elif is_contained('inst',dict[i]) and (is_contained('school', dict[i+1]) or is_contained('dep', dict[i+1]) or is_contained('acad', dict[i+1]) or is_contained('hosp', dict[i+1]) or is_contained('clin', dict[i+1]) or is_contained('klin', dict[i+1])  or is_contained('fak', dict[i+1]) or is_contained('fac', dict[i+1]) or is_contained('cent', dict[i+1]) or is_contained('div', dict[i+1])):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
           #     elif is_contained('hosp',dict[i]) and is_contained('school', dict[i+1]):
            #        if not is_contained('univ', dict[i]):
             #           del dict[i]
            
    light_aff = []
    for dict in new_aff_komma:
        light_aff.append(', '.join(list(dict.values())))



    remove_list = ['universi','research institute','laboratory' ,'gmbh', 'inc', 'universi of', 'research center', 'foundation', 'faculty',
    'universi college','national institute', 'school medicine', "universi school", 'graduate school', 'graduate school engineering', 
    'institute tropical medicine', 'institute virology', 'faculty medicine','laboratory', 'universi park', 'institute science','polytechnic universi', 'universi 1',
    'ciudad universi', 'universi campus']  

    city_names = ["College Park","Aberdeen", "Abilene", "Akron", "Albany", "Albuquerque", "Alexandria", "Allentown", "Amarillo", "Anaheim", "Anchorage", "Ann Arbor", "Antioch", "Apple Valley", "Appleton", "Arlington", "Arvada", "Asheville", "Athens", "Atlanta", "Atlantic City", "Augusta", "Aurora", "Austin", "Bakersfield", "Baltimore", "Barnstable", "Baton Rouge", "Beaumont", "Bel Air", "Bellevue", "Berkeley", "Bethlehem", "Billings", "Birmingham", "Bloomington", "Boise", "Boise City", "Bonita Springs", "Boston", "Boulder", "Bradenton", "Bremerton", "Bridgeport", "Brighton", "Brownsville", "Bryan", "Buffalo", "Burbank", "Burlington", "Cambridge", "Canton", "Cape Coral", "Carrollton", "Cary", "Cathedral City", "Cedar Rapids", "Champaign", "Chandler", "Charleston", "Charlotte", "Chattanooga", "Chesapeake", "Chicago", "Chula Vista", "Cincinnati", "Clarke County", "Clarksville", "Clearwater", "Cleveland", "College Station", "Colorado Springs", "Columbia", "Columbus", "Concord", "Coral Springs", "Corona", "Corpus Christi", "Costa Mesa", "Dallas", "Daly City", "Danbury", "Davenport", "Davidson County", "Dayton", "Daytona Beach", "Deltona", "Denton", "Denver", "Des Moines", "Detroit", "Downey", "Duluth", "Durham", "El Monte", "El Paso", "Elizabeth", "Elk Grove", "Elkhart", "Erie", "Escondido", "Eugene", "Evansville", "Fairfield", "Fargo", "Fayetteville", "Fitchburg", "Flint", "Fontana", "Fort Collins", "Fort Lauderdale", "Fort Smith", "Fort Walton Beach", "Fort Wayne", "Fort Worth", "Frederick", "Fremont", "Fresno", "Fullerton", "Gainesville", "Garden Grove", "Garland", "Gastonia", "Gilbert", "Glendale", "Grand Prairie", "Grand Rapids", "Grayslake", "Green Bay", "GreenBay", "Greensboro", "Greenville", "Gulfport-Biloxi", "Hagerstown", "Hampton", "Harlingen", "Harrisburg", "Hartford", "Havre de Grace", "Hayward", "Hemet", "Henderson", "Hesperia", "Hialeah", "Hickory", "High Point", "Hollywood", "Honolulu", "Houma", "Houston", "Howell", "Huntington", "Huntington Beach", "Huntsville", "Independence", "Indianapolis", "Inglewood", "Irvine", "Irving", "Jackson", "Jacksonville", "Jefferson", "Jersey City", "Johnson City", "Joliet", "Kailua", "Kalamazoo", "Kaneohe", "Kansas City", "Kennewick", "Kenosha", "Killeen", "Kissimmee", "Knoxville", "Lacey", "Lafayette", "Lake Charles", "Lakeland", "Lakewood", "Lancaster", "Lansing", "Laredo", "Las Cruces", "Las Vegas", "Layton", "Leominster", "Lewisville", "Lexington", "Lincoln", "Little Rock", "Long Beach", "Lorain", "Los Angeles", "Louisville", "Lowell", "Lubbock", "Macon", "Madison", "Manchester", "Marina", "Marysville", "McAllen", "McHenry", "Medford", "Melbourne", "Memphis", "Merced", "Mesa", "Mesquite", "Miami", "Milwaukee", "Minneapolis", "Miramar", "Mission Viejo", "Mobile", "Modesto", "Monroe", "Monterey", "Montgomery", "Moreno Valley", "Murfreesboro", "Murrieta", "Muskegon", "Myrtle Beach", "Naperville", "Naples", "Nashua", "Nashville", "New Bedford", "New Haven", "New London", "New Orleans", "New York", "New York City", "Newark", "Newburgh", "Newport News", "Norfolk", "Normal", "Norman", "North Charleston", "North Las Vegas", "North Port", "Norwalk", "Norwich", "Oakland", "Ocala", "Oceanside", "Odessa", "Ogden", "Oklahoma City", "Olathe", "Olympia", "Omaha", "Ontario", "Orange", "Orem", "Orlando", "Overland Park", "Oxnard", "Palm Bay", "Palm Springs", "Palmdale", "Panama City", "Pasadena", "Paterson", "Pembroke Pines", "Pensacola", "Peoria", "Philadelphia", "Phoenix", "Pittsburgh", "Plano", "Pomona", "Pompano Beach", "Port Arthur", "Port Orange", "Port Saint Lucie", "Port St. Lucie", "Portland", "Portsmouth", "Poughkeepsie", "Providence", "Provo", "Pueblo", "Punta Gorda", "Racine", "Raleigh", "Rancho Cucamonga", "Reading", "Redding", "Reno", "Richland", "Richmond", "Richmond County", "Riverside", "Roanoke", "Rochester", "Rockford", "Roseville", "Round Lake Beach", "Sacramento", "Saginaw", "Saint Louis", "Saint Paul", "Saint Petersburg", "Salem", "Salinas", "Salt Lake City", "San Antonio", "San Bernardino", "San Buenaventura", "San Diego", "San Francisco", "San Jose", "Santa Ana", "Santa Barbara", "Santa Clara", "Santa Clarita", "Santa Cruz", "Santa Maria", "Santa Rosa", "Sarasota", "Savannah", "Scottsdale", "Scranton", "Seaside", "Seattle", "Sebastian", "Shreveport", "Simi Valley", "Sioux City", "Sioux Falls", "South Bend", "South Lyon", "Spartanburg", "Spokane", "Springdale", "Springfield", "St. Louis", "St. Paul", "St. Petersburg", "Stamford", "Sterling Heights", "Stockton", "Sunnyvale", "Syracuse", "Tacoma", "Tallahassee", "Tampa", "Temecula", "Tempe", "Thornton", "Thousand Oaks", "Toledo", "Topeka", "Torrance", "Trenton", "Tucson", "Tulsa", "Tuscaloosa", "Tyler", "Utica", "Vallejo", "Vancouver", "Vero Beach", "Victorville", "Virginia Beach", "Visalia", "Waco", "Warren", "Washington", "Waterbury", "Waterloo", "West Covina", "West Valley City", "Westminster", "Wichita", "Wilmington", "Winston", "Winter Haven", "Worcester", "Yakima", "Yonkers", "York", "Youngstown"]

    city_names = [x.lower() for x in city_names]


    for dict in new_aff_komma:
        for i in list(dict.keys()):

            if dict[i] in city_names+remove_list:
                del dict[i]




    aff_df['Light affiliations'] = light_aff
    aff_df['Keywords'] =  [list(d.values()) for d in new_aff_komma]
    
    affiliations_dict = {}

    for i in range(len(aff_df)):
        affiliations_dict[i] = aff_df['Keywords'].iloc[i]
        
    d_new = {}

    # iterate over the keys of affiliations_dict
    for k in range(len(affiliations_dict)):
        # get the list associated with the current key in affiliations_dict
        L = affiliations_dict.get(k, [])
        mapped_listx = [[s, v] for s in L for k2, v in categ_dicts.items() if k2 in s]
        

        # add the mapped list to the new dictionary d_new
        d_new[k] = mapped_listx
        
    aff_df['Dictionary'] = list(d_new.values())
    
    category = [', '.join(list(set([x[1] for x in aff_df['Dictionary'].iloc[i]]))) for i in range(len(aff_df))]
    
    aff_df.loc[:, 'Category'] = category
    
    for i in range(len(aff_df)):
        if aff_df['Category'].iloc[i] == '':
            aff_df.iloc[i, aff_df.columns.get_loc('Category')] = 'Rest'


    affiliations_simple = [
        list(set([x[0] for x in aff_df['Dictionary'].iloc[i]]))
        for i in range(len(aff_df))
    ]


    aff_df['Keywords'] = affiliations_simple
    
    affiliations_simple_n = []

    for i in range(len(affiliations_simple)):
        inner = []
        for str in affiliations_simple[i]:
            if 'universi' in str:
                for x in str_radius_u(str):
                    inner.append(x)
            elif 'hospital' in str or 'hopita' in str:
                for x in str_radius_h(str):
                    inner.append(x)
            elif 'clinic' in str or 'klinik' in str:
                for x in str_radius_c(str):
                    inner.append(x)
                    
            else:
                inner.append(str)
        
        affiliations_simple_n.append(inner)      
        
    aff_df['Keywords'] = affiliations_simple_n
    
    univ_labs = [i for i in range(len(aff_df)) if 'Laboratory' in aff_df['Category'].iloc[i] 
            or 'Univ/Inst' in  aff_df['Category'].iloc[i] 
            or 'Hospital' in  aff_df['Category'].iloc[i]
            or 'Foundation' in  aff_df['Category'].iloc[i]]
            
        
    univ_labs_df = aff_df.iloc[univ_labs].copy()
    univ_labs_df.reset_index(inplace = True)
    univ_labs_df.drop(columns = ['index'], inplace = True)
    
    return univ_labs_df




################# Create df for the algorithm [facts's data] #################


def create_df_algorithm_facts(gendf):
    all_affs_list = []

    for doi in list(gendf['Unique affiliations']):
        for aff in doi:
            if aff not in all_affs_list:
                all_affs_list.append(aff)


    gendf1 = gendf.copy()
    
    aff_no_symbols_d ={}

    for x in list(gendf1['Unique affiliations']):
        for y in x:
            if y!= 'inc' and y not in list(aff_no_symbols_d.keys()):
                #aff_no_symbols_d[y] = (remove_stop_words(re.sub(r'[^\w\s,Α-Ωα-ωぁ-んァ-ン一-龯,;/]', '', replace_umlauts(unidecode(remove_parentheses(html.unescape(y)))))).lower()).replace("  ", " ")
                aff_no_symbols_d[y] = clean_string(y)
        
    
        
    aff_df = pd.DataFrame.from_dict(aff_no_symbols_d, orient='index')
    aff_df.reset_index(inplace = True)
    aff_df.rename(columns = {'index':'Original affiliations', 0:'Short affiliations'}, inplace = True)
    
    new_aff_komma = []

    for aff in list(aff_df['Short affiliations']):
        new_aff_komma.append(substrings_dict(aff))
                
        
    for dict in new_aff_komma:
    
        if len(dict)>1:
            for i in range(len(dict)-1):
                if is_contained('progr', dict[i]) and is_contained('dep', dict[i+1]):
                    del dict[i]
                elif (is_contained('assistant', dict[i]) or is_contained('researcher', dict[i]) or is_contained('phd', dict[i]) or is_contained('student', dict[i]) or is_contained('section', dict[i]) or is_contained('prof', dict[i]) or is_contained('director', dict[i])) and (not is_contained('school', dict[i+1]) or is_contained('univ', dict[i+1]) or is_contained('inst', dict[i+1]) or is_contained('lab', dict[i+1]) or is_contained('fac', dict[i+1])):
                    del dict[i]
                elif (is_contained('engineer', dict[i]) or is_contained('progr', dict[i]) or is_contained('unit', dict[i]) or is_contained('lab', dict[i]) or is_contained('dep', dict[i]) or  is_contained('school', dict[i])  or is_contained('inst', dict[i]) or is_contained('hosp', dict[i]) or is_contained('fac', dict[i])) and is_contained('univ', dict[i+1]):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
                elif is_contained('lab', dict[i]) and (is_contained('college', dict[i+1]) or is_contained('inst', dict[i+1]) or is_contained('dep', dict[i+1]) or is_contained('school', dict[i+1])):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
                elif is_contained('dep', dict[i]) and (is_contained('tech', dict[i+1]) or is_contained('college', dict[i+1]) or is_contained('inst', dict[i+1]) or  is_contained('hosp', dict[i+1]) or  is_contained('school', dict[i+1]) or  is_contained('fac', dict[i+1])):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
                elif is_contained('inst',dict[i]) and (is_contained('school', dict[i+1]) or is_contained('dep', dict[i+1]) or is_contained('acad', dict[i+1]) or is_contained('hosp', dict[i+1]) or is_contained('clin', dict[i+1]) or is_contained('klin', dict[i+1])  or is_contained('fak', dict[i+1]) or is_contained('fac', dict[i+1]) or is_contained('cent', dict[i+1]) or is_contained('div', dict[i+1])):
                    if not is_contained('univ', dict[i]):
                        del dict[i]
            #    elif is_contained('hosp',dict[i]) and is_contained('school', dict[i+1]):
             #       if not is_contained('univ', dict[i]):
             #           del dict[i]
            #   elif is_contained('hos',dict[i]) and (is_contained('cen', dict[i+1]):
            #       del dict[i+1]
            
    light_aff = []
    for dict in new_aff_komma:
        light_aff.append(', '.join(list(dict.values())))
        
    


    remove_list = ['universi','research institute','laboratory' ,'gmbh', 'inc', 'universi', 'research center', 'foundation', 'faculty',
    'universi college','national institute', 'school medicine', "universi school", 'graduate school', 'graduate school engineering', 
    'institute tropical medicine', 'institute virology', 'faculty medicine','laboratory', 'universi park', 'institute science','polytechnic universi', 'universi 1',
    'ciudad universi','school pharmacy','bioinformatics centre']    #remove_list = ['universi','research institute','laboratory' ,'gmbh', 'inc', 'universi of',# 'research center', 'foundation, 
     #              'faculty',
    #'universi college','national institute of', 'school of medicine', "universi school", 'graduate school', 'graduate school engineering', 
    #'institute tropical medicine', 'institute virology', 'faculty medicine','laboratory', 'universi park', 'institute science','polytechnic universi', 'universi 1',
    #'ciudad universi']

    city_names = ["Universitetskaya", "College Park","Aberdeen", "Abilene", "Akron", "Albany", "Albuquerque", "Alexandria", "Allentown", "Amarillo", "Anaheim", "Anchorage", "Ann Arbor", "Antioch", "Apple Valley", "Appleton", "Arlington", "Arvada", "Asheville", "Athens", "Atlanta", "Atlantic City", "Augusta", "Aurora", "Austin", "Bakersfield", "Baltimore", "Barnstable", "Baton Rouge", "Beaumont", "Bel Air", "Bellevue", "Berkeley", "Bethlehem", "Billings", "Birmingham", "Bloomington", "Boise", "Boise City", "Bonita Springs", "Boston", "Boulder", "Bradenton", "Bremerton", "Bridgeport", "Brighton", "Brownsville", "Bryan", "Buffalo", "Burbank", "Burlington", "Cambridge", "Canton", "Cape Coral", "Carrollton", "Cary", "Cathedral City", "Cedar Rapids", "Champaign", "Chandler", "Charleston", "Charlotte", "Chattanooga", "Chesapeake", "Chicago", "Chula Vista", "Cincinnati", "Clarke County", "Clarksville", "Clearwater", "Cleveland", "College Station", "Colorado Springs", "Columbia", "Columbus", "Concord", "Coral Springs", "Corona", "Corpus Christi", "Costa Mesa", "Dallas", "Daly City", "Danbury", "Davenport", "Davidson County", "Dayton", "Daytona Beach", "Deltona", "Denton", "Denver", "Des Moines", "Detroit", "Downey", "Duluth", "Durham", "El Monte", "El Paso", "Elizabeth", "Elk Grove", "Elkhart", "Erie", "Escondido", "Eugene", "Evansville", "Fairfield", "Fargo", "Fayetteville", "Fitchburg", "Flint", "Fontana", "Fort Collins", "Fort Lauderdale", "Fort Smith", "Fort Walton Beach", "Fort Wayne", "Fort Worth", "Frederick", "Fremont", "Fresno", "Fullerton", "Gainesville", "Garden Grove", "Garland", "Gastonia", "Gilbert", "Glendale", "Grand Prairie", "Grand Rapids", "Grayslake", "Green Bay", "GreenBay", "Greensboro", "Greenville", "Gulfport-Biloxi", "Hagerstown", "Hampton", "Harlingen", "Harrisburg", "Hartford", "Havre de Grace", "Hayward", "Hemet", "Henderson", "Hesperia", "Hialeah", "Hickory", "High Point", "Hollywood", "Honolulu", "Houma", "Houston", "Howell", "Huntington", "Huntington Beach", "Huntsville", "Independence", "Indianapolis", "Inglewood", "Irvine", "Irving", "Jackson", "Jacksonville", "Jefferson", "Jersey City", "Johnson City", "Joliet", "Kailua", "Kalamazoo", "Kaneohe", "Kansas City", "Kennewick", "Kenosha", "Killeen", "Kissimmee", "Knoxville", "Lacey", "Lafayette", "Lake Charles", "Lakeland", "Lakewood", "Lancaster", "Lansing", "Laredo", "Las Cruces", "Las Vegas", "Layton", "Leominster", "Lewisville", "Lexington", "Lincoln", "Little Rock", "Long Beach", "Lorain", "Los Angeles", "Louisville", "Lowell", "Lubbock", "Macon", "Madison", "Manchester", "Marina", "Marysville", "McAllen", "McHenry", "Medford", "Melbourne", "Memphis", "Merced", "Mesa", "Mesquite", "Miami", "Milwaukee", "Minneapolis", "Miramar", "Mission Viejo", "Mobile", "Modesto", "Monroe", "Monterey", "Montgomery", "Moreno Valley", "Murfreesboro", "Murrieta", "Muskegon", "Myrtle Beach", "Naperville", "Naples", "Nashua", "Nashville", "New Bedford", "New Haven", "New London", "New Orleans", "New York", "New York City", "Newark", "Newburgh", "Newport News", "Norfolk", "Normal", "Norman", "North Charleston", "North Las Vegas", "North Port", "Norwalk", "Norwich", "Oakland", "Ocala", "Oceanside", "Odessa", "Ogden", "Oklahoma City", "Olathe", "Olympia", "Omaha", "Ontario", "Orange", "Orem", "Orlando", "Overland Park", "Oxnard", "Palm Bay", "Palm Springs", "Palmdale", "Panama City", "Pasadena", "Paterson", "Pembroke Pines", "Pensacola", "Peoria", "Philadelphia", "Phoenix", "Pittsburgh", "Plano", "Pomona", "Pompano Beach", "Port Arthur", "Port Orange", "Port Saint Lucie", "Port St. Lucie", "Portland", "Portsmouth", "Poughkeepsie", "Providence", "Provo", "Pueblo", "Punta Gorda", "Racine", "Raleigh", "Rancho Cucamonga", "Reading", "Redding", "Reno", "Richland", "Richmond", "Richmond County", "Riverside", "Roanoke", "Rochester", "Rockford", "Roseville", "Round Lake Beach", "Sacramento", "Saginaw", "Saint Louis", "Saint Paul", "Saint Petersburg", "Salem", "Salinas", "Salt Lake City", "San Antonio", "San Bernardino", "San Buenaventura", "San Diego", "San Francisco", "San Jose", "Santa Ana", "Santa Barbara", "Santa Clara", "Santa Clarita", "Santa Cruz", "Santa Maria", "Santa Rosa", "Sarasota", "Savannah", "Scottsdale", "Scranton", "Seaside", "Seattle", "Sebastian", "Shreveport", "Simi Valley", "Sioux City", "Sioux Falls", "South Bend", "South Lyon", "Spartanburg", "Spokane", "Springdale", "Springfield", "St. Louis", "St. Paul", "St. Petersburg", "Stamford", "Sterling Heights", "Stockton", "Sunnyvale", "Syracuse", "Tacoma", "Tallahassee", "Tampa", "Temecula", "Tempe", "Thornton", "Thousand Oaks", "Toledo", "Topeka", "Torrance", "Trenton", "Tucson", "Tulsa", "Tuscaloosa", "Tyler", "Utica", "Vallejo", "Vancouver", "Vero Beach", "Victorville", "Virginia Beach", "Visalia", "Waco", "Warren", "Washington", "Waterbury", "Waterloo", "West Covina", "West Valley City", "Westminster", "Wichita", "Wilmington", "Winston", "Winter Haven", "Worcester", "Yakima", "Yonkers", "York", "Youngstown"]

    city_names = [x.lower() for x in city_names]


    for dict in new_aff_komma:
        for i in list(dict.keys()):

            if dict[i] in city_names+remove_list:
                del dict[i]


  


    aff_df['Light affiliations'] = light_aff
    aff_df['Keywords'] =  [list(d.values()) for d in new_aff_komma]
    
    affiliations_dict = {}

    for i in range(len(aff_df)):
        affiliations_dict[i] = aff_df['Keywords'].iloc[i]
        
    d_new = {}

    # iterate over the keys of affiliations_dict
    for k in range(len(affiliations_dict)):
        # get the list associated with the current key in affiliations_dict
        L = affiliations_dict.get(k, [])
        mapped_listx = [[s, v] for s in L for k2, v in categ_dicts.items() if k2 in s]
        

        # add the mapped list to the new dictionary d_new
        d_new[k] = mapped_listx
        
    aff_df['Dictionary'] = list(d_new.values())
    
    category = [', '.join(list(set([x[1] for x in aff_df['Dictionary'].iloc[i]]))) for i in range(len(aff_df))]
    
    aff_df.loc[:, 'Category'] = category
    
    for i in range(len(aff_df)):
        if aff_df['Category'].iloc[i] == '':
            aff_df.iloc[i, aff_df.columns.get_loc('Category')] = 'Rest'


    affiliations_simple = [
        list(set([x[0] for x in aff_df['Dictionary'].iloc[i]]))
        for i in range(len(aff_df))
    ]


    aff_df['Keywords'] = affiliations_simple
    
    affiliations_simple_n = []

    for i in range(len(affiliations_simple)):
        inner = []
        for str in affiliations_simple[i]:
            if 'universi' in str:
                for x in str_radius_u(str):
                    inner.append(x)
            elif 'hospital' in str or 'hopita' in str:
                for x in str_radius_h(str):
                    inner.append(x)
            elif 'clinic' in str or 'klinik' in str:
                for x in str_radius_c(str):
                    inner.append(x)
                    
            else:
                inner.append(str)
        
        affiliations_simple_n.append(inner)      
        
    aff_df['Keywords'] = affiliations_simple_n #affiliations_simple_n

                  
    univ_labs_df = aff_df.copy()
    univ_labs_df.drop(columns = ['Short affiliations'], inplace = True)
    
    return univ_labs_df
    
