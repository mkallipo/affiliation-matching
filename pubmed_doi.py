from bs4 import BeautifulSoup
import os
import pandas as pd
import requests
from io import BytesIO
import gzip
import xml.etree.ElementTree as ET

import json
import xmltodict
import logging


def xml_article(xml): 
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
    return article_list
            
            
def doi_pmi(article_list):
    df = pd.DataFrame(article_list)
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
                # Handle the KeyError here, e.g., by providing a default value or taking appropriate action
            print(f"KeyError: {e} occurred for index {i}")  # You can replace 'pass' with your desired error-handling logic
            key_errors.append(i)

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
                key_errors.append(i)
            
        dois.append(doisi)


    pmids = []
    for i in range(len(df)):
        pmidsi= []
        for j in range(len(ids[i])):
            try: 
                if ids[i][j]['@IdType'] == 'pubmed':
                    pmidsi.append(ids[i][j]['#text'])
            except KeyError as e:
            # Handle the KeyError exception here
                print(f"KeyError: {e} occurred for index {i}")
                key_errors.append(i)
    

            
        pmids.append(pmidsi)
        
    
    keep = [i for i in range(len(df)) if  len(dois[i])>0]
        
    df['PMID'] = [x[0] for x in  pmids] 

    df['DOI'] = [x[0]  if len(x)>0 else '-' for x in  dois]  
    
    df = df.iloc[keep]


    
    
    return df.drop(columns = ['Article'])



def doi_pmi_final(xml):
    file_name = os.path.join(csv_folder, f'output_{xml}.csv')

    return doi_pmi(xml_article(xml)).to_csv(file_name, index=False)



url = "https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/"

# Send an HTTP GET request to the webpage
response = requests.get(url)


soup = BeautifulSoup(response.text, "html.parser")

    # Find all the links on the webpage (you may need to adjust the selector)
links = soup.find_all("a")

    # List to store the file names
file_names = []

    # Loop through the links and extract file names ending with ".gz"
for link in links:
    href = link.get("href")
    if href:
        # Extract the file name from the URL
        file_name = os.path.basename(href)
        if file_name.endswith(".gz"):
            file_names.append(file_name)
            
url_list = [url+file for file in file_names]

csv_folder = '/Users/myrto/Documents/openAIRE/pubmed/csv_doi_pubmed'


    # Create the directory if it doesn't exist
os.makedirs(csv_folder, exist_ok=True)


