from affro.helpers.functions import *
from affro.helpers.create_input import *
from .. import __version__

VERSION = __version__

    

pattern = re.compile(r'\b(' + '|'.join(us_states) + r')\b')

def contains_us_state(text):
    return bool(pattern.search(text.lower()))

# def contains_gr_cities(text):
#     return bool(pattern.search(text.lower()))

# def contains_ie_cities(text):
#     return bool(pattern.search(text.lower()))

# weak_keywords = ['department']

def convert_to_result(id_list_, dix_id):
    result = []
    seen = set()

    for r in id_list_:
        score = r[1]
        if score > 1.0:
            score = 1.0

        value = r[2]
        rec = dix_id.get(value)
        if not rec:
            continue

        name = rec.get('name')
        country = rec.get('country')

        status = rec.get('status') or []
        primary = status[0] if status else None
        secondary = status[1] if len(status) > 1 else []

        # openorgs
        if "openorgs" in value:
            key = ('openorgs', value)
            if key not in seen:
                seen.add(key)
                result.append({
                    'provenance': 'affro',
                    'version': VERSION,
                    'pid': 'openorgs',
                    'value': value,
                    'name': name,
                    'confidence': float(score),
                    'status': 'active',
                    'country': country
                })
            continue

        # ROR active
        if primary == 'active':
            key = ('ror', value)
            if key not in seen:
                seen.add(key)
                result.append({
                    'provenance': 'affro',
                    'version': VERSION,
                    'pid': 'ror',
                    'value': value,
                    'name': name,
                    'confidence': float(score),
                    'status': 'active',
                    'country': country
                })
            continue

        # ROR inactive
        key = ('ror', value)
        if key not in seen:
            seen.add(key)
            result.append({
                'provenance': 'affro',
                'version': VERSION,
                'pid': 'ror',
                'value': value,
                'name': name,
                'confidence': float(score),
                'status': primary,
                'country': country
            })

        # linked active records
        if secondary and secondary[0] != '':
            for link in secondary:
                if not link:
                    continue

                link_key = ('ror', link)
                if link_key in seen:
                    continue

                link_rec = dix_id.get(link)
                if not link_rec:
                    continue

                seen.add(link_key)
                result.append({
                    'provenance': 'affro',
                    'version': VERSION,
                    'pid': 'ror',
                    'value': link,
                    'name': link_rec.get('name'),
                    'confidence': float(score),
                    'status': 'active',
                    'country': link_rec.get('country')
                })

    return result



def count_active(items):
    return sum(1 for x in items if x.get("status") == "active")
    
def disamb(input, id_list_,dix_id):
    # print('disamb id_list_', id_list_)
    if id_list_ == []:
        return []
    clean_aff = input[0]
    # print('result_dict',result_dict)
    if 'https://ror.org/00nnh8h94' in str(id_list_) and ('greece' not in clean_aff and 'helas' not in clean_aff and 'athens' not in clean_aff):
        id_list_ = [id for id in id_list_ if id[2] != 'https://ror.org/00nnh8h94']
    result_dict = convert_to_result(id_list_, dix_id)

    num_actives = count_active(result_dict)
    num_countries = len(description(clean_aff)[1])

    # print('num_actives', num_actives)
    if len(id_list_) ==1 :
        return result_dict
    elif num_countries == 0: 
        # print('no country in affiliation')  
        # polytechnic?
        # countries_uni = {
        # country
        # for res in result_dict
        # if 'Uni' in res['name'] or 'Trinity' in res['name'] 
        # for country in res['country'] }-low_prob_countries
       
        countries_high = {
        country
        for res in result_dict
        for country in res['country']
        if country not in low_prob_countries
    }
        # print(countries_high)
        # print('countries_uni',countries_uni)

        #[res['country'] for res in result_dict if 'Uni' in res['name']]
        if len(countries_high) >0:
            #If we suspect the affiliation refers to a university, restrict matches to the same country as detected university candidates
            final_matching = [res for res in result_dict if any(c in countries_high for c in res['country'])]
            if len(final_matching)==1 or len(countries_high)==1:
                return final_matching
            else:
                final_matching2 = [res for res in final_matching if 'Inst' not in res['name'] and 'Lab' not in res['name']]
                return final_matching2
            
        else:
            # print('no universities')
            return result_dict
       
    elif num_actives > num_countries:
        # print('more results than countries')
        final_matching = []
        light_aff_tokens = [clean_string_ror(x) for x in set(clean_aff.split())]
        for res in result_dict:
            # print('res',res)
          
            country = res['country']
            country_str = str(country)
            if 'united states' in country:
                if 'united states' in clean_aff or 'usa' in light_aff_tokens or contains_us_state(clean_aff):
                    final_matching.append(res)

            elif 'united kingdom' in country:
                if 'united kingdom' in clean_aff or 'uk' in light_aff_tokens:
                    final_matching.append(res)
            
            elif 'korea' in country_str:
          
                if 'korea' in light_aff_tokens:
                    final_matching.append(res)
            # elif 'greece' in country:
            #     if 'greece' in clean_aff or 'helas' in clean_aff or contains_gr_cities(clean_aff):
            #         inal_matching.append(res)


            elif any(c in clean_aff for c in country): #country in clean_aff:
                final_matching.append(res)
            
        if final_matching:
            return final_matching
        
        else:
            return result_dict

    elif len(result_dict)>0:
        return result_dict
    else:
        # print('leider nichts')
        return  []
        