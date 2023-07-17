# Matching Repository

This repository contains code and data for matching DOIs of Crossref JSON files with organization IDs from the OpenAIRE database.

## Files

- `matching.py`: This is the main code for the matching process. It takes JSON files as input and returns a JSON (`output.json`) with matchings between the DOIs of the JSONs and IDs of organizations in the OpenAIRE database. 
The organizations include universities, institutions, hospitals, labs.

- `matching.ipynb`: Is a Jupyter Notebook for testing the code. In addition to the JSON file (`output.json`) it returns two EXCEL files (`affilMatch` and `doisMatch` respectively), one with the distinct affiliations of the JSON input, the matched openAIRE organizations and the corresponding similarity scores and one with the DOIs of the JSON input and the matched openAIRE organizations and the similarity scores.

- `dixAcadRor.pkl`: This file is a pickled dictionary that contains keys representing legalnames and alternativenames of organizations in the OpenAIRE database. 
The corresponding values are the ROR PIDs (Persistent Identifiers) associated with each organization.
Note: the prefix of the openAIRE id of all organizations considered is `openorgs_`.

- `sample.json`: Is a sample of 1000 DOIs obtained from 300 json files from the Crossref database, which can be used for testing and validation purposes.
  
- `output.json`, `affilMatch` and `doisMatch`: The outputs for the `sample.json` file as described above.

- `findOrg.ipynb`: Is another Jupyter Notebook for evaluating the results of the matching algorithm.

- `findYear`: Is a Python script that takes a JSON file as input and generates a CSV file containing the years from the issued date field and the corresponding number of DOIs.


## Dependencies

Make sure you have the following dependencies installed before running the code:

- pandas
- re
- pickle
- unicodedata
- scikit-learn (for `CountVectorizer` and `cosine_similarity`)

## Usage

1. Run the `matching.ipynb` notebook in a Jupyter environment. Make sure to provide the JSON files that you want to match as input.

2. The notebook will process the input JSON files and generate a JSON file with the matchings between DOIs and organization IDs from the OpenAIRE database.


## Description of the algorithm

### Goal: Recognize openAIRE's organizations inside the Crossref's data and match to each DOI the corresponding ROR ids

__Input__: A JSON file from Crossref's data. Here is an example of the part where the affiliations and DOI information is found. 
> `'author': [{'given': 'Orlando',
   'family': 'Maeso',
   'sequence': 'first',
   'affiliation': [{'name': 'Escuela Técnica Superior de Ingenieros Industriales, Univ. de Las Palmas de Gran Canaria, Tafira Baja, 35017-Las Palmas de Gran Canaria, Spain.'}]},
  {'given': 'Juan J.',
   'family': 'Aznárez',
   'sequence': 'additional',
   'affiliation': [{'name': 'Escuela Técnica Superior de Ingenieros Industriales, Univ. de Las Palmas de Gran Canaria, Tafira Baja, 35017-Las Palmas de Gran Canaria, Spain.'}]},
  {'given': 'José',
   'family': 'Domnguez',
   'sequence': 'additional',
   'affiliation': [{'name': 'Escuela Superior de Ingenieros, Univ. de Sevilla, Camino de los Descubrimientos s/n, 41092-Sevilla, Spain.'}]}],
 'DOI': '10.1061/(asce)0733-9399(2002)128:7(759)`


__Output__: A JSON file containing DOIs from Crossref's data and their matchings to ROR ids frop openAIRE's organizations and the corresponding confidence scores, for example: 
>`{"DOI":"10.1061\/(asce)0733-9399(2002)128:7(759)","Matchings":[{"RORid":["https:\/\/ror.org\/01teme464"],"Confidence":0.73},{"RORid":["https:\/\/ror.org\/03yxnpp24"],"Confidence":0.7071067812}]}`.


### Steps:

1. **Data Preprocessing:** The affiliations' strings are imported and undergo cleaning, tokenization, and removal of stopwords.
2. **Categorization:** The algorithm categorizes the affiliations based on the frequency of words appearing in the legal names of openAIRE's organizations (a preparatory work with the openAIRE's data has already been carried out. The categories are `"Univisties/Instirutions"`, `"Laboratories"`, `"Hospitals"`, `"Companies"`, `"Museums"`, `"Governments"`, and `"Rest"`). 
In the same way the openAIRE's organizations are grouped.
3. **Filtering:** Half of the organizations in the openAIRE’s database lie in the category `Rest`. More than 80% of Crossref's affiliations lie in the categories `Universities/Institutes` and `Laboratories`. At the moment the algorithm focuses on these cases and excludes the openAIRE organizations labeled as `"Rest"`. This reduces significantly the dataset we need to search.
4. **String Shortening:** The goal is to extract only essential information from each affiliation string. The algorithm splits the string whenever a comma (`,`) or semicolon (`;`) is present. It applies certain 'association rules' to these substrings and keeps only the ones containing 'keywords.' It further shortens the substrings by retaining only words close to specific keywords like `"university"`,`"institute"`, or `"hospital"`. The average length of the strings is reduced from ~90 to ~35 characters.
5. **Matching with openAIRE's Database:** The algorithm verifies if a substring containing a keyword corresponds to or is part of a legal name or alternative name within the organizations in the openAIRE's database . To identify the best match, the algorithm utilizes cosine similarity. A similarity threshold of `0.7` is applied to strings containing `"universit"`, while for all other keywords, the threshold is set to `0.82`. Alternative methods such as Levenshtein Distance or Jaro-Winkler Distance were considered for measuring string similarity, but cosine similarity was determined to be the most suitable choice for this particular application
6. **Refinement with openAIRE's Database:** If multiple matches are found above the similarity thresholds, the algorithm performs another check. It applies cosine similarity between the organizations found in the openAIRE database and the original affiliation string. This comparison takes into account additional information present in the original affiliation, such as addresses or city names. The algorithm aims to identify the best fit among the potential matches.


## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

