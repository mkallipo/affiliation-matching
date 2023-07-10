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


## Description of the algorithm -- examples

__Goal__: Recognize openAIRE's organizations inside the Crossref's data and match to each DOI the corresponding ROR ids.

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


__Steps:__

1. After __importing__, __cleaning__, __tokenizing__ the affiliations’ strings and __removing stopwords__, the algorithm __categorizes the affiliations__ based on the frequency of words appearing in the legal names of openAIRE's organizations (a preparatory work with the openAIRE's data has already been carried out. The categories are _Univisties/Instirutions_, _Laboratories_, _Hospitals_, _Companies_, _Museums_, _Governments_, and _Rest_). For example, the affiliations:

* A1. `"Obstetrical Perinatal and Pediatric Epidemiology Research Team Institute of Health and Medical Research Centre of Research in Epidemiology and Statistics Université Paris Cité  Paris France"`

* A2. `"From the Department of Cardiovascular Science and Medicine, Chiba University Graduate School of Medicine, Chiba, Japan (M.A., H.T., T.N., H.H., T.S., Y.M., I.K.); the Department of Cardiovascular Medicine, Graduate School of Medicine, University of Tokyo, Tokyo, Japan (H.U.); and the Department of Metabolic Diseases, Graduate School of Medicine, University of Tokyo, Tokyo, Japan (N.K., T.K.)."`

* A3. `"Department of Biology, University of California, San Diego, La Jolla 92093-0063."`

  lie in the _Univisties/Instirutions_ category, while

* A4 `"Laboratoire Central dImmunologie dHistocompatibilite, INSERM U93, Paris, France"` lies in the _Laboratories_ category

  and the 

* A5 `"advancecsg lisbon portugal"` is in the _Rest_. 

  In the same way the openAIRE's organizations are grouped. 
>  **Note**:
> - The 50% of the organizations in the openAIRE’s database lie in the category _Rest_.
> - More than 80% of Crossref's affiliations lie in the categories _Universities/Institutes_ and _Laboratories_.
> We focus on these cases and filter the openAIRE organizations to those that are __not__ under the _Rest_ label. This reduces significantly the dataset we need to search.

2. In the next phase the goal is to __shorten the strings__: the average length of a string of an affiliation is ~90  and this string often contains unnecessary details. See for example the affiliations A1 (length 189), A2 (length 395), A3 (length 80) above. 
The task now is to __extract only the essential information__ from each affiliation string.
For this first the algorithms splits the string whenever a , or ; is found and applies certain ‘association rules’ to these substrings, then keeps only the substrings that contain ‘keywords’, and finally cuts even more the strings when necessary, by keeping only the words close to certain keywords like ‘university’, ‘institute’, or 'hospital'.  
After this procedure the average length is reduced to ~35 (for example, the affiliation A1 becomes `"research epidemiology statistics universit paris cite"` with length 53, while A2 is split to `["graduate school medicine","universit tokyo","chiba universit graduate school"` with lengths 24, 15, 31 respectively, and finally A3 becomes `"universit california`" with length 20).

4. Now the algorithm __checks__ whether a substring, that has a keyword, is __contained__ to (or __contains__) a legal name/alternative name of an organization in the openAIRE database and if so, it applies __cosine similarity__ to find which is the best match. 
After several experiments the threshold for strings containing ‘universit’ is set to 0.7 while for all others is set to 0.82.

5. Final step. It is possible that several matchings are found whose similarity scores are above the thresholds. 
In this case, another check is essential for the effectiveness of the method: the algorithm applies again cosine similarity between the organizations found in the openAIRE database on the one hand, and on the other hand the __original affiliation__ from which the substring containing the keyword was obtained. The idea behind this is that the original affiliations contain information like addresses or city names that can help decide which one from the openAIRE's organizations is the best fit. For example, `"universit california"` is matched to 40 organizations from openAIRE's database. In this second round, the original A3 string is considered, where the information `"San Diego"` helps the algorithm decide to finally match this affiliation to `"universit california san diego"`.


## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

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


## Description of the algorithm -- examples

__Goal__: Recognize openAIRE's organizations inside the Crossref's data and match to each DOI the corresponding ROR ids.

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


__Steps:__

1. After __importing__, __cleaning__, __tokenizing__ the affiliations’ strings and __removing stopwords__, the algorithm __categorizes the affiliations__ based on the frequency of words appearing in the legal names of openAIRE's organizations (a preparatory work with the openAIRE's data has already been carried out. The categories are _Univisties/Instirutions_, _Laboratories_, _Hospitals_, _Companies_, _Museums_, _Governments_, and _Rest_). For example, the affiliations:

