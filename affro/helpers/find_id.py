from affro.helpers.functions import *
from affro.helpers.create_input import *

low_confidence_ids = {'https://ror.org/003agka18', 'https://ror.org/00wra1b14','https://ror.org/05fe6f045',
               'https://ror.org/05pz81c75', 'https://ror.org/05q882j59', 'https://ror.org/00tpdkh38',
               'https://ror.org/04fnhr972','https://ror.org/04155gf20', 'https://ror.org/0243vac68', 'https://ror.org/00p61c264',
               'https://ror.org/01p2ej961','https://ror.org/04vwgk321','https://ror.org/01pc4rp54','https://ror.org/034ymz395',
               'https://ror.org/018xp1p31', 'https://ror.org/042tmw509', 'https://ror.org/035qa0k76','https://ror.org/009ytmf35', 
               'https://ror.org/048gmay44', 'https://ror.org/04wvz8b06', 'https://ror.org/01rk3xf02', 'https://ror.org/03gbw6p94', 'https://ror.org/02jjdwm75',
               'https://ror.org/05byh2e17', 'https://ror.org/02eaafc18'}


specific = set(k for k in categ_dicts if categ_dicts[k] in {'Specific', 'Acronyms'})

special_countries = {k for k, v in country_synonyms.items() if len(v) > 1}

excluded = {'univ', 'inst', 'national', 'nacional', 'colege', 'center', 'organization', 'hospital'}

    
    
def keep_highest_score(data):
    """
    Keeps only one entry per unique ID.
    Keeps the one with highest confidence score.
    """
    best = {}

    for org, conf, id_ in data:
        if id_ not in best or conf > best[id_][1]:
            best[id_] = [org, conf, id_]

    return list(best.values())


def _match_special_country(country_list, text, tokens):
    """
    Check if any special-country synonym appears in the affiliation text.
    Safer token-based matching.
    """
    country_syns = {
        synonym
        for country in country_list
        for synonym in country_synonyms.get(country, [country])
    }

    # Strict token match first
    if country_syns & tokens:
        return True

    # Controlled substring match (avoid very short tokens like 'us')
    for syn in country_syns:
        if len(syn) > 3 and re.search(r'\b' + re.escape(syn) + r'\b', text):
            return True

    return False


def disamb_country(org, light_aff):
    ids = []

    for rec in dix_name[org]:
        country_list = rec['country']
        if any(c in light_aff for c in country_list) and \
           not any(c in org for c in country_list):
            ids.append(rec['id'])

    return ids


def disamb_city(org, light_aff):
    ids = []

    for rec in dix_name[org]:
        city_list = rec['city']
        if any(c in light_aff for c in city_list) and \
           not any(c in org for c in city_list):
            ids.append(rec['id'])

    return ids


def disamb_city_country(org, light_aff):
    city_ids = set(disamb_city(org, light_aff))
    country_ids = set(disamb_country(org, light_aff))
    return list(city_ids & country_ids)


