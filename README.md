# Matching Repository

This repository contains code and data for matching DOIs of crossref JSON files with organization IDs from the OpenAIRE database.

## Files

- `matching.py`: This is the main code for the matching process. It takes JSON files as input and returns a JSON (`output.json`) with matchings between the DOIs of the JSONs and IDs of organizations in the OpenAIRE database. 
The organizations include universities, institutions, hospitals, labs.

- `matching.ipynb`: Is a Jupyter Notebook for testing the code. In addition to the JSON file (`output.json`) it returns two EXCEL files (`affilMatch` and `doisMatch` respectively), one with the distinct affiliations of the JSON input, the matched openAIRE organizations and the corresponding similarity scores and one with the DOIs of the JSON input and the matched openAIRE organizations and the similarity scores.

- `dixOpenAIRE_Alletc.pkl`: This file is a pickled dictionary that contains keys representing legalnames and alternativenames of organizations in the OpenAIRE database. 
The corresponding values are the PIDs (Persistent Identifiers) associated with each organization.

- `dixOpenAIRE_id.pkl`: This file is another pickled dictionary that maps legalnames and alternativenames of organizations in the OpenAIRE database to their corresponding OpenAIRE IDs.

- `dixOpenOrgId.pkl`: This file is one more pickled dictionary that maps legalnames and alternativenames of organizations in the OpenAIRE database to their corresponding OpenAIRE IDs and the prefix of the organizations is openorgs_.

- `sample.json`: Is a sample of 1000 DOIs obtained from 300 json files from the Crossref database, which can be used for testing and validation purposes.
  
- `output.json`: The output for the `sample.json` file.

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


## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

