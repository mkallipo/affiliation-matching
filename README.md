# Affiliation-Matching Repository \[aka AffRo\]

This repository contains code for matching affiliation strings to ROR IDs.

🚀 As it is destined to always be a work in progress, *the repository may not always be up-to-date*. 
However, I will incorporate improvements and bug fixes regularly. 

## Main files


-  `helpers/create_input.py`, `helpers/matching.py`,  `helpers/disambiguation.py` contain the main algorithm.



## Testing / Usage
- **Command-line usage:**  
  ```bash
  python core.py "your affiliation here"


## Description of the algorithm

### Goal: Identify organizations inside a raw affiliation string and match the corresponding ROR ids.

### Steps:

- **Preprocessing phase:** 
1. Cleaning and stemming
2. Keyword labeling and partitioning
3. Partition pruning and string shortening
- **Matching phase:**
1. Candidate identification and refinement
2. Results disambiguation

### Basic parameters:
1. Threshold for university related organizations (default 0.42).
2. Threshold for other organizations (default 0.82).
3. Context window for trimming text around the term "university" (default 3)

## Versions
The TPDL version of the algorithm can be found here: [GitHub Tags](https://github.com/mkallipo/affiliation-matching/tags)

## Contact

If you have any questions, comments, or issues, please feel free to contact me. You can reach me via email at [myrto.kallipoliti@gmail.com]. Feedback and contributions are also welcome.

