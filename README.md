# `run_affro` — Affiliation Matching Pipeline Documentation

**Version:** 3.3.4  
**Module:** `core.py`  
**Entry point:** `run_affro(aff: str) → list[dict]`

---

## Overview

`run_affro` is the main entry point of the **affro** affiliation-matching pipeline. It takes a raw affiliation string (as it appears in a publication metadata record) and returns a list of matched organisations with their identifiers (ROR and/or OpenOrgs), confidence scores, and status information.

```python
from core import run_affro

results = run_affro("Department of Physics, University of Milan, Italy")
```

---

## High-Level Pipeline

```
raw affiliation string
        │
        ▼
 direct_mapping()          ← fast rule-based lookup for known institute families
        │
        ├─ match found ──► run_affro_(shortened_aff)  +  direct results
        │
        └─ no match ─────► run_affro_(raw_aff)
                                │
                                ▼
                        normalise & stem
                                │
                         dix_name lookup   ← exact key lookup
                                │
              ┌─────────────────┼────────────────────┐
              │                                      │
        single match                          multiple matches
              │                                      │
              ▼                                      ▼
    build_result_list()     ◀---- filter by 'first'/'top_level'/'parent'
      (algorithm path)                  
                                                     │
                                              still ambiguous?
                                                     │
                                                     ▼
                                            (algorithm fallback)
```

---

## Stage 1 — `direct_mapping(aff)`

**File:** `helpers/direct_mapping.py`

A fast, rule-based pre-processor that recognises affiliation strings belonging to specific **institute families** (Fraunhofer, CNR, Max Planck, Helmholtz, Leibniz, FORTH, Demokritos, IRCCS, …).

### What it does

1. Produce a normalized, stemmed version of the raw string.
2. Checks for the presence of family-specific keywords (e.g. `fraunhofer`, `cnr`, `max planck`).
3. For each recognized family, iterates over pre-built sorted key lists (longest keys first for specificity) and checks whether the key appears close enough to the trigger word using a character-distance heuristic:
   ```
   distance(aff, trigger_word, key) < len(key) + len(trigger_word) + threshold
   ```
4. When a key matches, appends its ROR/OpenOrgs ID to `assigned` and removes the matched substring from the affiliation string (producing `shorten_aff`).

### Returns

```python
[list_of_direct_results, shortened_aff_string]
# list_of_direct_results: [] if nothing was matched, otherwise list of result dicts
# shortened_aff_string:   original affiliation with matched parts stripped out
```

The result dicts from direct mapping use `provenance = "affro_direct"`.


## Stage 2 — `run_affro_(raw_aff_string)`

**File:** `core_fast.py`

The core matching logic, applied after (or instead of) `direct_mapping`.

### Step 2.1 — `clean_string_lucky(raw_aff_string)`

**File:** `helpers/functions.py`

A lightweight, fast normalization pass that produces a single flat string key used for `dix_name` lookup. It does **not** segment the affiliation — that is left for the algorithm path.

**Main transformations applied (in order):**

| Step | Transformation |
|---|---|
| 1 | `unidecode` (remove accents / transliterate) |
| 2 | `process_parentheses` (keep parens with univ/hospital; drop others) |
| 3 | `replace_comma_spaces`, `replace_double_consonants`, `replace_underscore` |
| 4 | Lowercase, `replace_roman_numerals`, `remove_stop_words` |
| 5 | Remove non-alphanumeric except `,;/:.−` |
| 6 | `remove_multi_digit_numbers` |
| 7 | Replace `:`, `;`, `-`, `—`, `,` → single space |
| 8 | `normalize_organization_names` (stem `university*` → `univer`, `institution*` → `instit`, etc.) |

**Returns:** a single normalised string, e.g.:  
`"univer milan italy"` for input `"University of Milan, Italy"`

### Step 2.2 — `dix_name` lookup

`dix_name` is a dictionary loaded from `jsons/dix_name.json.gz`.  

**Structure:**
```json
{
  "instit information science techn": [
    {
      "id": "https://ror.org/05kacka20",
	  "city": ["pisa"],
	  "country": ["italy"],
	  "label": "cnr",
	  "first": "y"
    },
    ...
  ]
}
```


---

## Algorithm Path — `produce_result(input, simU, simG, limit)`

Used when the fast path fails. Called with `simU=0.42`, `simG=0.82`, `limit=500`.

### `create_df_algorithm(raw_aff_string, radius_u)` — `helpers/create_input.py`

Segments and enriches the affiliation string into a structured input representation.

**Steps:**

1. `clean_string()` — full normalisation (includes `insert_space_between_lower_and_upper`, `replace_newlines_with_space`, `replace_double_consonants`, etc.)
2. `remove_outer_parentheses`, `remove_leading_numbers`
3. `description(clean_aff)` → detects countries present in the string
4. `substrings_dict(reduce(clean_aff))` — segments the affiliation on `,;/:|` and `-` and applies `normalize_organization_names` to each segment
5. `replace_abbr_univ` — expands abbreviations like `"u Milan"` → `"univer Milan"`
6. Merges protected terms (e.g. `"univer california"`) with adjacent city/country tokens
7. Removes city-only or remove-list tokens
8. `shorten_keywords([x], radius_u)` — further reduces keywords
9. `valueToCategory(keyword)` — classifies each keyword (Academia, Hospitals, Specific, …)

**Returns:**
```python
[clean_aff, light_aff, aff_list, countries_list, keys_list]
# clean_aff:      normalised full string
# light_aff:      comma-joined list of segments
# aff_list:       list of {index, keywords, category} dicts
# countries_list: detected country names
# keys_list:      special category keys found
```

### `find_name(input, dix_name, simU, simG, limit)` — `helpers/find_name.py`

