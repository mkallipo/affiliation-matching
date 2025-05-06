# Affiliation-Matching Repository \[aka AffRo\]

This repository contains code for matching DOIs of Crossref / Pubmed / DataCite data with organization IDs from the ROR (https://ror.org) database.

🚀 As it is still a work in progress, *the repository may not always be up-to-date*. 
However, I will incorporate improvements and bug fixes regularly. 

## Main files


-  `create_input.py`, `matching.py`, contain the main algorithm (preprocessing and matching phase, respectively).



##  Testing


## Description of the algorithm

### Goal: Identify organizations inside a raw affiliation string and match the corresponding ROR ids.

### Steps:

1. **Data Preprocessing:** The affiliations' strings are imported and undergo cleaning, tokenization.
2. **Categorization:** Data preprocessing has already been conducted on ROR's data, involving the analysis of word frequency ('keywords') within the legal names of ROR's organizations to define specific categories. 
4. **Filtering:** to be added
5. **String Shortening:** The objective is to extract pertinent details from each affiliation string. The algorithm divides the string whenever a comma (,) or semicolon (;) is detected. It then applies specific 'rules' to these segments and retains only those containing relevant keywords. Additionally, it trims down the segments by preserving words in proximity to particular keywords like "university," "institute," "laboratory," or "hospital." As a result, the average string length is reduced from 90 to 35 characters.
6. **Matching with ROR's Database:** The algorithm checks whether a substring containing a keyword is linked to a legal name or to an alternative name in the organizations listed in the ROR's database. In order to identify the most accurate match, the algorithm employs cosine similarity. For strings containing "universi," a similarity threshold of 0.64 is employed, while for all other keywords, the threshold is set at 0.87. Although alternative methods like Levenshtein Distance or Jaro-Winkler Distance were considered for measuring string similarity, it was concluded that cosine similarity was the most appropriate choice for this specific application.
7. **Refinement:** If multiple matches are found above the similarity thresholds, the algorithm performs another check. It applies cosine similarity between the organizations found in the ROR's database and the original affiliation string. This comparison takes into account additional information present in the original affiliation, such as addresses or city names. The algorithm aims to identify the best fit among the potential matches. Note that the case where two or more different organizations share the same name is also considered.



## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

