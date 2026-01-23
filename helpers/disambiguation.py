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
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pensylvania", "rhode island", "south carolina",
    "south dakota", "tennesee", "texas", "utah", "vermont",
    "virginia", "washington", "west virginia", "wisconsin", "wyoming"
]


def contains_us_state(text):
    text = text.lower()
    return any(state in text for state in us_states)

# def get_city(name, dix_name):
#     return {x['city'] : x['id'] for x in dix_name[name]}


# weak_keywords = ['department']


def convert_to_result(id_list_, dix_id):
    """
    id_list_ rows: [something, score, value]
    dix_id: mapping from id -> {'name':..., 'country':..., 'status': [primary, secondary_list]}
    """
    result_dict = []
    for r in id_list_:
        # Confidence is in r[1]
        score = min(r[1], 1.0)
        value = r[2]

        rec = dix_id.get(value)

        if rec is None:
            # missing metadata for this id — skip (or log if you want)
            continue

        name = rec.get('name')
        country = rec.get('country')
        status_field = rec.get('status', [])
        primary_status = status_field[0] if len(status_field) > 0 else None
        secondary = status_field[1] if len(status_field) > 1 else []

        def make_entry(pid, val, nm, conf, st, ctry):
            return {
                'provenance': 'affro',
                'version': VERSION,
                'pid': pid,
                'value': val,
                'name': nm,
                'confidence': conf,
                'status': st,
                'country': ctry
            }

        if "openorgs" in value:
            result_dict.append(make_entry('openorgs', value, name, score, 'active', country))
            continue

        # ROR branch
        if primary_status == 'active':
            result_dict.append(make_entry('ror', value, name, score, 'active', country))
            continue

        # primary is not active
        # treat case where secondary exists and its first element is empty string specially
        if secondary and secondary[0] == '':
            result_dict.append(make_entry('ror', value, name, score, primary_status, country))
        else:
            # append parent (non-active)
            result_dict.append(make_entry('ror', value, name, score, primary_status, country))
            # append linked records (use link's own metadata)
            for link in secondary:
                if not link:
                    continue
                link_rec = dix_id.get(link, {})
                link_name = link_rec.get('name')
                link_country = link_rec.get('country')
                result_dict.append(make_entry('ror', link, link_name, score, 'active', link_country))

    return result_dict

def count_active(items):
    return sum(1 for x in items if x.get("status") == "active")
    
def disamb(input, id_list_,dix_id):
    # print('disamb id_list_', id_list_)
    if id_list_ == []:
        return []
    
    clean_aff = input[0]
    # print(input)
    result_dict = convert_to_result(id_list_, dix_id)
    num_actives = count_active(result_dict)
    # print('result_dict',result_dict)
    # print('num_actives', num_actives)
    if len(id_list_) ==1:
        # print('1')
        return result_dict
        
    elif len(description(clean_aff)[1]) == 0: 
        # print('no country in affiliation')  
        # polytechnic?
        countries_uni = [res['country'] for res in result_dict if 'Uni' in res['name']]
        if len(countries_uni) >0:
            final_matching = [res for res in result_dict if res['country'] in countries_uni]
            return final_matching
        else:
            # print('no universities')
            return result_dict
        
    elif num_actives > len(set(description(clean_aff)[1])):
        # print('more results than countries')
        final_matching = []
        light_aff_tokens = [clean_string_ror(x) for x in set(clean_aff.split())]
        for res in result_dict:
            country = res['country']
            if country == 'united states':
                if 'united states' in clean_aff or 'usa' in light_aff_tokens or contains_us_state(clean_aff):
                    final_matching.append(res)

            elif country == 'united kingdom':
                if 'united kingdom' in clean_aff or 'uk' in light_aff_tokens:
                    final_matching.append(res)
            
            elif 'korea' in country:
          
                if 'korea' in light_aff_tokens:
                    final_matching.append(res)

            elif country in clean_aff:
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
        