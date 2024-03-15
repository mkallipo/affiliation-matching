# Affiliation-Matching Repository

This repository contains code and data for matching DOIs of Crossref JSON files with organization IDs from the OpenAIRE (https://www.openaire.eu) or ROR (https://ror.org) database.

🚀 As it is still a work in progress, *the repository may not always be up-to-date*. 
However, I will incorporate improvements and bug fixes regularly. 

## Main files

- `dois_to_rors`: This is the main code for the matching process. It takes JSON files as input and returns a JSON with matchings between the DOIs of the JSONs and ROR_ids of organizations in the ROR database. The organizations include universities, institutions, hospitals, labs, foundations.

- `main_functions.py` contains the main algorithm.
  
- `matching.ipynb`: Is a Jupyter Notebook for testing the code. In addition to the JSON file (`dois_match.json`) it returns two EXCEL files (`affis_match.xlx` and `dois_match.xlx` respectively), one with the distinct affiliations of the JSON input, the matched organizations and the corresponding similarity scores and one with the DOIs of the JSON input and the matched organizations and the similarity scores.

- `dix_acad.pkl`: This file is a pickled dictionary with keys legalnames and alternativenames of organizations in the ROR database. The corresponding values are the ROR PIDs (Persistent Identifiers) associated with each organization.

- `dix_mult`, `dix_city`, `dix_country`: three more pickled dictionary with keys legalnames and alternativenames of organizations in the ROR database, necessary in the case where different organizations share the same name.

- `sample.json`: Is a sample of 1000 DOIs obtained from 300 json files from the Crossref database, which can be used for testing and validation purposes.
  
- `dois_match.json`, `affs_match.xlx` and `dois_match.xlx`: The outputs for the `sample.json` file as described above.

- `find_year`: Is a Python script that takes a JSON file as input and generates a CSV file containing the years from the issued date field and the corresponding number of DOIs.

- requirements.txt


## Usage

1. Run the `matching.ipynb` notebook in a Jupyter environment. Make sure to provide the JSON file that you want to match as input.

2. The notebook will process the input JSON file and generate a the EXCEL and JSON files with the matchings between DOIs and organization ROR_ids.


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


__Output__: A JSON file containing DOIs from Crossref's data and their matchings to ROR ids the corresponding confidence scores, for example: 
>`{"DOI":"10.1061\/(asce)0733-9399(2002)128:7(759)","Matchings":[{"RORid":["https:\/\/ror.org\/01teme464"],"Confidence":0.73},{"RORid":["https:\/\/ror.org\/03yxnpp24"],"Confidence":0.7071067812}]}`.


### Steps:

1. **Data Preprocessing:** The affiliations' strings are imported and undergo cleaning, tokenization, and removal of stopwords.
2. **Categorization:** Data preprocessing has already been conducted on ROR's data, involving the analysis of word frequency ('keywords') within the legal names of ROR's organizations to define specific categories. These categories include "Univ/Inst," "Laboratory," "Hospital," "Company," "Museum," "Government," "Foundation," and "Rest". ROR's organizations have subsequently been assigned to these categories based on their legal names. The algorithm employs a similar approach to categorize affiliations into these same groups.
4. **Filtering:** Almost 40\% of the organizations in the ROR’s database lie in the category "Rest". More than 80\% of Crossref's affiliations lie in the categories "Univ/Inst", "Laboratory", "Hospital", and "Foundation". At the moment the algorithm focuses on these cases and excludes the ROR's organizations labeled as "Rest". This reduces significantly the dataset we need to search.
5. **String Shortening:** The objective is to extract pertinent details from each affiliation string. The algorithm divides the string whenever a comma (,) or semicolon (;) is detected. It then applies specific 'rules' to these segments and retains only those containing relevant keywords. Additionally, it trims down the segments by preserving words in proximity to particular keywords like "university," "institute," "laboratory," or "hospital." As a result, the average string length is reduced from 90 to 35 characters.
6. **Matching with ROR's Database:** The algorithm checks whether a substring containing a keyword is linked to a legal name or to an alternative name in the organizations listed in the ROR's database. In order to identify the most accurate match, the algorithm employs cosine similarity. For strings containing "universi," a similarity threshold of 0.7 is employed, while for all other keywords, the threshold is set at 0.82. Although alternative methods like Levenshtein Distance or Jaro-Winkler Distance were considered for measuring string similarity, it was concluded that cosine similarity was the most appropriate choice for this specific application.
7. **Refinement:** If multiple matches are found above the similarity thresholds, the algorithm performs another check. It applies cosine similarity between the organizations found in the openAIRE database and the original affiliation string. This comparison takes into account additional information present in the original affiliation, such as addresses or city names. The algorithm aims to identify the best fit among the potential matches. Note that the case where two or more different organizations share the same name is also considered.



## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

