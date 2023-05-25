# Matching Repository

This repository contains code and data for matching DOIs of crossref JSON files with organization IDs from the OpenAIRE database.

## Files

- `matching.ipynb`: This Jupyter Notebook contains the main code for the matching process. It takes JSON files as input and returns JSON with matchings between the DOIs of the JSONs and IDs of organizations in the OpenAIRE database. 
The organizations include universities, institutions, hospitals, labs, etc.

- `dixOpenAIRE_Alletc.pkl`: This file is a pickled dictionary that contains keys representing legalnames and alternativenames of organizations in the OpenAIRE database. 
The corresponding values are the PIDs (Persistent Identifiers) associated with each organization.

- `dixOpenAIRE_id.pkl`: This file is another pickled dictionary that maps legalnames and alternativenames of organizations in the OpenAIRE database to their corresponding OpenAIRE IDs.

- `dixOpenOrgId.pkl`: This file is one more pickled dictionary that maps legalnames and alternativenames of organizations in the OpenAIRE database to their corresponding OpenAIRE IDs and the prefix of the organizations is openorgs_.

- `Archive.zip`: This ZIP file contains a `0.json` and `42.json` from the Crossref database, which can be used for testing and validation purposes.
- 'match0.json': The output for the '0.json' file.

## Dependencies

Make sure you have the following dependencies installed before running the code:

- pandas
- re
- pickle
- scikit-learn (for `CountVectorizer` and `cosine_similarity`)
- Levenshtein
- plotly and datapane (if you want to create an HTML file for reporting and sharing)

## Usage

1. Run the `matching.ipynb` notebook in a Jupyter environment. Make sure to provide the JSON files that you want to match as input.

2. The notebook will process the input JSON files and generate a JSON file with the matchings between DOIs and organization IDs from the OpenAIRE database.

3. You can access the generated matchings JSON file and use it for further analysis or any other required tasks.

## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

