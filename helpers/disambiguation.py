from .functions import *
from .create_input import *
from .__init__ import VERSION

    
us_states = [
    "alabama", "alaska", "arizona", "arkansas", "california",
    "colorado", "conecticut", "delaware", "florida", "georgia",
    "hawaii", "idaho", "ilinois", "indiana", "iowa",
    "kansas", "kentucky", "louisiana", "maine", "maryland",
    "masachusets", "michigan", "minesota", "misisipi", "misouri",
    "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "carolina", "dakota", "ohio",
    "oklahoma", "oregon", "pensylvania", "rhode island",
    "tenesee", "texas", "utah", "vermont",
    "virginia", "washington", "wisconsin", "wyoming"
]


def contains_us_state(text):
    text = text.lower()
    return any(state in text for state in us_states)

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
    # print(input)
    result_dict = convert_to_result(id_list_, dix_id)
    # print('result_dict',result_dict)
    num_actives = count_active(result_dict)
    # print('result_dict',result_dict)
    # print('num_actives', num_actives)
    if len(id_list_) ==1:
        return result_dict
        
    elif len(description(clean_aff)[1]) == 0: 
        # print('no country in affiliation')  
        # polytechnic?
        countries_uni = {
    country
    for res in result_dict
    if 'Uni' in res['name']
    for country in res['country']
}
        # print('countries_uni',countries_uni)

        #[res['country'] for res in result_dict if 'Uni' in res['name']]
        if len(countries_uni) >0:
            final_matching = [res for res in result_dict if any(c in countries_uni for c in res['country'])]
            return final_matching
        else:
            # print('no universities')
            return result_dict
        
    elif num_actives > len(set(description(clean_aff)[1])):
        # print('more results than countries')
        final_matching = []
        light_aff_tokens = [clean_string_ror(x) for x in set(clean_aff.split())]
        for res in result_dict:
            # print('res',res)
            country = res['country']
            if 'united states' in country:
                if 'united states' in clean_aff or 'usa' in light_aff_tokens or contains_us_state(clean_aff):
                    final_matching.append(res)

            elif 'united kingdom' in country:
                if 'united kingdom' in clean_aff or 'uk' in light_aff_tokens:
                    final_matching.append(res)
            
            elif 'korea' in str(country):
          
                if 'korea' in light_aff_tokens:
                    final_matching.append(res)

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
        