from affro.helpers.functions import *
from . import __version__

VERSION = __version__

def distance(s, substr1, substr2):
    pos1 = s.find(substr1)  # start index of substr1
    pos2 = s.find(substr2)  # start index of substr2

    # One of the substrings not found

    distance = abs(pos1 - pos2)
    return distance

# Sort by descending key length so the most specific keys are checked first,
# giving earlier matches and fewer iterations on average.
def _build_label_keys(label, exclude=None):
    """Return (sorted_keys, key_to_id) for a given label."""
    keys = []
    key_to_id = {}
    for k, v in dix_name.items():
        if exclude and k in exclude:
            continue
        for d in v:
            if d.get("label") == label:
                keys.append(k)
                key_to_id[k] = d["id"]
                break
    sorted_keys = sorted(keys, key=len, reverse=True)
    return sorted_keys, key_to_id

forth_keys,      forth_id      = _build_label_keys("forth")
demokritos_keys, demokritos_id = _build_label_keys("demokritos")
ircs_keys,       ircs_id       = _build_label_keys("ircs")
fraunhofer_keys, fraunhofer_id = _build_label_keys("fraunhofer")
cnr_keys,        cnr_id        = _build_label_keys("cnr", exclude={'isti', 'cnr isti'})
max_planck_keys, max_planck_id = _build_label_keys("max_planck")
helmholtz_keys,   helmholtz_id   = _build_label_keys("helmholtz")
leibniz_keys,    leibniz_id    = _build_label_keys("leibniz")
infn_keys,       infn_id       = _build_label_keys("infn")


def _make_entry(pid, id, info):
    return {
        'provenance': 'affro_direct',
        'version': VERSION,
        'pid': pid,
        'value': id,
        'name': info['name'],
        'confidence': 1,
        'status': info['status'][0],
        'country': info['country'],
        
    }


def direct_mapping_schema(list_ids):
    res = []
    for id in set(list_ids):
        info = dix_id[id]          # single lookup per id
        if 'ror' in id:
            res.append(_make_entry('ror', id, info))
            if info['status'][0] != 'active':
                for successor in info['status'][1]:
                    res.append(_make_entry('ror', successor, dix_id[successor]))
        else:
            res.append(_make_entry('openorgs', id, info))
    return res


def direct_mapping(aff):
    assigned = []
    # if lucky_guess is None:
    #     aff_cleaned = clean_string(aff)
    # else:
    #     aff_cleaned = lucky_guess
    # shorten_aff = aff_cleaned

   # stem univ, inst
    aff_cleaned =   normalize_organization_names(clean_string(aff), university_terms).replace(" and ", " ")
    shorten_aff = aff_cleaned
    # print(aff_cleaned)
    if 'europ univer' in shorten_aff and 'cyprus' in shorten_aff:
        assigned.append('https://ror.org/04xp48827')
        shorten_aff = shorten_aff.replace('europ univer', '')
    if 'colege' in shorten_aff:
        if 'intercolege' in shorten_aff and ('cyprus' in shorten_aff or 'nicosia' in shorten_aff):
            assigned.append('https://ror.org/012gfrj24')
            shorten_aff = shorten_aff.replace('intercolege', '')
        if 'mary immaculate colege' in shorten_aff and ('limerick' in shorten_aff or 'ireland' in shorten_aff):
            assigned.append('https://ror.org/009q3yg92')
            shorten_aff = shorten_aff.replace('mary immaculate colege', ',')

    if 'foundation research techn' in shorten_aff and ('helas' in shorten_aff or 'greece' in shorten_aff):
        # print('h')
        assigned.append('https://ror.org/052rphn09')
        shorten_aff = shorten_aff.replace('foundation research techn', '')
    if 'instit' in shorten_aff or "istituto" in shorten_aff:
        
        if 'friedrich loefler' in shorten_aff:
            assigned.append('https://ror.org/025fw7a54')
            shorten_aff = shorten_aff.replace('friedrich loefler instit', '').replace('bundesforschungsinstit tiergesundheit', '').replace('federal research instit animal health', '')

        if 'julius kuhn' in shorten_aff or 'julius kuehn' in shorten_aff:
            assigned.append('https://ror.org/022d5qt08')
            shorten_aff = shorten_aff.replace('julius kuhn instit', '').replace('julius kuehn', '').replace('bundesforschungsinstit kulturpflanzen', '').replace('federal research center cultivated plants', '')

        if "forth" in shorten_aff or 'foundation research techn' in shorten_aff:
            for key in forth_keys:
                if key in shorten_aff and (distance(shorten_aff, 'forth', key) < len(key)+len('forth')+5 or 'foundation research techn' in shorten_aff):
                    ror_id = forth_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',')

        if "demokritos" in shorten_aff or "ncsr" in shorten_aff:
            for key in demokritos_keys:
                if key in shorten_aff and distance(shorten_aff, 'demokritos', key) < len(key)+len('demokritos')+5:
                    ror_id = demokritos_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',')

        if 'tu clausthal' in shorten_aff and 'instit organische chemie' in shorten_aff and distance(shorten_aff, 'tu clausthal', 'instit organische chemie') < len('tu clausthal')+len('instit organische chemie')+5:
            assigned.append('openorgs____::0000103105')
            shorten_aff = shorten_aff.replace('instit organische chemie', ',')

        if 'ircs' in shorten_aff or 'istituti ricovero e cura caratere scien' in shorten_aff or 'milan' in shorten_aff:
            for key in ircs_keys:
                if key in shorten_aff and distance(shorten_aff, 'ircs', key) < len(key)+len('istituti ricovero e cura caratere scien')+5:
                    ror_id = ircs_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',')
        if 'infn' in shorten_aff or 'istituto nazionale fisica nucleare' in shorten_aff:
            for key in infn_keys:
                if key in shorten_aff:
                    ror_id = infn_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',')

        if ('instit comunication computer systems' in shorten_aff or 'ics' in shorten_aff or 'instit computer comunication systems') and ('national techn univer athens' in aff_cleaned or 'ntua' in aff_cleaned):
            assigned.append('https://ror.org/0483fn738')
            shorten_aff = shorten_aff.replace('instit comunication computer systems', ',')

        if 'fraunhofer' in shorten_aff:
            for key in fraunhofer_keys:
                if key in shorten_aff and distance(shorten_aff, 'fraunhofer', key) < len(key)+len('fraunhofer')+5:
                    ror_id = fraunhofer_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',').replace('fraunhofer', ',')

        if 'cnr' in shorten_aff or ('national research council' in shorten_aff and 'italy' in shorten_aff):
            for key in cnr_keys:
                if key in shorten_aff and distance(shorten_aff, 'cnr', key) < len(key)+len('national research council')+5:
                    ror_id = cnr_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',')

        if 'max planck' in shorten_aff:
            for key in max_planck_keys:
                if key in shorten_aff and distance(shorten_aff, 'max planck', key) < len(key)+len('max planck')+15:
                    ror_id = max_planck_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',')

        if 'helmholtz' in shorten_aff:
            for key in helmholtz_keys:
                if key in shorten_aff and distance(shorten_aff, 'helmholtz', key) < len(key)+len('helmholtz')+15:
                    ror_id = helmholtz_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)

        if 'leibniz' in shorten_aff:
            for key in leibniz_keys:
                if key in shorten_aff and distance(shorten_aff, 'leibniz', key) < len(key)+len('leibniz')+15:
                    ror_id = leibniz_id.get(key)
                    if ror_id is not None:
                        assigned.append(ror_id)
                        shorten_aff = shorten_aff.replace(key, ',')
    

    return [direct_mapping_schema(assigned), shorten_aff]
