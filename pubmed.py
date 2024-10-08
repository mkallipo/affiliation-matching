import pandas as pd
from pandas import json_normalize
import re
import unicodedata
from collections import defaultdict

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
from concurrent.futures import ProcessPoolExecutor,wait,ALL_COMPLETED
import sys 
import Levenshtein
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from create_input import *
from affro import *


with open('dictionaries/dix_acad.json', 'rb') as f:
    dix_acad = json.load(f)

with open('dictionaries/dix_mult.json', 'rb') as f:
    dix_mult = json.load(f)

with open('dictionaries/dix_city.json', 'rb') as f:
    dix_city = json.load(f)
    
with open('dictionaries/dix_country.json', 'rb') as f:
    dix_country = json.load(f)

with open('dictionaries/dix_status.json', 'rb') as f:
    dix_status = json.load(f)

def create_df(articleList):
    df = pd.DataFrame(articleList)
    final = []
    key_errors = []

    for i in range(len(df)):
        line = df['Article'].iloc[i]
    # Remove all occurrences of '\n'
        line = line.replace('\n', '')

        final.append(json.loads(json.dumps(xmltodict.parse(line))))
    ids = []
    for i in range(len(df)):
        try:
            if type(final[i]['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']) == list:
                ids.append(final[i]['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId'])
            else:
                ids.append([final[i]['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']])
        except KeyError as e:
            print(f"KeyError: {e} occurred for index {i}")
            key_errors.append(i)
            
    dois = []
    for i in range(len(df)):
        doisi= []
        for j in range(len(ids[i])):
            try: 
                if ids[i][j]['@IdType'] == 'doi':
                    doisi.append(ids[i][j]['#text'])
            except KeyError as e:
                print(f"KeyError: {e} occurred for index {i}")
                key_errors.append(i)
            
        dois.append(doisi)
                
    
    
        

    affList = []

    for i in range(len(df)):
        affList_i = []
        
        try:
            fi = final[i]['PubmedArticle']['MedlineCitation']['Article']['AuthorList']['Author']
        except KeyError as e:
            print(f"KeyError: {e} occurred for index {i}")
            key_errors.append(i)


        
        if type(fi) == dict:
            try:
                if type(fi['AffiliationInfo']) == dict:
                    affList_i.append(fi['AffiliationInfo']['Affiliation'])
                else:
                    for j in range(len(fi['AffiliationInfo'])):
                        affList_i.append(fi['AffiliationInfo'][j]['Affiliation'])
            except KeyError as e:
                print(f"KeyError: {e} occurred for index {i}")
                key_errors.append(i)

                        
                    
                
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
    indices_final = [i for i in indices if i not in key_errors]

            
    df_final = (df.iloc[indices_final]).reset_index()
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




def xml_to_json(xml):
    try:
    
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

        if len(pubmedDF)>0:
        # continue 
            
            uniqueAff = []
            remove_rows = []
        

            for i in range(len(pubmedDF)):
                try:
                    uniqueAff.append(list(set(x.lower() for x in pubmedDF['Affiliations'].iloc[i])))
                except AttributeError as e:
                    print(f'AttributeError {e} at index {i}')
                    uniqueAff.append(list(set(x for x in pubmedDF['Affiliations'].iloc[i])))
        
                    remove_rows.append(i)
                    
                
            pubmedDF['Unique affiliations'] = uniqueAff
        
        
            doi_df = pubmedDF[['DOI', 'Unique affiliations']].copy()
            doi_df = doi_df.drop(remove_rows)
            doi_df.reset_index(inplace = True)
            
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
        
                    unique_matching = []
                
                    for x in matching: 
                        list_of_dicts = x


                        max_values = {}
                        result_list = []

                        for d in list_of_dicts:
                            value1 = d['RORid']
                            value2 = d['Confidence']

                            # Check if value1 is already in max_values dictionary
                            if value1 in max_values:
                                # If value2 is greater, update max_values
                                if value2 > max_values[value1]:
                                    max_values[value1] = value2
                                    # Replace the dictionary in the result_list with the one with higher value2
                                    result_list = [item for item in result_list if item['RORid'] != value1]
                                    result_list.append(d)
                            else:
                                # If value1 is not in max_values, add it with its value2
                                max_values[value1] = value2
                                result_list.append(d)
                        unique_matching.append(result_list)

                        new_matching = []
                        for x in unique_matching:
                            new_x = []
                            for y in x:
                                if  dix_status[y['RORid']][0] == 'active':
                                    new_x.append({'Provenance':'AffRo', 'PID':'ROR','Value':y['RORid'], 'Confidence': y['Confidence'], 'Status':'active'})
                                else:
                                    if dix_status[y['RORid']][1] == '':
                                        new_x.append({'Provenance':'AffRo', 'PID':'ROR','Value':y['RORid'], 'Confidence': y['Confidence'], 'Status':dix_status[y['RORid']][0]})
                                    else:
                                        new_x.append({'Provenance':'AffRo', 'PID':'ROR','Value':y['RORid'], 'Confidence': y['Confidence'], 'Status':dix_status[y['RORid']][0]})
                                        new_x.append({'Provenance':'AffRo', 'PID':'ROR','Value':dix_status[y['RORid']][1], 'Confidence': y['Confidence'], 'Status':'active'})
                            new_matching.append(new_x)
                                        
                        final_df['Matchings'] = new_matching    
        
                    # 3. JSON [Final output]
        
        
                    doi_df_output = final_df[['DOI','Matchings']]
                    
                    doi_json = doi_df_output.to_json(orient='records', lines=True)
                    
                
                    filename = f'file{xml}.json'
                    with open("pubmed-output/" + filename, 'w') as f:

                        f.write(doi_json)
    
    except Exception as e:
        print(e)


numberOfThreads = int(sys.argv[1])
executor = ProcessPoolExecutor(max_workers=numberOfThreads)

futures = [executor.submit(xml_to_json, xml) for xml in range(0, len(url_list))]
done, not_done = wait(futures)
print(not_done)