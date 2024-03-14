import pandas as pd
import sys 
import tarfile
from concurrent.futures import ProcessPoolExecutor,wait,ALL_COMPLETED

def do(name, crossref_df):
# combine all DataFrames into a single DataFrame
    # crossrefDF = pd.concat(dfsList, ignore_index=True)
    print("processing " + name)

    try:
        authors = [i for i in range(len(crossref_df)) if 'author'  in crossref_df['items'][i]]


        date = [(crossref_df['items'].iloc[i]['issued']['date-parts'][0][0]) for i in range(len(crossref_df))]
        date_dep = [(crossref_df['items'].iloc[i]['deposited']['date-parts'][0][0]) for i in range(len(crossref_df))]
        type = [(crossref_df['items'].iloc[i]['type']) for i in range(len(crossref_df))]



        crossref_df['date'] = date
        crossref_df['date_dep'] = date_dep
        crossref_df['type'] = type


        crossref_auth = crossref_df.iloc[authors].copy()

        crossref_auth.reset_index(inplace= True)
        #crossref_auth.drop(columns = ['index'], inplace = True)

        #crossref_auth.loc[:, 'DOI'] = crossref_auth['items'].apply(lambda x: x['DOI'])
        crossref_auth.loc[:,'authors'] = crossref_auth['items'].apply(lambda x: x['author'])

        def getAff(k):
            return [crossref_auth['authors'][k][j]['affiliation'] for j in range(len(crossref_auth['authors'][k]))]
            
        affiliations = [getAff(k) for k in range(len(crossref_auth))]

        crossref_auth.loc[:,'affiliations'] = affiliations

        ## Clean 'empty' affiliations

        possible_empty_aff = []

        for k in range(len(crossref_auth)):
            if len(crossref_auth['affiliations'][k][0]) == 0:
                possible_empty_aff.append(k)
                
        non_empty_aff = []

        for k in possible_empty_aff:
            for j in range(len(crossref_auth['affiliations'].iloc[k])):
                if len(crossref_auth['affiliations'].iloc[k][j]) != 0:
                    non_empty_aff.append(k)
            
        final_empty_aff =  [x for x in possible_empty_aff if x not in non_empty_aff] 
        final_non_empty_aff = [x for x in range(len(crossref_auth)) if x not in final_empty_aff]


        doi_df = crossref_auth.iloc[final_non_empty_aff].copy()
        doi_df.reset_index(inplace = True)
        doi_df.drop(columns = ['index'], inplace = True)

        # (still some cleaning: cases with empty brackets [{}])

        empty_brackets = [k for k in range(len(doi_df)) if len(doi_df['affiliations'][k][0]) != 0 and doi_df['affiliations'][k][0][0] == {}]
        doi_df.iloc[empty_brackets]
        doi_df.drop(empty_brackets, inplace = True)

        doi_df.reset_index(inplace = True)
        doi_df.drop(columns = ['index'], inplace = True)    


        doi_df['affiliations'] = 'Y'

        indices = list(doi_df['level_0'])
        no_affiliations = [i for i in range(len(crossref_df)) if i not in indices]

        no_affiliations_df = crossref_df.iloc[no_affiliations]
        no_affiliations_df = no_affiliations_df.reset_index()
        no_affiliations_df['authors'] = '-'
        no_affiliations_df['affiliations'] = 'N'

        no_affiliations_df = no_affiliations_df.rename(columns = {'index':'level_0'})

        final_df = pd.concat([no_affiliations_df, doi_df])
        final_df = final_df.sort_values(by='date')
        final_df.reset_index(inplace = True)
        final_short_df = final_df.drop(columns = ['level_0', 'index', 'items','authors'])


        # Save the DataFrame as a CSV file
        final_short_df.to_csv('./count/' + name + '.csv', index=False, header=False)  



    
    except Exception as Argument:
        logging.exception("Error in thread code for file: " + name)

i = 0
data = []
numberOfThreads = int(sys.argv[2])
executor = ProcessPoolExecutor(max_workers=numberOfThreads)

with tarfile.open(sys.argv[1], "r:gz") as tar:
    while True:
        member = tar.next()
        # returns None if end of tar
        if not member:
            break
        if member.isfile():
            
            print("reading file: " + member.name)
            
            # files= ['0.json', '1.json', '2.json', '3.json', '4.json','42.json', '15693.json']
            # files = ['42.json']
            # create an empty list to store the DataFrames
            current_file = tar.extractfile(member)

            crossrefDF = pd.read_json(current_file, orient='records')
            data.append((member.name, crossrefDF))

            i += 1
            if (i > numberOfThreads):
                print("execute batch: " + str([name for (name, d) in data]))
                futures = [executor.submit(do, name, d) for (name, d) in data]
                done, not_done = wait(futures)
                
                # print(done)
                print(not_done)

                data = []
                i = 0

    futures = [executor.submit(do, name, d) for (name, d) in data]
    done, not_done = wait(futures)
    print(not_done)

    print("Done")
    
    

