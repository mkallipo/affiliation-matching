# Matching Repository

This repository contains code and data for matching DOIs of crossref JSON files with organization IDs from the OpenAIRE database.

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

- `description.txt`: Is a description of the main code.


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

__Goal__: Recognize openAIREs organizations having a openAIRE inside the crossref affiliations data and match the corresponding ROR ids.

__Input__: A JSON file from Crossref's data.


__Output__: A JSON file containing DOIs from Crossref data and their matchings to openAIRE's organization and the corresponding confidence scores, for example: `{"DOI":"10.1061\/(asce)0733-9399(2002)128:7(759)","Matchings":[{"RORid":["https:\/\/ror.org\/01teme464"],"Confidence":0.73},{"RORid":["https:\/\/ror.org\/03yxnpp24"],"Confidence":0.7071067812}]}`.


__Steps:__

1. After importing, cleaning, tokenizing the affiliations’ strings and removing certain stopwords, the algorithm categorizes the affiliations based on the frequency of words appearing in the legal names of openAIREs organizations (a preparatory work with the openAIREs data has already been carried out. The categories are Univisties/Instirutions, Laboratories, Hospitals, Companies, Museums, Governments, and Rest). For example, the affiliations:

* A1. `"Obstetrical Perinatal Pediatric Epidemiology Research Team Institute Health Medical Research Centre Research Epidemiology     Statistics Universite Paris Cite Paris France"`

* A2. `"From Department Cardiovascular Science Medicine, Chiba University Graduate School Medicine, Chiba, Japan Department Cardiovascular Medicine, Graduate School Medicine, University Tokyo, Tokyo, Japan Department Metabolic Diseases, Graduate School Medicine, University Tokyo, Tokyo, Japan"`

* A3. `"Department Biology, University California, San Diego, La Jolla 920930063"`

  lie in the _Univisties/Instirutions_ category, while

* A4 `"Laboratoire Central dImmunologie dHistocompatibilite, INSERM U93, Paris, France"` lies in the _Laboratories_ category

  and the 

* A5 `"advancecsg lisbon portugal"` is in the _Rest_. 

  In the same way the openAIREs organizations are grouped. 

  __Facts__:  > * The 40% of the organizations in the openAIRE’s database lie in the categories ‘Rest’.   
              > * More than 80% of the affiliations in the openAIRE’s database lie in the categories ‘Universities/Institutes’ and ‘Laboratories’

  We focus on these cases and filter the openAIRE orgs to those that are under the ‘Rest’ label. In this way we reduce by 40% the data in which we search to find the matchings.

2. In the next phase the goal is to shorten the strings: the average length of a string is ~84  and often contain unnecessary details. See for example the affiliations A1 (length 167), A2 (length 286), A3 (length 72) above. 
The task now is to extract only the essential information from each affiliation string. 
This is be done by splitting the string whenever a , or ; is found, then apply certain ‘association rules’ to these substrings, then keep only the substrings that contain ‘keywords’, and finally cut even more the strings when necessary, by keeping only the words close to certain keywords like ‘university’, ‘institute’, or 'hospital' etc.  

  After this procedure the average length is reduced to ~32 (the affiliation A1 becomes `"research epidemiology statistics universit     paris cite"` with length 53, 
  while A2 is split to `["graduate school medicine","universit tokyo","chiba universit graduate school"` (of lengths 24, 15, 31 respectively, and finally A3 becomes `"univerit california`" (length 20)

4. Then the algorithm checks whether a substring that contains a keyword is contained to (or contains one) legal name/alternative name of an organization in the openAIRE database and if so, it applies cosine similarity to find which is the best match. 
After several experiments the threshold for organizations contain the substring ‘universit’ is set to 0.7 while for all others is set to 0.82.

5. Final step. It is possible that several matches are found whose similarity scores are above the thresholds. 
In this case, another check is essential for the effectiveness of the method: the algorithm applies again cosine similarity between the organizations found in the openAIRE database on the one hand, and on the other hand the original affiliation from which the substring containing the keyword was obtained. The idea behind this is that the original affiliation contain information like addresses or city names that can help decide which one from the openAIREs organizations is the best fit. For example, ‘universit California’ is matched to 40 organizations from openAIREs database. In the second round, the original A3 string is considered, where the information _San Diego_ helps the algorithm decide to finally match this affiliation to `"universit california san diego"`.


## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

