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


## Description of the algorithm -- examples. 

__Goal__: Recognize openAIRE's organizations inside the Crossref's data and match the corresponding ROR ids.

__Input__: A JSON file from Crossref's data.


__Output__: A JSON file containing DOIs from Crossref's data and their matchings to openAIRE's organizations and the corresponding confidence scores, for example: 
>`{"DOI":"10.1061\/(asce)0733-9399(2002)128:7(759)","Matchings":[{"RORid":["https:\/\/ror.org\/01teme464"],"Confidence":0.73},{"RORid":["https:\/\/ror.org\/03yxnpp24"],"Confidence":0.7071067812}]}`.


__Steps:__

1. After __importing__, __cleaning__, __tokenizing__ the affiliations’ strings and __removing stopwords__, the algorithm __categorizes the affiliations__ based on the frequency of words appearing in the legal names of openAIREs organizations (a preparatory work with the openAIREs data has already been carried out. The categories are _Univisties/Instirutions_, _Laboratories_, _Hospitals_, _Companies_, _Museums_, _Governments_, and _Rest_). For example, the affiliations:

* A1. `"Obstetrical Perinatal Pediatric Epidemiology Research Team Institute Health Medical Research Centre Research Epidemiology     Statistics Universite Paris Cite Paris France"`

* A2. `"From Department Cardiovascular Science Medicine, Chiba University Graduate School Medicine, Chiba, Japan Department Cardiovascular Medicine, Graduate School Medicine, University Tokyo, Tokyo, Japan Department Metabolic Diseases, Graduate School Medicine, University Tokyo, Tokyo, Japan"`

* A3. `"Department Biology, University California, San Diego, La Jolla 920930063"`

  lie in the _Univisties/Instirutions_ category, while

* A4 `"Laboratoire Central dImmunologie dHistocompatibilite, INSERM U93, Paris, France"` lies in the _Laboratories_ category

  and the 

* A5 `"advancecsg lisbon portugal"` is in the _Rest_. 

  In the same way the openAIREs organizations are grouped. 
> #### Facts:
> - The 50% of the organizations in the openAIRE’s database lie in the category _Rest_.
> - More than 80% of Crossref's affiliations lie in the categories _Universities/Institutes_ and _Laboratories_.

- **Note:** We focus on these cases and filter the openAIRE organizations to those that are __not__ under the _Rest_ label. This reduces significantly the dataset we need to search.

2. In the next phase the goal is to __shorten the strings__: the average length of a string of an affiliation is ~85  and often contains unnecessary details. See for example the affiliations A1 (length 167), A2 (length 286), A3 (length 72) above. 
The task now is to __extract only the essential information__ from each affiliation string. 
This is done by splitting the string whenever a , or ; is found, then apply certain ‘association rules’ to these substrings, then keep only the substrings that contain ‘keywords’, and finally cut even more the strings when necessary, by keeping only the words close to certain keywords like ‘university’, ‘institute’, or 'hospital'.  
After this procedure the average length is reduced to ~35 (for example, the affiliation A1 becomes `"research epidemiology statistics universit paris cite"` with length 53, while A2 is split to `["graduate school medicine","universit tokyo","chiba universit graduate school"` with lengths 24, 15, 31 respectively, and finally A3 becomes `"universit california`" with length 20).

4. Now the algorithm __checks__ whether a substring, that has a keyword, is __contained__ to (or __contains__) a legal name/alternative name of an organization in the openAIRE database and if so, it applies __cosine similarity__ to find which is the best match. 
After several experiments the threshold for strings containing ‘universit’ is set to 0.7 while for all others is set to 0.82.

5. Final step. It is possible that several matchings are found whose similarity scores are above the thresholds. 
In this case, another check is essential for the effectiveness of the method: the algorithm applies again cosine similarity between the organizations found in the openAIRE database on the one hand, and on the other hand the __original affiliation__ from which the substring containing the keyword was obtained. The idea behind this is that the original affiliations contain information like addresses or city names that can help decide which one from the openAIREs organizations is the best fit. For example, `"universit california"` is matched to 40 organizations from openAIREs database. In this second round, the original A3 string is considered, where the information `"San Diego"` helps the algorithm decide to finally match this affiliation to `"universit california san diego"`.


## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