* A1. `"Obstetrical Perinatal and Pediatric Epidemiology Research Team Institute of Health and Medical Research Centre of Research in Epidemiology and Statistics Université Paris Cité  Paris France"`

* A2. `"From the Department of Cardiovascular Science and Medicine, Chiba University Graduate School of Medicine, Chiba, Japan (M.A., H.T., T.N., H.H., T.S., Y.M., I.K.); the Department of Cardiovascular Medicine, Graduate School of Medicine, University of Tokyo, Tokyo, Japan (H.U.); and the Department of Metabolic Diseases, Graduate School of Medicine, University of Tokyo, Tokyo, Japan (N.K., T.K.)."`

* A3. `"Department of Biology, University of California, San Diego, La Jolla 92093-0063."`

  lie in the _Univisties/Instirutions_ category, while

* A4 `"Laboratoire Central dImmunologie dHistocompatibilite, INSERM U93, Paris, France"` lies in the _Laboratories_ category

  and the 

* A5 `"advancecsg lisbon portugal"` is in the _Rest_. 

  In the same way the openAIRE's organizations are grouped. 
>  **Note:**
> - The 50% of the organizations in the openAIRE’s database lie in the category _Rest_.
> - More than 80% of Crossref's affiliations lie in the categories _Universities/Institutes_ and _Laboratories_.
>
>   We focus on these cases and filter the openAIRE organizations to those that are __not__ under the _Rest_ label. This reduces significantly the dataset we need to search.

2. In the next phase the goal is to __shorten the strings__: the average length of a string of an affiliation is ~90  and this string often contains unnecessary details. See for example the affiliations A1 (length 189), A2 (length 395), A3 (length 80) above. 
The task now is to __extract only the essential information__ from each affiliation string.
For this, the algorithms first splits the string whenever a , or ; is found and applies certain ‘association rules’ to these substrings, then keeps only the substrings that contain ‘keywords’, and finally cuts even more the strings when necessary, by keeping only the words close to certain keywords like ‘university’, ‘institute’, or 'hospital'.  
After this procedure the average length is reduced to ~35 (for example, the affiliation A1 becomes `"research epidemiology statistics universit paris cite"` with length 53, while A2 is split to `["graduate school medicine","universit tokyo","chiba universit graduate school"` with lengths 24, 15, 31 respectively, and finally A3 becomes `"universit california`" with length 20).

4. Now the algorithm __checks__ whether a substring, that has a keyword, is __contained__ to (or __contains__) a legal name/alternative name of an organization in the openAIRE database and if so, it applies __cosine similarity__ to find which is the best match. 
After several experiments the threshold for strings containing ‘universit’ is set to 0.7 while for all others is set to 0.82.

5. Final step. It is possible that several matchings are found whose similarity scores are above the thresholds. 
In this case, another check is essential for the effectiveness of the method: the algorithm applies again cosine similarity between the organizations found in the openAIRE database on the one hand, and on the other hand the __original affiliation__ from which the substring containing the keyword was obtained. The idea behind this is that the original affiliations contain information like addresses or city names that can help decide which one from the openAIRE's organizations is the best fit. For example, `"universit california"` is matched to 40 organizations from openAIRE's database. In this second round, the original A3 string is considered, where the information `"San Diego"` helps the algorithm decide to finally match this affiliation to `"universit california san diego"`.


## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

