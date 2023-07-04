# %%
"""
# Import packages
"""
import tarfile
import logging

# %%
import pandas as pd
import sys
# %%
#import plotly
#import datapane as dp
#plotly.offline.init_notebook_mode(connected=True)

# %%
import re
import unicodedata
import pickle

#import Levenshtein
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,ALL_COMPLETED

"""
# Upload json files
"""

def do(name, crossrefDF):
    try: 
        print("processing file:" + name)

        # # Data preparation 

        noAuthors = [i for i in range(len(crossrefDF)) if 'author' not in crossrefDF['items'][i]]
        Authors = [i for i in range(len(crossrefDF)) if 'author'  in crossrefDF['items'][i]]
        len(noAuthors) + len(Authors) == len(crossrefDF)


        # ## Rows with authors

        crossrefAuth = crossrefDF.iloc[Authors].copy()
        crossrefAuth.reset_index(inplace= True)
        crossrefAuth.drop(columns = ['index'], inplace = True)


        # ## Extract 'DOI'

        crossrefAuth.loc[:, 'DOI'] = crossrefAuth['items'].apply(lambda x: x['DOI'])

        # ## Extract 'authors' --- number of authors

        crossrefAuth.loc[:,'authors'] = crossrefAuth['items'].apply(lambda x: x['author'])
        numAuthors = [len(crossrefAuth.iloc[i]['authors']) for i in range(len(crossrefAuth))]

        ## yparxoun lathi  ---> kalytera number of affiliations
        crossrefAuth.loc[:,'# authors'] = numAuthors

        # ## Extract 'affiliations' --- number of affiliations

        def getAff(k):
            return [crossrefAuth['authors'][k][j]['affiliation'] for j in range(len(crossrefAuth['authors'][k]))]
            
        Affiliations = [getAff(k) for k in range(len(crossrefAuth))]

        crossrefAuth.loc[:,'affiliations'] = Affiliations
        numAffil = [len(Affiliations[i]) for i in range(len(crossrefAuth))]
        crossrefAuth.loc[:,'# Affil'] = numAffil


        # ## Clean 'empty' affiliations

        possibleEmptyAff = []

        for k in range(len(crossrefAuth)):
            if len(crossrefAuth['affiliations'][k][0]) == 0:
                possibleEmptyAff.append(k)

        nonEmptyAff = []

        for k in possibleEmptyAff:
            for j in range(len(crossrefAuth['affiliations'].iloc[k])):
                if len(crossrefAuth['affiliations'].iloc[k][j]) != 0:
                    nonEmptyAff.append(k)
            
            
        FinalEmptyyAff=  [x for x in possibleEmptyAff if x not in nonEmptyAff] 
        FinalNonEmptyAff = [x for x in range(len(crossrefAuth)) if x not in FinalEmptyyAff]

        # skip file when this list is empty
        if (len(FinalNonEmptyAff) == 0):
            return

        # # doiDF: crossrefAuth subdataframe with nonpempty affiliation lists

        doiDF = crossrefAuth.iloc[FinalNonEmptyAff].copy()
        doiDF.reset_index(inplace = True)
        doiDF.drop(columns = ['index'], inplace = True)


        # ## (still some cleaning: cases with empty brackets [{}])

        for k in range(len(doiDF)):
            if len(doiDF['affiliations'][k][0]) != 0 and doiDF['affiliations'][k][0][0] == {}:
                print(k)

        emptyBrackets = [k for k in range(len(doiDF)) if len(doiDF['affiliations'][k][0]) != 0 and doiDF['affiliations'][k][0][0] == {}]

        doiDF.iloc[emptyBrackets]
        doiDF.drop(emptyBrackets, inplace = True)
        doiDF.reset_index(inplace = True)
        doiDF.drop(columns = ['index'], inplace = True)


        # # Clean affiliations 

        # ## is_contained(a,b) map : returns true when a is a substring of b 

        def is_contained(s, w):
            words = s.split()  # Split the string 's' into a list of words
            for word in words:
                if word not in w:  # If a word from 's' is not found in 'w'
                    return False  # Return False immediately
            return True  # If all words from 's' are found in 'w', return True

        # ## 1. "Unique" affiliations --- number of unique affiliations

        uniqueAff = []
        error_indices =[] # New list to store error indices
        for i in range(len(doiDF)):
            try:
                uniqueAff.append(list(set([x[0] for x in [list(d.values()) for d in [item for sublist in doiDF['affiliations'].iloc[i] for item in sublist if sublist !=[{}]  and item !={}]]])))
            except TypeError:
                print(name + ": Error occurred for i =", i)
                error_indices.append(i)  # Save the index where the error occurred
            #except IndexError:
            #   print("IndexError occurred for i =", i)
            #  error_indices.append(i)  # Save the index where the IndexError occurred


        # Print the error indices
        print(name + ": Error indices:", error_indices)

        doiDF.drop(error_indices, inplace = True)
        doiDF.reset_index(inplace = True)
        doiDF.drop(columns = ['index'], inplace = True)

        doiDF.loc[:,'uniqueAff'] = uniqueAff

        numUniqueAff = [len(doiDF['uniqueAff'].iloc[i]) for i in range(len(doiDF))]
        doiDF.loc[:,'# uniqueAff'] = numUniqueAff

        doiDF.loc[:,'uniqueAff1'] = doiDF['uniqueAff'].apply(lambda x: [s.lower() for s in x])


        # ## 2. Remove stop words 

        stopWords = ['from', 'the', 'of', 'at', 'de','for','et','für','des', 'in','as','a','and']

        def remove_stop_words(text):
            words = text.split()
            filtered_words = [word for word in words if word not in stopWords]
            return ' '.join(filtered_words)


        doiDF.loc[:,'uniqueAff1'] = doiDF['uniqueAff'].apply(lambda x: [remove_stop_words(s) for s in x])


        # ## 3. Remove parenthesis 

        def remove_parentheses(text):
            return re.sub(r'\([^()]*\)', '', text)


        doiDF.loc[:,'uniqueAff1'] = doiDF['uniqueAff1'].apply(lambda x: [remove_parentheses(s) for s in x])


        # ## 4. Remove @#$%characters and umlauts

        def replace_umlauts(text):
            normalized_text = unicodedata.normalize('NFKD', text)
            replaced_text = ''.join(c for c in normalized_text if not unicodedata.combining(c))
            return replaced_text

        affNoSymbols = []

        for i in range(len(list(doiDF['uniqueAff1']))):
            L = list(doiDF['uniqueAff1'])[i]
            for j in range(len(L)):
                L[j] = re.sub(r'[^\w\s,Α-Ωα-ωぁ-んァ-ン一-龯，]', '', L[j])
                L[j] = L[j].replace("  ", " ")
                L[j] = replace_umlauts(L[j])
                
            affNoSymbols.append(L)


        affNoSymbols = [[item for item in inner_list if item != "inc"] for inner_list in affNoSymbols]

        doiDF['uniqueAff1'] = affNoSymbols


        # ## 5. Check 'sub'-affiliations (affiliations that are contained in other affiliations of the same DOI)

        newAff0 = []

        for k in range(len(doiDF)):
            
            L2 = []
            for s1 in doiDF['uniqueAff1'].iloc[k]:
                is_substring = False
                for s2 in doiDF['uniqueAff1'].iloc[k]:
                    if s1 != s2 and s1 in s2:
                        is_substring = True
                        break
                if not is_substring:
                    L2.append(s1)
            newAff0.append(L2)
            
        newAffList = [list(set(newAff0[k])) for k in range(len(newAff0))]
       
        doiDF['Unique affiliations'] = newAffList

        allAffsList = []

        for doi in newAffList:
            for aff in doi:
                if aff not in allAffsList:
                    allAffsList.append(aff)

        # ## 6. Split strings where ',' or ';' appears    | Apply .lower()

        def substringsDict(string):
            split_strings = [re.sub(r'^[\s.]+|[\s.]+$', '', s.strip()) for s in re.split(r'[,;]', string)]
            dict_string = {}
            index = 0

            for value in split_strings:
                if value:
                    modified_value = re.sub(r'\buniversit\w*', 'universit', value, flags=re.IGNORECASE)
                    dict_string[index] = modified_value.lower()
                    index += 1

            return dict_string

        newAffkomma = []

        for aff in allAffsList:
            newAffkomma.append(substringsDict(aff))


        for dict in newAffkomma:
    
            if len(dict)>1:
                for i in range(len(dict)-1):
                    if is_contained('progr', dict[i]) and is_contained('dep', dict[i+1]):
                        del dict[i]
                    elif (is_contained('assistant', dict[i]) or is_contained('researcher', dict[i]) or is_contained('phd', dict[i]) or is_contained('student', dict[i]) or is_contained('section', dict[i]) or is_contained('prof', dict[i]) or is_contained('director', dict[i])) and (not is_contained('school', dict[i+1]) or is_contained('univ', dict[i+1]) or is_contained('inst', dict[i+1]) or is_contained('lab', dict[i+1]) or is_contained('fac', dict[i+1])):
                        del dict[i]
                    elif (is_contained('engineer', dict[i]) or is_contained('progr', dict[i]) or is_contained('unit', dict[i]) or is_contained('lab', dict[i]) or is_contained('dep', dict[i]) or is_contained('inst', dict[i]) or is_contained('hosp', dict[i]) or is_contained('school', dict[i]) or is_contained('fac', dict[i])) and is_contained('univ', dict[i+1]):
                        del dict[i]
                    elif is_contained('lab', dict[i]) and (is_contained('college', dict[i+1]) or is_contained('inst', dict[i+1]) or is_contained('dep', dict[i+1]) or is_contained('school', dict[i+1])):
                        del dict[i]
                    elif is_contained('dep', dict[i]) and (is_contained('tech', dict[i+1]) or is_contained('college', dict[i+1]) or is_contained('inst', dict[i+1]) or  is_contained('hosp', dict[i+1]) or  is_contained('school', dict[i+1]) or  is_contained('fac', dict[i+1])):
                        del dict[i]
                    elif is_contained('inst',dict[i]) and (is_contained('dep', dict[i+1]) or is_contained('acad', dict[i+1]) or is_contained('hosp', dict[i+1]) or is_contained('fac', dict[i+1]) or is_contained('cent', dict[i+1]) or is_contained('div', dict[i+1])):
                        del dict[i]
                    elif is_contained('hosp',dict[i]) and is_contained('school', dict[i+1]):
                        del dict[i]
                

                    
        lightAff = []
        
        for dict in newAffkomma:
            lightAff.append(', '.join(list(dict.values())))



        removeList = ['university','research institute','laboratory' , 'universit','gmbh', 'inc', 'university of', 'research center', 
        'university college','national institute of', 'school of medicine', "university school", 'graduate school of', 'graduate school of engineering', 
        'institute of tropical medicine', 'institute of virology', 'faculty of medicine','laboratory', 'university park', 'institute of science','Polytechnic University']

        city_names = ["Aberdeen", "Abilene", "Akron", "Albany", "Albuquerque", "Alexandria", "Allentown", "Amarillo", "Anaheim", "Anchorage", "Ann Arbor", "Antioch", "Apple Valley", "Appleton", "Arlington", "Arvada", "Asheville", "Athens", "Atlanta", "Atlantic City", "Augusta", "Aurora", "Austin", "Bakersfield", "Baltimore", "Barnstable", "Baton Rouge", "Beaumont", "Bel Air", "Bellevue", "Berkeley", "Bethlehem", "Billings", "Birmingham", "Bloomington", "Boise", "Boise City", "Bonita Springs", "Boston", "Boulder", "Bradenton", "Bremerton", "Bridgeport", "Brighton", "Brownsville", "Bryan", "Buffalo", "Burbank", "Burlington", "Cambridge", "Canton", "Cape Coral", "Carrollton", "Cary", "Cathedral City", "Cedar Rapids", "Champaign", "Chandler", "Charleston", "Charlotte", "Chattanooga", "Chesapeake", "Chicago", "Chula Vista", "Cincinnati", "Clarke County", "Clarksville", "Clearwater", "Cleveland", "College Station", "Colorado Springs", "Columbia", "Columbus", "Concord", "Coral Springs", "Corona", "Corpus Christi", "Costa Mesa", "Dallas", "Daly City", "Danbury", "Davenport", "Davidson County", "Dayton", "Daytona Beach", "Deltona", "Denton", "Denver", "Des Moines", "Detroit", "Downey", "Duluth", "Durham", "El Monte", "El Paso", "Elizabeth", "Elk Grove", "Elkhart", "Erie", "Escondido", "Eugene", "Evansville", "Fairfield", "Fargo", "Fayetteville", "Fitchburg", "Flint", "Fontana", "Fort Collins", "Fort Lauderdale", "Fort Smith", "Fort Walton Beach", "Fort Wayne", "Fort Worth", "Frederick", "Fremont", "Fresno", "Fullerton", "Gainesville", "Garden Grove", "Garland", "Gastonia", "Gilbert", "Glendale", "Grand Prairie", "Grand Rapids", "Grayslake", "Green Bay", "GreenBay", "Greensboro", "Greenville", "Gulfport-Biloxi", "Hagerstown", "Hampton", "Harlingen", "Harrisburg", "Hartford", "Havre de Grace", "Hayward", "Hemet", "Henderson", "Hesperia", "Hialeah", "Hickory", "High Point", "Hollywood", "Honolulu", "Houma", "Houston", "Howell", "Huntington", "Huntington Beach", "Huntsville", "Independence", "Indianapolis", "Inglewood", "Irvine", "Irving", "Jackson", "Jacksonville", "Jefferson", "Jersey City", "Johnson City", "Joliet", "Kailua", "Kalamazoo", "Kaneohe", "Kansas City", "Kennewick", "Kenosha", "Killeen", "Kissimmee", "Knoxville", "Lacey", "Lafayette", "Lake Charles", "Lakeland", "Lakewood", "Lancaster", "Lansing", "Laredo", "Las Cruces", "Las Vegas", "Layton", "Leominster", "Lewisville", "Lexington", "Lincoln", "Little Rock", "Long Beach", "Lorain", "Los Angeles", "Louisville", "Lowell", "Lubbock", "Macon", "Madison", "Manchester", "Marina", "Marysville", "McAllen", "McHenry", "Medford", "Melbourne", "Memphis", "Merced", "Mesa", "Mesquite", "Miami", "Milwaukee", "Minneapolis", "Miramar", "Mission Viejo", "Mobile", "Modesto", "Monroe", "Monterey", "Montgomery", "Moreno Valley", "Murfreesboro", "Murrieta", "Muskegon", "Myrtle Beach", "Naperville", "Naples", "Nashua", "Nashville", "New Bedford", "New Haven", "New London", "New Orleans", "New York", "New York City", "Newark", "Newburgh", "Newport News", "Norfolk", "Normal", "Norman", "North Charleston", "North Las Vegas", "North Port", "Norwalk", "Norwich", "Oakland", "Ocala", "Oceanside", "Odessa", "Ogden", "Oklahoma City", "Olathe", "Olympia", "Omaha", "Ontario", "Orange", "Orem", "Orlando", "Overland Park", "Oxnard", "Palm Bay", "Palm Springs", "Palmdale", "Panama City", "Pasadena", "Paterson", "Pembroke Pines", "Pensacola", "Peoria", "Philadelphia", "Phoenix", "Pittsburgh", "Plano", "Pomona", "Pompano Beach", "Port Arthur", "Port Orange", "Port Saint Lucie", "Port St. Lucie", "Portland", "Portsmouth", "Poughkeepsie", "Providence", "Provo", "Pueblo", "Punta Gorda", "Racine", "Raleigh", "Rancho Cucamonga", "Reading", "Redding", "Reno", "Richland", "Richmond", "Richmond County", "Riverside", "Roanoke", "Rochester", "Rockford", "Roseville", "Round Lake Beach", "Sacramento", "Saginaw", "Saint Louis", "Saint Paul", "Saint Petersburg", "Salem", "Salinas", "Salt Lake City", "San Antonio", "San Bernardino", "San Buenaventura", "San Diego", "San Francisco", "San Jose", "Santa Ana", "Santa Barbara", "Santa Clara", "Santa Clarita", "Santa Cruz", "Santa Maria", "Santa Rosa", "Sarasota", "Savannah", "Scottsdale", "Scranton", "Seaside", "Seattle", "Sebastian", "Shreveport", "Simi Valley", "Sioux City", "Sioux Falls", "South Bend", "South Lyon", "Spartanburg", "Spokane", "Springdale", "Springfield", "St. Louis", "St. Paul", "St. Petersburg", "Stamford", "Sterling Heights", "Stockton", "Sunnyvale", "Syracuse", "Tacoma", "Tallahassee", "Tampa", "Temecula", "Tempe", "Thornton", "Thousand Oaks", "Toledo", "Topeka", "Torrance", "Trenton", "Tucson", "Tulsa", "Tuscaloosa", "Tyler", "Utica", "Vallejo", "Vancouver", "Vero Beach", "Victorville", "Virginia Beach", "Visalia", "Waco", "Warren", "Washington", "Waterbury", "Waterloo", "West Covina", "West Valley City", "Westminster", "Wichita", "Wilmington", "Winston", "Winter Haven", "Worcester", "Yakima", "Yonkers", "York", "Youngstown"]

        city_names = [x.lower() for x in city_names]

       
        for dict in newAffkomma:
            for i in list(dict.keys()):

                if dict[i] in city_names+removeList:
                    del dict[i]



        affDF = pd.DataFrame()
        affDF['Original Affiliations'] = allAffsList
        affDF['Light Affiliations'] = lightAff
        affDF['Keywords'] =  [list(d.values()) for d in newAffkomma]
        

        # # Labels based on legalnames of openAIRE's organizations
        
        uniList = ['institu', 'istitut', 'univ', 'coll', 'center','polytechnic', 'centre' , 'cnrs', 'faculty','school' , 'academy' , 'akadem','école', 'hochschule' , 'ecole', 'tech', 'observ']
        
        labList = ['lab']
        
        hosplList = ['hospital' ,'clinic', 'hôpital', 'klinik','oncol','medical']
        
        gmbhList = ['gmbh', 'company' , 'industr', 'etaireia' , 'corporation', 'inc']
        
        musList =  ['museum', 'library']
        
        foundList =  ['foundation' , 'association','organization' ,'society', 'group' ]
        
        deptList = ['district' , 'federation'  , 'government' , 'municipal' , 'county','council', 'agency']

        unknownList = ['unknown']

        #######   Dictionaries ##########

        uniDict = {k: 'Univ/Inst' for k in uniList}   

        labDict = {k: 'Laboratory' for k in labList} 

        hosplDict = {k: 'Hospital' for k in hosplList}   

        gmbhDict = {k: 'Company' for k in gmbhList}   

        musDict = {k: 'Museum' for k in musList}   

        #schoolDict = {k: 'School' for k in schoolList}   

        foundDict = {k: 'Foundation' for k in foundList}   

        deptDict = {k: 'Government' for k in deptList}   

        unknownDict =  {k: 'Unknown' for k in unknownList}   

        categDictsList = [uniDict, labDict, hosplDict, gmbhDict, musDict, #schoolDict, 
                        foundDict, deptDict, unknownDict]

        
        


        ################# Final Dictionary #####################

        categDicts = {}
        i = 0
        while i in range(len(categDictsList)):
            categDicts.update(categDictsList[i])
            i = i+1
            
            
        # ## affiliationsDict

        affiliationsDict = {}

        for i in range(len(affDF)):
            affiliationsDict[i] = affDF['Keywords'].iloc[i]
                    
        d_new = {}

        # iterate over the keys of affiliationsDict
        for k in range(len(affiliationsDict)):
            # get the list associated with the current key in affiliationsDict
            L = affiliationsDict.get(k, [])
            mapped_listx = [[s, v] for s in L for k2, v in categDicts.items() if k2 in s]
            

            # add the mapped list to the new dictionary d_new
            d_new[k] = mapped_listx


        affDF['Dictionary'] = list(d_new.values())



        # ## New column: category based on the labels 

        category = [', '.join(list(set([x[1] for x in affDF['Dictionary'].iloc[i]]))) for i in range(len(affDF))]
            

        affDF.loc[:, 'Category'] = category



        # ### new label: rest

        for i in range(len(affDF)):
            if affDF['Category'].iloc[i] == '':
                affDF.iloc[i, affDF.columns.get_loc('Category')] = 'Rest'

        affiliationsSimple = [
            list(set([x[0] for x in affDF['Dictionary'].iloc[i]]))
            for i in range(len(affDF))]

        affDF['Keywords'] = affiliationsSimple
        
        def strRadiusU(string):
            string = string.lower()
            radius = 3
            
            strList = string.split()
            indices = []
            result = []

            for i, x in enumerate(strList):
                if is_contained('univers',x):
                    indices.append(i)
                    
            for r0 in indices:
                lmin =max(0,r0-radius)
                lmax =min(r0+radius, len(strList))
                s = strList[lmin:lmax]
                
                result.append(' '.join(s))
            
            return result 

        def strRadiusH(string):
            string = string.lower()
            radius = 3
            
            strList = string.split()
            indices = []
            result = []

            for i, x in enumerate(strList):
                if is_contained('hospital',x):
                    indices.append(i)
                    
            for r0 in indices:
                lmin =max(0,r0-radius-1)
                lmax =min(r0+radius, len(strList))
                s = strList[lmin:lmax]
                
                result.append(' '.join(s))
            
            return result 

        
        def strRadiusC(string):
            string = string.lower()
            radius = 2
            
            strList = string.split()
            indices = []
            result = []
        
            for i, x in enumerate(strList):
                if is_contained('clinic',x) or is_contained('klinik',x):
                    indices.append(i)
                    
            for r0 in indices:
                lmin =max(0,r0-radius-1)
                lmax =min(r0+radius, len(strList))
                s = strList[lmin:lmax]
                
                result.append(' '.join(s))
            
            return result 
            

        affiliationsSimpleN = []

        for i in range(len(affiliationsSimple)):
            inner = []
            for str in affiliationsSimple[i]:
                if 'university' in str.split():
                    for x in strRadiusU(str):
                        inner.append(x)
                elif 'hospital' in str or 'hôpital' in str:
                    for x in strRadiusH(str):
                        inner.append(x)
                elif 'clinic' in str or 'klinik' in str:
                    for x in strRadiusH(str):
                        inner.append(x)
                
                else:
                    inner.append(str)
            
            affiliationsSimpleN.append(inner)       
                    
        
        affDF['Keywords'] = affiliationsSimpleN
        


        # # UNIVS & LABS

        univLabs = [i for i in range(len(affDF)) if 'Laboratory' in affDF['Category'].iloc[i] 
            or 'Univ/Inst' in  affDF['Category'].iloc[i]]
        
        if (len(univLabs) == 0):
            return


        univLabsDF = affDF.iloc[univLabs].copy()
        univLabsDF.reset_index(inplace = True)
        univLabsDF.drop(columns = ['index'], inplace = True)


        # # Load files from openAIRE

        with open('dixAcadRor.pkl', 'rb') as f:
            dixOpenOrgId = pickle.load(f)


        # ## Clean/modify the files


        def filter_key(key):
          # Remove all non-alphanumeric characters except Greek letters and Chinese characters
            modified_key = re.sub(r'[^\w\s,Α-Ωα-ωぁ-んァ-ン一-龯，]', '', key)
            modified_key = re.sub(r'\buniversit\w*', 'universit', modified_key, flags=re.IGNORECASE)
            modified_key = modified_key.replace(' and ', ' ')
            return modified_key

            
        def filter_dictionary_keys(dictionary):
            filtered_dict = {}
            for key, value in dictionary.items():
                filtered_key = filter_key(key)
                filtered_dict[filtered_key] = value
            return filtered_dict


        def cleanDict(dix):
            dix1 =  {k.replace(',', ''): v for k, v in dix.items()}
            
            dix1 = {replace_umlauts(key): value
            for key, value in dix1.items()}
            
            dix1 = filter_dictionary_keys(dix1)
            
            dix2 = {}
            
            for key, value in dix1.items():
                updated_key = ' '.join([word for word in key.split() if word.lower() not in stopWords])
                dix2[updated_key] = value
                
            for x in list(dix2.keys()):
                if len(x) <3:
                    del dix2[x]
                    
            if 'universit hospital' in list(dix2.keys()):
                del dix2['universit hospital']
                
            if 'universit school' in list(dix2.keys()):
                del dix2['universit school']
                
            if 'ni universit' in list(dix2.keys()):
                del dix2['ni universit']
        
                
            if 's v universit' in list(dix2.keys()):
                del dix2['s v universit']
        
            if 'k l universit' in list(dix2.keys()):
                del dix2['k l universit']
                
            return dix2
    
        dixOpenOrgId2 = cleanDict(dixOpenOrgId)
        # # MATCHINGS

        # ## Helper functions

        # ### Clean the matchings

        def bestSimScore(l1, l2, l3, l4, simU, simG):
            """
            Finds the best match between a 'key word' and several legal names from the OpenAIRE database.
            ---> corrects special cases in the main map that follows
        
            Args:
                l1: List of light affiliations.
                l2: number of candidates.
                l3: List of pairs.
                l4: mult
        
            Returns:
                List: Resulting list containing OpenAIRE names and their similarity scores.
            """
            
            vectorizer = CountVectorizer()
            numUniv = sum([(l1[i].lower()).count('univ') for i in range(len(l1))])
            result = []
            for i in range(len(l1)):
                best = [] 
                s = l1[i]
               # s_contains_university = is_contained("university", s.lower())  
                
               # if not is_contained("univ", s.lower()):
               #     continue  # Skip if s does not contain "university" or "univ"
                
            
                for j in range(len(l3)):
                    x = l3[j][1] 
                   
                    if [x, l3[j][2]] in result:
                            continue
                    
                    if l4[l3[j][0]] == 1:
                       
                        if  is_contained('univ', x.lower()) and  l3[j][2]> simU:
                            result.append([x, l3[j][2]])
                        elif  l3[j][2] >simG:
                            result.append([x, l3[j][2]])
        
                        
                      
                    elif l3[j][2] >=0.99 and (is_contained("univ", x.lower()) or is_contained("college", x.lower()) or  is_contained("center", x.lower()) or  is_contained("schule", x.lower())): # If the similarity score of a pair (s,x) was 1, we store it to results list
                        result.append([l3[j][1], 1])
                        
                    else:
                        try:
                    #        x_contains_university = is_contained("university", x.lower())
                            if not is_contained("univ", x.lower()):
                                continue  # Skip if x does not contain "university" or "univ"
                            
                            if (is_contained('hosp', x.lower()) and not is_contained('hosp', s)) or (not is_contained('hosp', x.lower()) and is_contained('hosp', s)):
                                continue
                            s_vector = vectorizer.fit_transform([s]).toarray() #Else we compute the similarity of s with the original affiiation name
                            x_vector = vectorizer.transform([x]).toarray()
                        #  s_vector1 =  vectorizer.transform([s]).toarray()
                        #  x_vector1 =  vectorizer.fit_transform([s]).toarray()
                            
        
                            # Compute similarity between the vectors
                            similarity = cosine_similarity(x_vector, s_vector)[0][0]
                            if similarity> 0.1:
                        # similarity1 = cosine_similarity(x_vector1, s_vector1)[0][0]
                            #similarity2 = Levenshtein.ratio(s,x)
        
        
                                best.append([x, similarity])#(similarity+similarity2)/2])
                        except:
                            KeyError
                            
                if best:
                    max_numbers = defaultdict(float)
                    for item in best:
                        string, number = item
                        max_numbers[string] = max(max_numbers[string], number)
        
        # Create a new list with the elements having the maximum number for each string
                    reduced_best = [[string, number] for string, number in best if number == max_numbers[string]]
        
        #            max_score = max(best, key=lambda x: x[1])[1]
        #            max_results = [(x[0], x[1]) for x in best if x[1] == max_score]
                   # if len(reduced_best) > 1:
                    reduced_best.sort(key=lambda x: x[1], reverse=True)
                    #reduced_best.sort(key=lambda x: (l2.index(x[0]), -x[1]), reverse=False)
                   #     result.append(reduced_best[-1])
                    #else:
                    result = result + reduced_best
                        
            univ_list = []
            other_list = []
            
            for r in result:
                if is_contained('univ',r[0]):
                    univ_list.append(r)
                else:
                    other_list.append(r)
            
            limit =  min(numUniv, l2)
        
            if len(univ_list)> limit:
                result = univ_list[:limit] + other_list
                        
            return result
    

 

        # ### Find rows with multiple mathcings

        def index_multipleMatchings(df):
            multipleMatchings = []
            mult = []

            for i in range(len(df)):
                result_dict = {}
                

                for t in [t[0] for t in df.Pairs.iloc[i]]:
                    key = t
                    if key in result_dict:
                        result_dict[key] += 1
                        multipleMatchings.append(i)
                        
                    else:
                        result_dict[key] = 1
                mult.append(result_dict)
            return [list(set(multipleMatchings)), mult]
                        
    
        # ## Main map
        
        def Aff_Ids(m, DF, dixOpenAIRE, simU, simG):
            
            """
            Matches affiliations in DataFrame 'DF' with names from dictionary 'dixOpenAIRE' and their openAIRE ids based on similarity scores.
        
            Args:
                m (int): The number of DOIs to check.
                DF (DataFrame): The input DataFrame containing affiliation data.
                dixOpenAIRE (dict): A dictionary of names from OpenAIRE.
                simU (float): Similarity threshold for universities.
                simG (float): Similarity threshold for non-universities.
        
            Returns:
                DataFrame: The final DataFrame with matched affiliations and their corresponding similarity scores.
            """
            vectorizer = CountVectorizer()
        
            lnamelist = list(dixOpenAIRE.keys())
            dix = {}    # will store indeces and legalnames of organizations of the DOI { i : [legalname1, legalname2,...]}
            deiktes = []  # stores indeces where a match is found
            similarity_ab = [] # stores lists of similarity scores of the mathces 
            pairs = [] #  pairs[i] =  [ [s,x,t] ] where (s,x) is a match and t the corresponding similarity score
            
            for k in range(m):
                similar_k = []
                pairs_k = []
        
        
                for s in DF['Keywords'].iloc[k]:
        
                    if s in lnamelist:
                        deiktes.append(k)
                        similarity = 1
                        similar_k.append(similarity)
                        
                        pairs_k.append((s,s,similarity))
        
                        if k not in dix:
                            dix[k] = [s]
                        else:
                            dix[k].append(s)
                    else:
        
                        for x in lnamelist:
                            
                            if  is_contained(s, x):
        
                                x_vector = vectorizer.fit_transform([x]).toarray()
                                s_vector = vectorizer.transform([s]).toarray()
        
                                # Compute similarity between the vectors
                                similarity = cosine_similarity(x_vector, s_vector)[0][0]
                                if similarity > min(simU, simG):
                                    if (is_contained('univ', s) and is_contained('univ', x)) and similarity > simU:
                                        similar_k.append(similarity)
                                        deiktes.append(k)
                                        pairs_k.append((s,x,similarity))
        
                                        if k not in dix:
                                            dix[k] = [x]
                                        else:
                                            dix[k].append(x)
                                    elif (not is_contained('univ', s) and not is_contained('univ', x)) and similarity > simG:
                                        similar_k.append(similarity)
                                        deiktes.append(k)
                                        pairs_k.append((s,x,similarity))
        
                                        if k not in dix:
                                            dix[k] = [x]
                                        else:
                                            dix[k].append(x)
                                            
                            elif is_contained(x, s):
                                if (is_contained('univ', s) and is_contained('univ', x)):
        
                                    if ' and ' in s:
                                        list_s = s.split(' and ')
                                        
                                        if list_s:
                                            for q in list_s:
                                                if is_contained('univ', q):
        
                                                    q_vector = vectorizer.fit_transform([q]).toarray()
                                                    x_vector = vectorizer.transform([x]).toarray()
        
                                        # Compute similarity between the vectors
                                                    similarity = cosine_similarity(q_vector, x_vector)[0][0]
                                                    if similarity > simU:
                                                        similar_k.append(similarity)
                                                        deiktes.append(k)
                                                        pairs_k.append((s,x,similarity))
        
                                                        if k not in dix:
                                                            dix[k] = [x]
                                                        else:
                                                            dix[k].append(x)
                                    
                                    else: 
        
                                        s_vector = vectorizer.fit_transform([s]).toarray()
                                        x_vector = vectorizer.transform([x]).toarray()
        
                                        # Compute similarity between the vectors
                                        similarity = cosine_similarity(s_vector, x_vector)[0][0]
                                        if similarity > simU: #max(0.82,sim):
                                            similar_k.append(similarity)
                                            deiktes.append(k)
                                            pairs_k.append((s,x,similarity))
        
                                            if k not in dix:
                                                dix[k] = [x]
                                            else:
                                                dix[k].append(x)
                                elif not is_contained('univ', s) and not is_contained('univ', x):
                                   # if 'and' in s:
                                   #     list_s = s.split(' and ')
                                   #     if list_s:
                                   #         for t in list_s:
                                   #             if is_contained(x, t):
        
                                   #                 t_vector = vectorizer.fit_transform([t]).toarray()
                                   #                 x_vector = vectorizer.transform([x]).toarray()
        
                                        # Compute similarity between the vectors
                                   #                 similarity = cosine_similarity(t_vector, x_vector)[0][0]
                                   #                 if similarity > simG:
                                   #                     similar_k.append(similarity)
                                   #                     deiktes.append(k)
                                   #                     pairs_k.append((s,x,similarity))
        
                                   #                     if k not in dix:
                                #                        dix[k] = [x]
                                    #                    else:
                                    #                        dix[k].append(x)
                                    #            
                                    #            if is_contained(t, x):
        
                                    #                x_vector = vectorizer.fit_transform([x]).toarray()
                                    #                t_vector = vectorizer.transform([t]).toarray()
        
                                        # Compute similarity between the vectors
                                    #                similarity = cosine_similarity(t_vector, x_vector)[0][0]
                                    #                if similarity > simG:
                                    #                    similar_k.append(similarity)
                                    #                    deiktes.append(k)
                                    #                    pairs_k.append((s,x,similarity))
        
                                     #                   if k not in dix:
                                     #                       dix[k] = [x]
                                     #                   else:
                                     #                       dix[k].append(x)
                                   # else: 
        
                                    s_vector = vectorizer.fit_transform([s]).toarray()
                                    x_vector = vectorizer.transform([x]).toarray()
        
                                    # Compute similarity between the vectors
                                    similarity = cosine_similarity(s_vector, x_vector)[0][0]
                                    if similarity > simG: #max(0.82,sim):
                                        similar_k.append(similarity)
                                        deiktes.append(k)
                                        pairs_k.append((s,x,similarity))
        
                                        if k not in dix:
                                            dix[k] = [x]
                                        else:
                                            dix[k].append(x)
                                    
                similarity_ab.append(similar_k)   
                similarity_ab = [lst for lst in similarity_ab if lst != []]
                pairs.append(pairs_k)
                
         
            
            
        ## Define the new Dataframe
            
            affIdDF = pd.DataFrame()
            affIdDF['Original affiliations'] = list(DF['Original Affiliations'].iloc[list(set(deiktes))])
        
            affIdDF['Light affiliations'] = list(DF['Light Affiliations'].iloc[list(set(deiktes))])
        
            affIdDF['Candidates for matching'] = list(DF['Keywords'].iloc[list(set(deiktes))])
        
        
            affIdDF['Matched openAIRE names'] = list(dix.values())
            affIdDF['# Matched orgs'] = [len(list(dix.values())[i]) for i in range(len(list(dix.values())))]
            
        
            affIdDF['Similarity score'] = similarity_ab
        
            Pairs = [lst for lst in pairs if lst]
            affIdDF['Pairs'] = Pairs
            affIdDF['mult'] = index_multipleMatchings(affIdDF)[1]
        
        
        
        
        ## Correct the matchings
            needCheck = list(set([i for i in range(len(affIdDF)) for k in list(affIdDF['mult'].iloc[i].values()) if k>1]))
            
        
            ready = [i for i in range(len(affIdDF)) if i not in needCheck]
            
           
            best = [ bestSimScore([affIdDF['Light affiliations'].iloc[i]], len(affIdDF['Candidates for matching'].iloc[i]), affIdDF['Pairs'].iloc[i],affIdDF['mult'].iloc[i], simU, simG) for i in needCheck]
            best_o = []
            best_s = []
            
            for x in best:
                best_o.append([x[i][0]  for i in range(len(x))])
                best_s.append([round(x[i][1],2)  for i in range(len(x))])
            numMathced = [len(best_s[i]) for i in range(len(needCheck))]
            
        
            
            dfFinal0 = (affIdDF.iloc[ready]).copy()
            dfFinal0['index'] = ready
            
            dfFinal1 = (affIdDF.iloc[needCheck]).copy()
            dfFinal1['index'] = needCheck
            dfFinal1['Matched openAIRE names'] = best_o
            dfFinal1['Similarity score'] = best_s
            dfFinal1['# Matched orgs'] = numMathced
            
            finalDF =  pd.concat([dfFinal0, dfFinal1])
            finalDF.set_index('index', inplace=True)
            finalDF.sort_values('index', ascending=True, inplace = True)
            
            ids = [[dixOpenAIRE[x] for x in v] for v in finalDF['Matched openAIRE names']]
            numIds = [len(x) for x in ids]
        
            finalDF['IDs'] = ids
            finalDF['# IDs'] = numIds
            finalDF = finalDF[~(finalDF['# Matched orgs'] == 0)]
            
            finalDF = finalDF.reset_index(drop=True)
            perc = 100*len(finalDF)/m
        
        
        
            
            
            return [perc,finalDF]

    
                  
        
 
        result = Aff_Ids(len(univLabsDF), univLabsDF, dixOpenOrgId2, 0.7,0.82)
    
        if len(result) == 0:
            return
        
        dict_aff_open = {x: y for x, y in zip(result[1]['Original affiliations'], result[1]['Matched openAIRE names'])}
        dict_aff_id = {x: y for x, y in zip(result[1]['Original affiliations'], result[1]['IDs'])}
        dict_aff_score = {x: y for x, y in zip(result[1]['Original affiliations'], result[1]['Similarity score'])}

        pids = []
        for i in range(len(doiDF)):
            pidsi = []
            for aff in doiDF['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_id.keys()):
                    pidsi = pidsi + dict_aff_id[aff]
                elif 'unmatched organization(s)' not in pidsi:
                    pidsi = pidsi + ['unmatched organization(s)']
            pids.append(pidsi)
            
            
        names = []
        for i in range(len(doiDF)):
            namesi = []
            for aff in doiDF['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_open.keys()):
                    namesi = namesi +  dict_aff_open[aff]
                elif 'unmatched organization(s)' not in namesi:
                    namesi = namesi + ['unmatched organization(s)']
            names.append(namesi)    
            
        scores = []
        for i in range(len(doiDF)):
            scoresi = []
            for aff in doiDF['Unique affiliations'].iloc[i]:
                if aff in list(dict_aff_score.keys()):
                    scoresi = scoresi +  dict_aff_score[aff]
                elif 'unmatched organization(s)' not in scoresi:
                    scoresi = scoresi + ['-']
            scores.append(scoresi)
     
            
        doiDF['Matched openAIRE names'] = names
        doiDF['IDs'] = pids
        doiDF['Scores'] = scores
        
        unmatched = [i for i in range(len(doiDF)) if doiDF['Matched openAIRE names'].iloc[i] == ['unmatched organization(s)']]
        matched = [i for i in range(len(doiDF))  if i not in unmatched]
            
        finalDF =  doiDF[['DOI',"Unique affiliations",'Matched openAIRE names','IDs', 'Scores']].iloc[matched]
        finalDF.reset_index(inplace = True)

        def update_Z(row):
            new_Z = []
            for i in range(len(row['IDs'])):
                entry = {'RORid': row['IDs'][i], 'Confidence': row['Scores'][i]}
                new_Z.append(entry)
            return new_Z

        matching = finalDF.apply(update_Z, axis=1)

        finalDF.loc[:,'Matchings'] = matching
        
        # Output
        doiDF_output = finalDF[['DOI','Matchings']]


        match0 = doiDF_output.to_json(orient='records',lines=True)

        # Save the JSON to a file
        with open('output/' + name, 'w') as f:
            f.write(match0)
    except Exception as Argument:
        logging.exception("Error in thred code for file: " + name)


i = 1
data = []
numberOfThreads = int(sys.argv[2])
executor = ProcessPoolExecutor(max_workers=numberOfThreads)

with tarfile.open(sys.argv[1], "r:gz") as tar:
    while True:
        member = tar.next()
        # returns None if end of tar
        if not member:
            break
        if member.isfile():
            
            print("reading file: " + member.name)

            current_file = tar.extractfile(member)

            crossrefDF = pd.read_json(current_file, orient='records')
            # print(crossrefDF)
            data.append((member.name, crossrefDF))
            i += 1

            if (i > numberOfThreads):
                print("execute batch: " + str([name for (name, d) in data]))
                futures = [executor.submit(do, name, d) for (name, d) in data]
                done, not_done = wait(futures)
                
                # print(done)
                print(not_done)

                data = []
                i = 0

    futures = [executor.submit(do, name, d) for (name, d) in data]
    done, not_done = wait(futures)
    print(not_done)

    print("Done")