Matches each keyword segment against `dix_name` candidates, using similarity scoring.

**Steps:**

1. `get_candidates(countries_list, keys_list)` → restricts the search space by country and special category keys (intersection of `dix_country_legalnames` and `dix_key_legalnames`).
2. For each keyword `s`:
   - If `s` is directly in `candidates` → exact "lucky" match (score = 1).
   - Otherwise → `find_candidate(s, ...)` applies cosine similarity / edit-distance scoring against candidates, bounded by `simU` (universities) or `simG` (others).
3. `index_multiple_matchings(pairs)` detects keywords matched by >1 candidate.
4. `best_sim_score(...)` resolves multi-matched keywords using the full clean/light affiliation string.
5. `unique_subset(best0, best1)` de-duplicates.

**Returns:** `[[name, score], ...]`

### `find_id(aff_input, best_names, dix_name, simG)` — `helpers/find_id.py`

Resolves each matched name to a specific organisation ID, disambiguating when a name maps to multiple organisations in different countries/cities.

**Disambiguation cascade (in order):**

| Step | Strategy |
|---|---|
| 1 | City **and** Country match |
| 2 | Country direct match |
| 3 | Special country synonyms (US states, UK variants,…) |
| 4 | City match (city not embedded in org name) |
| 5 | Country appears in affiliation |
| 6 | Country appears in both affiliation and org name |
| 7 | Specific/Acronym category → prefer `top_level`, then `parent` |
| 8 | Fallback: `first == 'y'` for non-department, non-lab, non-low-prob-country orgs |

**Returns:** `[[name, score, id], ...]` (deduplicated, highest score per ID kept)

### `disamb(input, id_list_, dix_id)` — `helpers/disambiguation.py`

Final post-processing to resolve cases where multiple organisations were matched.

**Logic:**

| Condition | Action |
|---|---|
| Single result | Return as-is |
| No country detected in affiliation | Keep same-country results (excluding low-probability countries) |
| More active results than detected countries | Filter by country (with special handling for US, UK, Korea) |
| Otherwise | Return all results |

**Returns:** Full result list (see Output Schema below).

---

## Output Schema

Each item in the returned list is a dictionary:

| Field | Type | Description |
|---|---|---|
| `provenance` | `str` | `"affro"` (algorithm path) or `"affro_direct"` (direct mapping) |
| `version` | `str` / `int` | Pipeline version (`"3.3.4"` for affro, `1` for direct) |
| `pid` | `str` | `"ror"` or `"openorgs"` |
| `value` | `str` | The organisation identifier (ROR URI or OpenOrgs ID) |
| `name` | `str` | Official organisation name |
| `confidence` | `float` | Match confidence score (0–1). Always `1` on the fast path. |
| `status` | `str` | `"active"`, `"inactive"`, `"withdrawn"`, or `"merged"` |
| `country` | `list[str]` | Country or countries associated with the organisation |

**Example output:**
```json
[
  {
    "provenance": "affro",
    "version": "3.3.4",
    "pid": "ror",
    "value": "https://ror.org/00wra1b14",
    "name": "University of Milan",
    "confidence": 1,
    "status": "active",
    "country": ["italy"]
  }
]
```

> [!NOTE]
> When an organisation is inactive/withdrawn, affro also appends the active successor(s) from `dix_id[id]['status'][1]` as separate entries in the list.

---

## Data Dictionaries

### `dix_name` — `jsons/dix_name.json.gz`

Maps **normalised name keys** to a list of candidate organisations. Each candidate has:

| Field | Type | Description |
|---|---|---|
| `id` | `str` | ROR URI or OpenOrgs ID |
| `first` | `str` | `"y"` if this is the canonical/primary org for this key |
| `label` | `str` \| `null` | Family label (e.g. `"fraunhofer"`, `"cnr"`) used by direct mapping |
| `country` | `list[str]` | Country names |
| `city` | `list[str]` | City names |

### `dix_id` — `jsons/dix_id.json.gz`

Maps **organisation IDs** to metadata:

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Official name |
| `country` | `list[str]` | Country |
| `status` | `list` | `[primary_status, [successor_ids]]` |
| `top_level` | `str` | `"y"` if the org has no parent |
| `parent` | `str` | `"y"` if the org is a parent to others |

---

## Usage

### Command-line

From the project root directory:

```bash
python3 -c "from affro.cores import run_affro; print(run_affro('university of athens'))"

```

### Expected behaviour by case

| Input | Fast path taken | Reason |
|---|---|---|
| `"University of Cambridge"` | `dix_name` exact match | `"univer cambridge"` found in `dix_name` |
| `"Fraunhofer, Institute for Industrial Engineering, Stuttgart"` | Direct mapping | `"fraunhofer"` + `"instit industrial engineering"` triggers `direct_mapping` |
| `"Dept. of Physics, Univ. of Auckland, NZ"` | Algorithm path | Lucky key not in `dix_name` |
| Inactive ROR org | Fast path + successor | Status list contains successor ID → appended to result |

---

## Error Handling

- Any exception inside `run_affro_` is caught, logged to stdout with the input string, and an empty list `[]` is returned.
- An empty result list `[]` indicates no match was found or an error occurred.

---

## Module Dependencies

```
core.py
├── helpers/functions.py          # string cleaning, dix_name/dix_id loading, regex, utils
├── helpers/create_input.py       # create_df_algorithm, valueToCategory, substrings_dict
├── helpers/matching.py           # find_candidate, get_candidates, best_sim_score, cosine similarity
├── helpers/find_name.py          # find_name
├── helpers/find_id.py            # find_id, disambiguation helpers
├── helpers/disambiguation.py     # disamb, convert_to_result
└── helpers/direct_mapping.py     # direct_mapping, _build_label_keys
```
