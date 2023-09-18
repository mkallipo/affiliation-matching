import pandas as pd
from pandas import json_normalize
import re
import unicodedata
from collections import defaultdict

import pickle
import sys 

import Levenshtein
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import xml.etree.ElementTree as ET
import json
import xmltodict

import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

sys.path.append('/Users/myrto/Documents/openAIRE')

from helper_functions import *
from main_functions import *

# Load the XML file

# Send an HTTP GET request to the webpage with the .xml.gz link
url = 'https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/pubmed23n0048.xml.gz'
response = requests.get(url)

# Create a BytesIO object from the compressed content
compressed_content = BytesIO(response.content)

# Decompress the content using gzip
with gzip.GzipFile(fileobj=compressed_content) as decompressed_content:
 
    root = ET.parse(decompressed_content).getroot()

# Initialize lists to store article data
article_list = []

# Iterate over the Article elements
for article in root.iter('PubmedArticle'):
    # Find the AffiliationInfo element within each Article
    affiliation_info = article.find('.//AffiliationInfo')
    
    if affiliation_info is not None:
        # Extract the text within the Article element
        article_text = ET.tostring(article, encoding='unicode')
        article_list.append({'Article': article_text})


def create_df(articleList):
    df = pd.DataFrame(articleList)
    final = []
    for i in range(len(df)):
        line = df['Article'].iloc[i]
    # Remove all occurrences of '\n'
        line = line.replace('\n', '')

        final.append(json.loads(json.dumps(xmltodict.parse(line))))
    ids = []
    for i in range(len(df)):
        ids.append(final[i]['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId'])
        

    affList = []

    for i in range(len(df)):
        affList_i = []
        fi = final[i]['PubmedArticle']['MedlineCitation']['Article']['AuthorList']['Author']


        if type(fi) == dict:
            if type(fi['AffiliationInfo']) == dict:
                affList_i.append(fi['AffiliationInfo']['Affiliation'])
            else:
                    for j in range(len(fi['AffiliationInfo'])):
                        affList_i.append(fi['AffiliationInfo'][j]['Affiliation'])
                        
                    
                
        else:
            for m in range(len(fi)):
                if 'AffiliationInfo' in list(fi[m].keys()):
                    if type(fi[m]['AffiliationInfo']) == dict:
                        affList_i.append(fi[m]['AffiliationInfo']['Affiliation'])
                    else:
                        for j in range(len(fi[m]['AffiliationInfo'])):
                            affList_i.append(fi[m]['AffiliationInfo'][j]['Affiliation'])
                        
                    
    
        affList.append(list(set(affList_i)))

                            
                                    
    df['ids'] = ids 
    df['Affiliations'] = affList
    
    return df

pubmedDF = create_df(article_list)


uniqueAff = []

for i in range(len(pubmedDF)):
    uniqueAff.append(list(set(x.lower() for x in pubmedDF['Affiliations'].iloc[i])))
    
    
pubmedDF['Unique affiliations'] = uniqueAff
generalDF = pubmedDF[['ids', 'Unique affiliations']].copy()

doi_df = generalDF.rename(columns = {'ids':'DOI'})

academia_df = create_df_algorithm(doi_df)



with open('dix_acad.pkl', 'rb') as f:
    dix_acad = pickle.load(f)

with open('dix_mult.pkl', 'rb') as f:
    dix_mult = pickle.load(f)

with open('dix_city.pkl', 'rb') as f:
    dix_city = pickle.load(f)
    
with open('dix_country.pkl', 'rb') as f:
    dix_country = pickle.load(f)
