# Affiliation-Matching Repository \[aka AffRo\]

This repository contains code for matching DOIs of Crossref / Pubmed / DataCite data with organization IDs from the ROR (https://ror.org) database.

🚀 As it is still a work in progress, *the repository may not always be up-to-date*. 
However, I will incorporate improvements and bug fixes regularly. 

## Main files

- `crossref.py`, `pubmed.py`, `datacite.py` are python scripts, designed to meet the unique needs of the corresponding data source.

- `main_functions.py` contains the main algorithm.

- `dictionaries/dix_acad.pkl`: This file is a pickled dictionary with keys legalnames and alternativenames of organizations in the ROR database. The corresponding values are the ROR ids associated with each organization.

- `dictionaries/dix_mult`, `dictionaries/dix_city`, `dictionaries/dix_country`: three more pickled dictionary with keys legalnames and alternativenames of organizations in the ROR database, necessary in the case where different organizations share the same name.
  



- `requirements.txt`.


##  Testing

If you want to match a single affiliation string, run the `find_ror.ipynb` notebook  of the _testing_ folder by providing the string and two thresholds, simU (for Universities) and simG (for other institutions). 

Example: `find_ror('university of athens', 0.8, 0.4) = [{'ROR_ID': 'https://ror.org/04gnjpq42', 'Score': 1}]`.

In the same folder you will find `testing/sample.json`, which is a sample of 1000 DOIs obtained from 300 json files from the Crossref database. Run the `testing/crossref.ipynb` notebook. It will produce the files `testing/dois_match.json`, `testing/affs_match.csv` and `testing/dois_match.csv`.


## Description of the algorithm

### Goal: Identify organizations inside a raw affiliation string and match the corresponding ROR ids.

### Steps:

1. **Data Preprocessing:** The affiliations' strings are imported and undergo cleaning, tokenization, and removal of stopwords.
2. **Categorization:** Data preprocessing has already been conducted on ROR's data, involving the analysis of word frequency ('keywords') within the legal names of ROR's organizations to define specific categories. These categories include "Univ/Inst," "Laboratory," "Hospital," "Company," "Museum," "Government," "Foundation," and "Rest". ROR's organizations have subsequently been assigned to these categories based on their legal names. The algorithm employs a similar approach to categorize affiliations into these same groups.
4. **Filtering:** Almost 40\% of the organizations in the ROR’s database lie in the category "Rest". More than 80\% of Crossref's affiliations lie in the categories "Univ/Inst", "Laboratory", "Hospital", and "Foundation". At the moment the algorithm focuses on these cases and excludes the ROR's organizations labeled as "Rest". This reduces significantly the dataset we need to search.
5. **String Shortening:** The objective is to extract pertinent details from each affiliation string. The algorithm divides the string whenever a comma (,) or semicolon (;) is detected. It then applies specific 'rules' to these segments and retains only those containing relevant keywords. Additionally, it trims down the segments by preserving words in proximity to particular keywords like "university," "institute," "laboratory," or "hospital." As a result, the average string length is reduced from 90 to 35 characters.
6. **Matching with ROR's Database:** The algorithm checks whether a substring containing a keyword is linked to a legal name or to an alternative name in the organizations listed in the ROR's database. In order to identify the most accurate match, the algorithm employs cosine similarity. For strings containing "universi," a similarity threshold of 0.7 is employed, while for all other keywords, the threshold is set at 0.82. Although alternative methods like Levenshtein Distance or Jaro-Winkler Distance were considered for measuring string similarity, it was concluded that cosine similarity was the most appropriate choice for this specific application.
7. **Refinement:** If multiple matches are found above the similarity thresholds, the algorithm performs another check. It applies cosine similarity between the organizations found in the ROR's database and the original affiliation string. This comparison takes into account additional information present in the original affiliation, such as addresses or city names. The algorithm aims to identify the best fit among the potential matches. Note that the case where two or more different organizations share the same name is also considered.



## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