def find_id(aff_input, best_names, dix_name, simG):
    clean_aff = aff_input[0]
    # print('find_id')
    # print(clean_aff)
    light_aff = aff_input[1]
    # print(best_names)
    id_list = []

    clean_aff_tokens = {x.replace(',', '') for x in clean_aff.split()}
    light_aff_tokens = {x.strip(',;.:()') for x in light_aff.split()}
    for org_list in best_names:
        

        org = org_list[0]
        conf = org_list[1]

        records = dix_name[org]
        
        # -------------------------------------------------
        # SINGLE MATCH CASE
        # -------------------------------------------------
        if len(records) == 1:
            # print('Single match for:', org)
            rec = records[0]
            id_ = rec['id']
            city_list = rec['city']
            country_list = rec['country']
            if id_ in low_confidence_ids and conf < simG:
                # print('problem')
                continue
                
            country_set = {
                synonym
                for country in country_list
                for synonym in country_synonyms.get(country, [country])
            }

            # print('light_aff',light_aff)
            if org in light_aff or org in light_aff.split(','):
                # print('Exact match for:', org)
                id_list.append([org, conf, id_])

            elif (
                not any(city in light_aff for city in city_list)
                and not country_set & light_aff_tokens
                and not any(word in org for word in excluded)
                and valueToCategory(org)[1] not in {'Company', 'Acronyms', 'Specific'}
            ):
                # print('No city/country match but no exclusion words for:', org)
                pass

            else:
                id_list.append([org, conf, id_])

        # -------------------------------------------------
        # MULTIPLE MATCH CASE
        # -------------------------------------------------
        else:
            # print('Multiple matches for:', org)
            match_found = False

            # Precompute country universe once
            countries_ids = {
                country
                for rec in records
                for country in rec['country']
            }

            # -------------------------------
            # STEP 1: City + Country
            # -------------------------------
            disamb = disamb_city_country(org, light_aff)

            if len(disamb) == 1:
                # print('STEP 1: City + Country disambiguation')
                id_list.append([org, conf, disamb[0]])
                continue

            # -------------------------------
            # STEP 2: Country direct match
            # -------------------------------
            for rec in records:
                country_list = rec['country']
                id_ = rec['id']

                if any(c in light_aff for c in country_list) and \
                   not any(c in org for c in country_list):

                    id_list.append([org, conf, id_])
                    match_found = True
                    # print('STEP 2: Country direct match')
                    break

            # -------------------------------
            # STEP 3: Special country synonyms
            # -------------------------------
            if not match_found and countries_ids & special_countries:

                for rec in records:
                    if _match_special_country(
                        rec['country'],
                        clean_aff,
                        clean_aff_tokens
                    ):
                        id_list.append([org, conf, rec['id']])
                        match_found = True
                        # print('STEP 3: Special country synonym match')
                        break

            # -------------------------------
            # STEP 4: City match
            # -------------------------------
            if not match_found:
                # print('STEP 4: City match')
                for rec in records:
                    city_list = rec['city']
                    id_ = rec['id']

                    if any(c in clean_aff for c in city_list):
                        # print('city')
                        if not any(city in org for city in city_list):
                            id_list.append([org, conf, id_])
                            match_found = True
                            # print('STEP 4: City match without city in org')
                            break

                        elif any(clean_aff.count(city) > 1 for city in city_list):
                            id_list.append([org, conf, id_])
                            match_found = True
                            # print('STEP 4: City match with multiple city mentions')
                            break

            # -------------------------------
            # STEP 5: First word of country
            # -------------------------------
            if not match_found:
                # print('STEP 5: First word of country')
                for rec in records:
                    for country in rec['country']:
                        if country.split()[0] in clean_aff and \
                           not any(c in org for c in rec['country']):

                            id_list.append([org, conf, rec['id']])
                            match_found = True
                            # print('STEP 5: First word of country match')
                            break
                    if match_found:
                        break

            # -------------------------------
            # STEP 6: Country appears in both
            # -------------------------------
            if not match_found:

                for rec in records:
                    if any(c in clean_aff.split() for c in rec['country']) and \
                       any(c in org for c in rec['country']):

                        id_list.append([org, conf, rec['id']])
                        match_found = True
                        # print('STEP 6: Country appears in both affiliation and org')
                        break

            # -------------------------------
            # STEP 7: Specific/Acronym preference
            # -------------------------------
            if not match_found:

                for sp in specific:
                    if sp in org:

                        for rec in records:
                            if dix_id[rec['id']]['top_level'] == 'y':
                                id_list.append([org, conf, rec['id']])
                                match_found = True
                                # print('STEP 7: Specific/Acronym preference with top-level match')
                                break

                        if not match_found:
                            for rec in records:
                                if dix_id[rec['id']]['parent'] == 'y':
                                    id_list.append([org, conf, rec['id']])
                                    match_found = True
                                    # print('STEP 7: Specific/Acronym preference with parent match')
                                    break

                        break

            # -------------------------------
            # STEP 8: Fallback first='y'
            # -------------------------------
            if not match_found:
                # print(org)
                # print('last chance')
                if org != 'national research council':
                    if any(c in clean_aff for c in city_list):
                        id_list.append([org, conf, id_])
                        match_found = True
                        break
                    else:
                        for rec in records:
                            # print('rec', rec)
                            id_ = rec['id']

                            if 'department' not in org and \
                            'labora' not in org and \
                                'instit' not in org and \
                                not any( x in low_prob_countries for x in dix_id[id_]['country']) and \
                                rec['first'] == 'y':
                                id_list.append([org, conf, rec['id']])
                                match_found = True
                                # print('STEP 8: Fallback first="y" match')
                                break
                
                   
            # if not match_found:
            #     print('No match found for:', org)
    # print(id_list)
    return keep_highest_score(id_list)