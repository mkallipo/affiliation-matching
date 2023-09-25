import pandas as pd
from pandas import json_normalize
import re
import unicodedata
from collections import defaultdict

import tarfile
import logging
import html

import xml.etree.ElementTree as ET
import json
import xmltodict

import requests
import gzip
from io import BytesIO
from bs4 import BeautifulSoup
import os

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor,wait,ALL_COMPLETED

import pickle
import sys 

import Levenshtein
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity



from helper_functions import *
from main_functions import *


with open('dix_acad.pkl', 'rb') as f:
    dix_acad = pickle.load(f)

with open('dix_mult.pkl', 'rb') as f:
    dix_mult = pickle.load(f)

with open('dix_city.pkl', 'rb') as f:
    dix_city = pickle.load(f)
    
with open('dix_country.pkl', 'rb') as f:
    dix_country = pickle.load(f)


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
        if type(final[i]['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']) == list:
            ids.append(final[i]['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId'])
        else:
            ids.append([final[i]['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']])
    dois = []
    for i in range(len(df)):
        doisi= []
        for j in range(len(ids[i])):
            try: 
                if ids[i][j]['@IdType'] == 'doi':
                    doisi.append(ids[i][j]['#text'])
            except KeyError as e:
            # Handle the KeyError exception here
                print(f"KeyError: {e} occurred for index {i}")
            
        dois.append(doisi)
        
        

    affList = []

    for i in range(len(df)):
        affList_i = []
        
        try:
            fi = final[i]['PubmedArticle']['MedlineCitation']['Article']['AuthorList']['Author']
            # Continue processing fi here
        except KeyError as e:
            # Handle the KeyError exception here
            print(f"KeyError: {e} occurred for index {i}")


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

                            
                                    
    df['DOI'] = dois 
    df['Affiliations'] = affList

    indices = []
    
    for i in range(len(df)):
        if len(dois[i])>0:
            indices.append(i)
            
            
    df_final = (df.iloc[indices]).reset_index()
    df_final.drop(columns = 'index', inplace = True) 
    doi_string = [x[0] for x in list(df_final['DOI'])]
    df_final['DOI'] = doi_string
    
    return df_final


url = "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/"
response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

links = soup.find_all("a")

file_names = []

for link in links:
    href = link.get("href")
    if href:
        # Extract the file name from the URL
        file_name = os.path.basename(href)
        if file_name.endswith(".gz"):
            file_names.append(file_name)

url_list = [url+file for file in file_names]



for xml in range(44, len(url_list)): 
    response = requests.get(url_list[xml])

# Create a BytesIO object from the compressed content
    compressed_content = BytesIO(response.content)

# Decompress the content using gzip
    with gzip.GzipFile(fileobj=compressed_content) as decompressed_content:
    # Now you have the decompressed content in 'decompressed_content'
    # You can parse it as XML using ElementTree or any other XML parsing library
        root = ET.parse(decompressed_content).getroot()

# Process the XML content as needed


    article_list = []

    # Iterate over the Article elements
    for article in root.iter('PubmedArticle'):
        # Find the AffiliationInfo element within each Article
        affiliation_info = article.find('.//AffiliationInfo')
        
        if affiliation_info is not None:
            # Extract the text within the Article element
            article_text = ET.tostring(article, encoding='unicode')
            article_list.append({'Article': article_text})
            
            
    pubmedDF = create_df(article_list)

    if len(pubmedDF)==0:
        continue 
        
    uniqueAff = []

    for i in range(len(pubmedDF)):
        uniqueAff.append(list(set(x.lower() for x in pubmedDF['Affiliations'].iloc[i])))
        
    pubmedDF['Unique affiliations'] = uniqueAff
    
    
    doi_df = pubmedDF[['DOI', 'Unique affiliations']].copy()
    academia_df = create_df_algorithm(doi_df)

    if len(academia_df)>0:   
        result = Aff_Ids(len(academia_df), academia_df,dix_acad, dix_mult, dix_city, dix_country, 0.7,0.82)
    
        if len(result)>0:

            affs_match = result[['Original affiliations','Matched organizations', 'unique ROR']]

            dict_aff_open = {x: y for x, y in zip(result['Original affiliations'], result['Matched organizations'])}
            dict_aff_id = {x: y for x, y in zip(result['Original affiliations'], result['ROR'])}
            #dict_aff_score = {x: y for x, y in zip(result['Original affiliations'], result['Similarity score'])}

            dict_aff_score = {}
            for i in range(len(result)):
                if type(result['Similarity score'].iloc[i]) == list:
                    dict_aff_score[result['Original affiliations'].iloc[i]] = result['Similarity score'].iloc[i]
                else:
                    dict_aff_score[result['Original affiliations'].iloc[i]] = [result['Similarity score'].iloc[i]]
                    

            pids = []
            for i in range(len(doi_df)):
                pidsi = []
                for aff in doi_df['Unique affiliations'].iloc[i]:
                    if aff in list(dict_aff_id.keys()):
                        pidsi = pidsi + dict_aff_id[aff]
                # elif 'unmatched organization(s)' not in pidsi:
                #     pidsi = pidsi + ['unmatched organization(s)']
                pids.append(pidsi)
                        
                        
            names = []
            for i in range(len(doi_df)):
                namesi = []
                for aff in doi_df['Unique affiliations'].iloc[i]:
                    if aff in list(dict_aff_open.keys()):
                        try:
                            namesi = namesi + dict_aff_open[aff]
                        except TypeError:
                            namesi = namesi + [dict_aff_open[aff]]
                        
                names.append(namesi)
                
            scores = []
            for i in range(len(doi_df)):
                scoresi = []
                for aff in doi_df['Unique affiliations'].iloc[i]:
                    if aff in list(dict_aff_score.keys()):
                        scoresi = scoresi +  dict_aff_score[aff]
                        
                scores.append(scoresi)
                
                
            doi_df['Matched organizations'] = names
            doi_df['ROR'] = pids
            doi_df['Scores'] = scores


            unmatched = [i for i in range(len(doi_df)) if doi_df['Matched organizations'].iloc[i] == []]
                    
            matched = [i for i in range(len(doi_df))  if i not in unmatched]


            final_df0 =  doi_df.iloc[matched].copy()
            final_df0.reset_index(inplace = True)

            final_df = final_df0[['DOI',"Unique affiliations",'Matched organizations','ROR', 'Scores']].copy()

            def update_Z(row):
                if len(row['ROR']) == 0 or len(row['Scores']) == 0:
                    return []
                
                new_Z = []
                for ror, score in zip(row['ROR'], row['Scores']):
                    entry = {'RORid': ror, 'Confidence': score}
                    new_Z.append(entry)
                return new_Z

            matching = final_df.apply(update_Z, axis=1)

            final_df['Matchings'] = matching

            final_df_short = final_df[['Unique affiliations','Matched organizations','ROR','Scores']]

            # 3. JSON [Final output]


            doi_df_output = final_df[['DOI','Matchings']]
            
            doi_json = doi_df_output.to_json(orient='records', lines=True)
            
            filename = f'file{xml}.json'

            with open(filename, 'w') as f:
                f.write(doi_json)
            
    
            
        
                  
        
