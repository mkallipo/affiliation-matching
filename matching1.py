# %%
"""
# Import packages
"""
import tarfile

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

# %%
"""
# Upload json files
"""

# %%
#files= ['0.json', '1.json', '2.json', '3.json', '4.json','42.json', '15693.json']
#files = ['0.json']
'''
files = [ sys.argv[1] ]

with tarfile.open(sys.argv[2], "r:gz") as tar:
    while True:
        member = tar.next()
        # returns None if end of tar
        if not member:
            break
        if member.isfile():
            print("processing " + member.name)
            current_file = tar.extractfile(member)

            dfsList = pd.read_json(current_file, orient='records')
            do(member.name, dfsList)
    print("Done")
'''

def do(name, crossrefDF):


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




    crossrefAuth.head()


    # ## Extract 'authors' --- number of authors



    crossrefAuth.loc[:,'authors'] = crossrefAuth['items'].apply(lambda x: x['author'])




    crossrefAuth.head()




    numAuthors = [len(crossrefAuth.iloc[i]['authors']) for i in range(len(crossrefAuth))]




    ## yparxoun lathi  ---> kalytera number of affiliations
    crossrefAuth.loc[:,'# authors'] = numAuthors




    crossrefAuth.head()


    # ## Extract 'affiliations' --- number of affiliations



    def getAff(k):
        return [crossrefAuth['authors'][k][j]['affiliation'] for j in range(len(crossrefAuth['authors'][k]))]
        




    Affiliations = [getAff(k) for k in range(len(crossrefAuth))]

    crossrefAuth.loc[:,'affiliations'] = Affiliations




    numAffil = [len(Affiliations[i]) for i in range(len(crossrefAuth))]




    crossrefAuth.loc[:,'# Affil'] = numAffil




    crossrefAuth.head()


    # ## Clean 'empty' affiliations



    possibleEmptyAff = []

    for k in range(len(crossrefAuth)):
        if len(crossrefAuth['affiliations'][k][0]) == 0:
            possibleEmptyAff.append(k)




    len(possibleEmptyAff)




    nonEmptyAff = []

    for k in possibleEmptyAff:
        for j in range(len(crossrefAuth['affiliations'].iloc[k])):
            if len(crossrefAuth['affiliations'].iloc[k][j]) != 0:
                nonEmptyAff.append(k)
        
        




    FinalEmptyyAff=  [x for x in possibleEmptyAff if x not in nonEmptyAff] 




    FinalNonEmptyAff = [x for x in range(len(crossrefAuth)) if x not in FinalEmptyyAff]


    # # affilDF: crossrefAuth subdataframe with nonpempty affiliation lists



    affilDF = crossrefAuth.iloc[FinalNonEmptyAff].copy()
    affilDF.reset_index(inplace = True)
    affilDF.drop(columns = ['index'], inplace = True)


    # ## (still some cleaning: cases with empty brackets [{}])



    affilDF[affilDF['DOI'] == '10.48130/emst-2022-0020']




    for k in range(len(affilDF)):
        if len(affilDF['affiliations'][k][0]) != 0 and affilDF['affiliations'][k][0][0] == {}:
            print(k)




    emptyBrackets = [k for k in range(len(affilDF)) if len(affilDF['affiliations'][k][0]) != 0 and affilDF['affiliations'][k][0][0] == {}]




    affilDF.iloc[emptyBrackets]




    affilDF.copy()




    affilDF.drop(emptyBrackets, inplace = True)




    affilDF.reset_index(inplace = True)




    affilDF.copy()




    affilDF.drop(columns = ['index'], inplace = True)


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
    for i in range(len(affilDF)):
        try:
            uniqueAff.append(list(set([x[0] for x in [list(d.values()) for d in [item for sublist in affilDF['affiliations'].iloc[i] for item in sublist if sublist !=[{}]]]])))
        except TypeError:
            print("Error occurred for i =", i)
            error_indices.append(i)  # Save the index where the error occurred
        #except IndexError:
        #   print("IndexError occurred for i =", i)
        #  error_indices.append(i)  # Save the index where the IndexError occurred


    # Print the error indices
    print("Error indices:", error_indices)




    affilDF.drop(error_indices, inplace = True)
    affilDF.reset_index(inplace = True)
    affilDF.drop(columns = ['index'], inplace = True)




    affilDF.loc[:,'uniqueAff'] = uniqueAff




    numUniqueAff = [len(affilDF['uniqueAff'].iloc[i]) for i in range(len(affilDF))]




    affilDF.loc[:,'# uniqueAff'] = numUniqueAff


    # ## 2. Remove stop words ['from', 'the']



    stopWords = ['from', 'the', 'From', 'The', 'of', 'at', 'de']




    def remove_stop_words(text):
        words = text.split()
        filtered_words = [word for word in words if word not in stopWords]
        return ' '.join(filtered_words)


    # apply the function to the column  affilDF['uniqueAff'] to create column affilDF.loc[:,'uniqueAff1']

    affilDF.loc[:,'uniqueAff1'] = affilDF['uniqueAff'].apply(lambda x: [remove_stop_words(s) for s in x])


    # ## 3. Remove parenthesis 



    def remove_parentheses(text):
        return re.sub(r'\([^()]*\)', '', text)

    # apply the function to each list element of column affilDF['uniqueAff1'] to remove substrings inside parentheses

    affilDF.loc[:,'uniqueAff1'] = affilDF['uniqueAff1'].apply(lambda x: [remove_parentheses(s) for s in x])


    # ## 4. Remove @#$%characters and umlauts



    def replace_umlauts(text):
        normalized_text = unicodedata.normalize('NFKD', text)
        replaced_text = ''.join(c for c in normalized_text if not unicodedata.combining(c))
        return replaced_text

    affNoSymbols = []

    for i in range(len(list(affilDF['uniqueAff1']))):
        L = list(affilDF['uniqueAff1'])[i]
        for j in range(len(L)):
            L[j] = re.sub(r'[^\w\s,Α-Ωα-ωぁ-んァ-ン一-龯，]', '', L[j])
            L[j] = replace_umlauts(L[j])
            
        affNoSymbols.append(L)





    affNoSymbols = [[item for item in inner_list if item != "inc"] for inner_list in affNoSymbols]




    affilDF['uniqueAff1'] = affNoSymbols


    # ## 5. Check 'sub'-affiliations (affiliations that are contained in other affiliations of the same DOI)



    newAff0 = []

    for k in range(len(affilDF)):
        
        L2 = []
        for s1 in affilDF['uniqueAff1'].iloc[k]:
            is_substring = False
            for s2 in affilDF['uniqueAff1'].iloc[k]:
                if s1 != s2 and s1 in s2:
                    is_substring = True
                    break
            if not is_substring:
                L2.append(s1)
        newAff0.append(L2)




    newAffList = [list(set(newAff0[k])) for k in range(len(newAff0))]




    affilDF['uniqueAff2'] = newAffList


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

    for k in range(len(affilDF)):
        
        new_list = []
        for item in affilDF['uniqueAff2'].iloc[k]:
            new_list.append(substringsDict(item))


        newAffkomma.append(new_list)





    for j in range(len(newAffkomma)):
        for y in newAffkomma[j]:
            if len(y)>1:
                for i in range(len(y)-1):
                    if is_contained('progr', y[i]) and is_contained('dep', y[i+1]):
                        del y[i]
                    elif (is_contained('assistant', y[i]) or is_contained('researcher', y[i]) or is_contained('phd', y[i]) or is_contained('student', y[i]) or is_contained('section', y[i]) or is_contained('prof', y[i]) or is_contained('director', y[i])) and (not is_contained('school', y[i+1]) or is_contained('univ', y[i+1]) or is_contained('inst', y[i+1]) or is_contained('lab', y[i+1]) or is_contained('fac', y[i+1])):
                        del y[i]
                    elif (is_contained('engineer', y[i]) or is_contained('progr', y[i]) or is_contained('unit', y[i]) or is_contained('lab', y[i]) or is_contained('dep', y[i]) or is_contained('inst', y[i]) or is_contained('hosp', y[i]) or is_contained('school', y[i]) or is_contained('fac', y[i])) and is_contained('univ', y[i+1]):
                        del y[i]
                    elif is_contained('lab', y[i]) and (is_contained('college', y[i+1]) or is_contained('inst', y[i+1]) or is_contained('dep', y[i+1]) or is_contained('school', y[i+1])):
                        del y[i]
                    elif is_contained('dep', y[i]) and (is_contained('college', y[i+1]) or is_contained('inst', y[i+1]) or  is_contained('hosp', y[i+1]) or  is_contained('school', y[i+1]) or  is_contained('fac', y[i+1])):
                        del y[i]
                    elif is_contained('inst', y[i]) and (is_contained('dep', y[i+1]) or is_contained('acad', y[i+1]) or is_contained('hosp', y[i+1]) or is_contained('fac', y[i+1]) or is_contained('cent', y[i+1]) or is_contained('div', y[i+1])):
                        del y[i]
                #    elif y[i] in city_names+removeList:
                #       del y[i]

                




    lightAff = []
    for j in range(len(newAffkomma)):
        lightAffj = []
        for y in newAffkomma[j]:
            lightAffj.append(', '.join(list(y.values())))
        lightAff.append(lightAffj)




    lightAff0 = []

    for k in range(len(lightAff)):
        
        L2 = []
        for s1 in lightAff[k]:
            is_substring = False
            for s2 in lightAff[k]:
                if s1 != s2 and s1 in s2:
                    is_substring = True
                    break
            if not is_substring:
                L2.append(s1)
        lightAff0.append(L2)




    affilDF['lightAff'] = lightAff0




    removeList = ['university','research institute','laboratory' , 'universit','gmbh', 'inc', 'university of', 'research center', 
    'university college','national institute of', 'school of medicine', "university school", 'graduate school of', 'graduate school of engineering', 
    'institute of tropical medicine', 'institute of virology', 'faculty of medicine','laboratory', 'university park', 'institute of science','Polytechnic University']

    city_names = ["Aberdeen", "Abilene", "Akron", "Albany", "Albuquerque", "Alexandria", "Allentown", "Amarillo", "Anaheim", "Anchorage", "Ann Arbor", "Antioch", "Apple Valley", "Appleton", "Arlington", "Arvada", "Asheville", "Athens", "Atlanta", "Atlantic City", "Augusta", "Aurora", "Austin", "Bakersfield", "Baltimore", "Barnstable", "Baton Rouge", "Beaumont", "Bel Air", "Bellevue", "Berkeley", "Bethlehem", "Billings", "Birmingham", "Bloomington", "Boise", "Boise City", "Bonita Springs", "Boston", "Boulder", "Bradenton", "Bremerton", "Bridgeport", "Brighton", "Brownsville", "Bryan", "Buffalo", "Burbank", "Burlington", "Cambridge", "Canton", "Cape Coral", "Carrollton", "Cary", "Cathedral City", "Cedar Rapids", "Champaign", "Chandler", "Charleston", "Charlotte", "Chattanooga", "Chesapeake", "Chicago", "Chula Vista", "Cincinnati", "Clarke County", "Clarksville", "Clearwater", "Cleveland", "College Station", "Colorado Springs", "Columbia", "Columbus", "Concord", "Coral Springs", "Corona", "Corpus Christi", "Costa Mesa", "Dallas", "Daly City", "Danbury", "Davenport", "Davidson County", "Dayton", "Daytona Beach", "Deltona", "Denton", "Denver", "Des Moines", "Detroit", "Downey", "Duluth", "Durham", "El Monte", "El Paso", "Elizabeth", "Elk Grove", "Elkhart", "Erie", "Escondido", "Eugene", "Evansville", "Fairfield", "Fargo", "Fayetteville", "Fitchburg", "Flint", "Fontana", "Fort Collins", "Fort Lauderdale", "Fort Smith", "Fort Walton Beach", "Fort Wayne", "Fort Worth", "Frederick", "Fremont", "Fresno", "Fullerton", "Gainesville", "Garden Grove", "Garland", "Gastonia", "Gilbert", "Glendale", "Grand Prairie", "Grand Rapids", "Grayslake", "Green Bay", "GreenBay", "Greensboro", "Greenville", "Gulfport-Biloxi", "Hagerstown", "Hampton", "Harlingen", "Harrisburg", "Hartford", "Havre de Grace", "Hayward", "Hemet", "Henderson", "Hesperia", "Hialeah", "Hickory", "High Point", "Hollywood", "Honolulu", "Houma", "Houston", "Howell", "Huntington", "Huntington Beach", "Huntsville", "Independence", "Indianapolis", "Inglewood", "Irvine", "Irving", "Jackson", "Jacksonville", "Jefferson", "Jersey City", "Johnson City", "Joliet", "Kailua", "Kalamazoo", "Kaneohe", "Kansas City", "Kennewick", "Kenosha", "Killeen", "Kissimmee", "Knoxville", "Lacey", "Lafayette", "Lake Charles", "Lakeland", "Lakewood", "Lancaster", "Lansing", "Laredo", "Las Cruces", "Las Vegas", "Layton", "Leominster", "Lewisville", "Lexington", "Lincoln", "Little Rock", "Long Beach", "Lorain", "Los Angeles", "Louisville", "Lowell", "Lubbock", "Macon", "Madison", "Manchester", "Marina", "Marysville", "McAllen", "McHenry", "Medford", "Melbourne", "Memphis", "Merced", "Mesa", "Mesquite", "Miami", "Milwaukee", "Minneapolis", "Miramar", "Mission Viejo", "Mobile", "Modesto", "Monroe", "Monterey", "Montgomery", "Moreno Valley", "Murfreesboro", "Murrieta", "Muskegon", "Myrtle Beach", "Naperville", "Naples", "Nashua", "Nashville", "New Bedford", "New Haven", "New London", "New Orleans", "New York", "New York City", "Newark", "Newburgh", "Newport News", "Norfolk", "Normal", "Norman", "North Charleston", "North Las Vegas", "North Port", "Norwalk", "Norwich", "Oakland", "Ocala", "Oceanside", "Odessa", "Ogden", "Oklahoma City", "Olathe", "Olympia", "Omaha", "Ontario", "Orange", "Orem", "Orlando", "Overland Park", "Oxnard", "Palm Bay", "Palm Springs", "Palmdale", "Panama City", "Pasadena", "Paterson", "Pembroke Pines", "Pensacola", "Peoria", "Philadelphia", "Phoenix", "Pittsburgh", "Plano", "Pomona", "Pompano Beach", "Port Arthur", "Port Orange", "Port Saint Lucie", "Port St. Lucie", "Portland", "Portsmouth", "Poughkeepsie", "Providence", "Provo", "Pueblo", "Punta Gorda", "Racine", "Raleigh", "Rancho Cucamonga", "Reading", "Redding", "Reno", "Richland", "Richmond", "Richmond County", "Riverside", "Roanoke", "Rochester", "Rockford", "Roseville", "Round Lake Beach", "Sacramento", "Saginaw", "Saint Louis", "Saint Paul", "Saint Petersburg", "Salem", "Salinas", "Salt Lake City", "San Antonio", "San Bernardino", "San Buenaventura", "San Diego", "San Francisco", "San Jose", "Santa Ana", "Santa Barbara", "Santa Clara", "Santa Clarita", "Santa Cruz", "Santa Maria", "Santa Rosa", "Sarasota", "Savannah", "Scottsdale", "Scranton", "Seaside", "Seattle", "Sebastian", "Shreveport", "Simi Valley", "Sioux City", "Sioux Falls", "South Bend", "South Lyon", "Spartanburg", "Spokane", "Springdale", "Springfield", "St. Louis", "St. Paul", "St. Petersburg", "Stamford", "Sterling Heights", "Stockton", "Sunnyvale", "Syracuse", "Tacoma", "Tallahassee", "Tampa", "Temecula", "Tempe", "Thornton", "Thousand Oaks", "Toledo", "Topeka", "Torrance", "Trenton", "Tucson", "Tulsa", "Tuscaloosa", "Tyler", "Utica", "Vallejo", "Vancouver", "Vero Beach", "Victorville", "Virginia Beach", "Visalia", "Waco", "Warren", "Washington", "Waterbury", "Waterloo", "West Covina", "West Valley City", "Westminster", "Wichita", "Wilmington", "Winston", "Winter Haven", "Worcester", "Yakima", "Yonkers", "York", "Youngstown"]

    city_names = [x.lower() for x in city_names]




    for j in range(len(newAffkomma)):
        for y in newAffkomma[j]:
            for i in list(y.keys()):

                if y[i] in city_names+removeList:
                    del y[i]




    affilDF['uniqueAff4'] =  [[list(d.values()) for d in sublist] for sublist in newAffkomma]


    # # Labels based on legalnames of openAIRE's organizations



    uniList = ['escuela','institu', 'istituto','univ', 'college', 'center', 'centre' , 'cnrs', 'faculty','school' , 'academy' , 'école', 'hochschule' , 'ecole' ]

    labList = ['lab']

    hosplList = ['hospital' ,'clinic', 'hôpital']

    gmbhList = ['gmbh', 'company' , 'industr', 'etaireia' , 'corporation', 'inc']

    musList =  ['museum', 'library']

    foundList =  ['foundation' , 'association','organization' ,'society', 'group' ]

    deptList = ['district' , 'federation'  , 'government' , 'municipal' , 'county','council', 'agency']
    # miistry -> out

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

    for i in range(len(affilDF)):
        affiliationsDict[i] = affilDF['uniqueAff4'].iloc[i]
        




    d_new = {}

    # iterate over the keys of affiliationsDict
    for k in range(len(affiliationsDict)):
        mappedk = []
        # get the list associated with the current key in affiliationsDict
        L = affiliationsDict.get(k, [])
        
        for x in L:
            mapped_listx = [[s, v] for s in x for k2, v in categDicts.items() if k2 in s]
            mappedk.append(mapped_listx)
        
        # add the mapped list to the new dictionary d_new
        d_new[k] = mappedk




    affilDF['Dictionary'] = d_new




    notInList = [i for i in range(len(affilDF)) if affilDF['Dictionary'].iloc[i] == [[]]]
        




    len(affilDF)  - len(notInList)




    len(notInList)


    # # affilDF1 ['DOI', 'affiliations', 'Dictionary','uniqueAff4', 'uniqueAff2','# authors','# uniqueAff']



    affilDF.head(10)




    affilDF1 = affilDF[['DOI', 'affiliations','lightAff','Dictionary','uniqueAff4', 'uniqueAff2','# authors','# uniqueAff']]




    len(affilDF1)




    len(affilDF1.drop_duplicates(subset=['DOI']))


    # ## New column: category based on the labels 



    category = [', '.join(list(set([x[1] for y in affilDF1['Dictionary'].iloc[i] for x in y]))) for i in range(len(affilDF1))]
        




    affilDF1 = affilDF1.copy()




    affilDF1.loc[:, 'category'] = category


    # ### new label: rest



    for i in range(len(affilDF1)):
        if affilDF1['category'].iloc[i] == '':
            affilDF1.iloc[i, affilDF1.columns.get_loc('category')] = 'Rest'




    affiliationsSimple = [
        list(set([inner_list[0] for outer_list in affilDF1['Dictionary'].iloc[i] for inner_list in outer_list]))
        for i in range(len(affilDF1))
    ]




    affilDF1.loc[:,'affilSimple'] = affiliationsSimple




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




    affiliationsSimpleN = []

    for i in range(len(affiliationsSimple)):
        inner = []
        for str in affiliationsSimple[i]:
            if 'university' in str.split():
                for x in strRadiusU(str):
                    inner.append(x)
            elif 'hospital' in str.split():
                for x in strRadiusH(str):
                    inner.append(x)
            else:
                inner.append(str)
        
        affiliationsSimpleN.append(inner)      
                
                
        




    affilDF1.loc[:,'affilSimpleNew'] = affiliationsSimpleN




    len(affilDF1[affilDF1['category'] == 'Rest'])


    # # UNIVS & LABS



    univLabs = [i for i in range(len(affilDF1)) if 'Laboratory' in affilDF1['category'].iloc[i] 
                or 'Univ/Inst' in  affilDF1['category'].iloc[i]]




    univLabsDF = affilDF1.iloc[univLabs].copy()




    univLabsDF.reset_index(inplace = True)




    univLabsDF.drop(columns = ['index'], inplace = True)


    # # Load files from openAIRE



    #with open('dixOpenAIRE_Alletc.pkl', 'rb') as f:
    #    dixOpenAIRE_Alletc = pickle.load(f)

    #with open('dixOpenAIRE_id.pkl', 'rb') as f:
    #    dixOpenAIRE_id = pickle.load(f)




    with open('dixOpenOrgId.pkl', 'rb') as f:
        dixOpenOrgId = pickle.load(f)


    # ## Clean/modify the files



    #dixOpenAIRE_Alletc1 =  {k.replace(',', ''): v for k, v in dixOpenAIRE_Alletc.items()}
    #dixOpenAIRE_id1 = {k.replace(',', ''): v for k, v in dixOpenAIRE_id.items()}




    dixOpenOrgId1 = {k.replace(',', ''): v for k, v in dixOpenOrgId.items()}




    dixOpenOrgId1 = {
        replace_umlauts(key): value
        for key, value in dixOpenOrgId1.items()
    }




    def filter_key(key):
        # Remove all non-alphanumeric characters except Greek letters and Chinese characters
        modified_key = re.sub(r'[^\w\s,Α-Ωα-ωぁ-んァ-ン一-龯，]', '', key)
        modified_key = re.sub(r'\buniversit\w*', 'universit', modified_key, flags=re.IGNORECASE)
        return modified_key

        
    def filter_dictionary_keys(dictionary):
        filtered_dict = {}
        for key, value in dictionary.items():
            filtered_key = filter_key(key)
            filtered_dict[filtered_key] = value
        return filtered_dict


    #dixOpenAIRE_Alletc1 = filter_dictionary_keys(dixOpenAIRE_Alletc1)
    #dixOpenAIRE_id1 = filter_dictionary_keys(dixOpenAIRE_id1)
    dixOpenOrgId1 = filter_dictionary_keys(dixOpenOrgId1)





    dixOpenOrgId2 = {}
    for key, value in dixOpenOrgId1.items():
        updated_key = ' '.join([word for word in key.split() if word.lower() not in ['of', 'at', "the", 'de']])
        dixOpenOrgId2[updated_key] = value




    #del dixOpenAIRE_Alletc1['laboratory']
    #del dixOpenAIRE_Alletc1['university hospital']




    #del dixOpenAIRE_id1['laboratory']
    #del dixOpenAIRE_id1['university hospital']




    del dixOpenOrgId2['universit hospital']




    del dixOpenOrgId2['universit school']




    del dixOpenOrgId2['us']




    del dixOpenOrgId2['ni universit']
    del dixOpenOrgId2['s v universit']




    del dixOpenOrgId2['k l universit']




    def findID(name):
        lnames = []
        for x in list(dixOpenOrgId2.keys()):
            if name.lower() in x:
                lnames.append(x)
        return lnames


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
                    if similarity> 0.31:
                # similarity1 = cosine_similarity(x_vector1, s_vector1)[0][0]
                    #similarity2 = Levenshtein.ratio(s,x)


                        best.append([x, similarity])#(similarity+similarity2)/2])
            
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



    def Doi_Ids(m, DF, dixOpenAIRE, simU, simG):
        
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
        
        lnamelist = list(dixOpenAIRE.keys())
        dix = {}    # will store indeces and legalnames of organizations of the DOI { i : [legalname1, legalname2,...]}
        deiktes = []  # stores indeces where a match is found
        vectorizer = CountVectorizer()
        similarity_ab = [] # stores lists of similarity scores of the mathces 
        pairs = [] #  pairs[i] =  [ [s,x,t] ] where (s,x) is a match and t the corresponding similarity score
        
        for k in range(m):
            similar_k = []
            pairs_k = []


            for s in DF['affilSimpleNew'].iloc[k]:

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

                                if 'and' in s:
                                    list_s = s.split(' and ')
                                    for t in list_s:
                                        if is_contained(x, t) and is_contained('univ', t):
                                            t_vector = vectorizer.fit_transform([t]).toarray()
                                            x_vector = vectorizer.transform([x]).toarray()

                                # Compute similarity between the vectors
                                            similarity = cosine_similarity(t_vector, x_vector)[0][0]
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
                                if 'and' in s:
                                    list_s = s.split(' and ')
                                    for t in list_s:
                                        if is_contained(x, t):
                                            t_vector = vectorizer.fit_transform([t]).toarray()
                                            x_vector = vectorizer.transform([x]).toarray()

                                # Compute similarity between the vectors
                                            similarity = cosine_similarity(t_vector, x_vector)[0][0]
                                            if similarity > simG:
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
            
        
        dixDoiAff = {DF['DOI'].iloc[key]: value for key, value in dix.items()} # dictionary {DOI : legalnames} 
        
        #dixDoiPid1 = {key : [dixOpenAIRE[x] for x in value if x in  lnamelist] for key , value in dixDoiAff.items()}
        
    # dixDoiPid = {key : [dixOpenAIRE[x] for x in value] for key , value in dixDoiAff.items()} # dictionary {DOI : PIDs} 
        
        
        
    ## Define the new Dataframe
        
        doiIdDF = pd.DataFrame()
        doiIdDF['DOI'] = list(dixDoiAff.keys())
        doiIdDF['Affiliations'] = list(DF['affiliations'].iloc[list(set(deiktes))])

        doiIdDF['Unique affiliations'] = list(DF['uniqueAff2'].iloc[list(set(deiktes))])
        doiIdDF['light affiliations'] = list(DF['lightAff'].iloc[list(set(deiktes))])

        
        doiIdDF['# Authors'] = list(DF['# authors'].iloc[list(set(deiktes))])


        doiIdDF['# Unique affiliations'] = list(DF['# uniqueAff'].iloc[list(set(deiktes))])

        doiIdDF['Candidates for matching'] = list(DF['affilSimpleNew'].iloc[list(set(deiktes))])
        doiIdDF['Candidates old'] = list(DF['affilSimple'].iloc[list(set(deiktes))])


        doiIdDF['Matched openAIRE names'] = list(dix.values())
        doiIdDF['# Matched orgs'] = [len(list(dix.values())[i]) for i in range(len(list(dix.values())))]
        

        doiIdDF['Similarity score'] = similarity_ab
        #perfectSim = [[1 if num >= 1 else 0 for num in inner_list] for inner_list in similarity_ab]

        #doiIdDF['Perfect match'] = perfectSim
        #perfectSimSum = [sum(x) for x in perfectSim]
        #doiIdDF['Perfect sum'] = perfectSimSum
        Pairs = [lst for lst in pairs if lst]
        doiIdDF['Pairs'] = Pairs
        doiIdDF['mult'] = index_multipleMatchings(doiIdDF)[1]
        #doiIdDF['Cleaning'] =  list(DF['Cleaning'].iloc[list(set(deiktes))])


        


    ## Correct the matchings
        needCheck = list(set([i for i in range(len(doiIdDF)) for k in list(doiIdDF['mult'].iloc[i].values()) if k>1]))
        
        #needCheck = [i for i  in range(len(doiIdDF)) if doiIdDF['# Matched orgs'].iloc[i] - max(doiIdDF['# Authors'].iloc[i],doiIdDF['# Unique affiliations'].iloc[i]) >0 or    i in index_multipleMatchings(doiIdDF)[0]]

        ready = [i for i in range(len(doiIdDF)) if i not in needCheck]
    
        best = [ bestSimScore1(doiIdDF['light affiliations'].iloc[i], len(doiIdDF['Candidates for matching'].iloc[i]), doiIdDF['Pairs'].iloc[i],doiIdDF['mult'].iloc[i], simU, simG) for i in needCheck]
        #best = [ bestSimScore(doiIdDF['light affiliations'].iloc[i], doiIdDF['Matched openAIRE names'].iloc[i], doiIdDF['Pairs'].iloc[i]) for i in needCheck]
        best_o = []
        best_s = []
        
        for x in best:
            best_o.append([x[i][0]  for i in range(len(x))])
            best_s.append([round(x[i][1],2)  for i in range(len(x))])
        numMathced = [len(best_s[i]) for i in range(len(needCheck))]
        

        
        dfFinal0 = (doiIdDF.iloc[ready]).copy()
        dfFinal0['index'] = ready
        
        dfFinal1 = (doiIdDF.iloc[needCheck]).copy()
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



        
        
        return [perc,finalDF,doiIdDF, needCheck]
        




    result = Doi_Ids(len(univLabsDF), univLabsDF, dixOpenOrgId2, 0.7,0.82)




    result[0]


    # # HTML



    finaldf = result[1]
    
    def update_Z(row):
        new_Z = []
        for i in range(len(row['IDs'])):
            entry = {'openaireId': row['IDs'][i], 'confidence': row['Similarity score'][i]}
            new_Z.append(entry)
        return new_Z

    # Update the values in column 'Z' using 'apply'
    finaldf['affiliations'] = finaldf.apply(update_Z, axis=1)

    finaldf_output = finaldf[['DOI','affiliations']]
    finaldf_output = finaldf_output.rename(columns={'DOI': 'doi'}).copy()


    """
    # JSON
    """


    match0 = finaldf_output.to_json(orient='records',lines=True)

    # Save the JSON to a file
    with open('output/' + name, 'w') as f:
        f.write(match0)

    

with tarfile.open(sys.argv[2], "r:gz") as tar:
    while True:
        member = tar.next()
        # returns None if end of tar
        if not member:
            break
        if member.isfile():
            print("processing " + member.name)
            current_file = tar.extractfile(member)

            dfsList = pd.read_json(current_file, orient='records')
            do(member.name, dfsList)
    print("Done")









