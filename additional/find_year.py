import pandas as pd
import sys 
import tarfile
from concurrent.futures import ProcessPoolExecutor,wait,ALL_COMPLETED

def do(name, crossrefDF):
# combine all DataFrames into a single DataFrame
    # crossrefDF = pd.concat(dfsList, ignore_index=True)
    print("processing " + name)

    try:
        Authors = [i for i in range(len(crossrefDF)) if 'author'  in crossrefDF['items'][i]]

        crossrefAuth = crossrefDF.iloc[Authors].copy()

        crossrefAuth.reset_index(inplace= True)
        crossrefAuth.drop(columns = ['index'], inplace = True)

        crossrefAuth.loc[:, 'DOI'] = crossrefAuth['items'].apply(lambda x: x['DOI'])
        crossrefAuth.loc[:,'authors'] = crossrefAuth['items'].apply(lambda x: x['author'])

        def getAff(k):
            return [crossrefAuth['authors'][k][j]['affiliation'] for j in range(len(crossrefAuth['authors'][k]))]
            
        Affiliations = [getAff(k) for k in range(len(crossrefAuth))]

        crossrefAuth.loc[:,'affiliations'] = Affiliations

        possibleEmptyAff = []

        for k in range(len(crossrefAuth)):
            if len(crossrefAuth['affiliations'][k][0]) == 0:
                possibleEmptyAff.append(k)
                
                
        nonEmptyAff = []

        for k in possibleEmptyAff:
            for j in range(len(crossrefAuth['affiliations'].iloc[k])):
                if len(crossrefAuth['affiliations'].iloc[k][j]) != 0:
                    nonEmptyAff.append(k)
            
        FinalEmptyyAff =  [x for x in possibleEmptyAff if x not in nonEmptyAff] 
        FinalNonEmptyAff = [x for x in range(len(crossrefAuth)) if x not in FinalEmptyyAff]


        doiDF = crossrefAuth.iloc[FinalNonEmptyAff].copy()
        doiDF.reset_index(inplace = True)
        doiDF.drop(columns = ['index'], inplace = True)


        emptyBrackets = [k for k in range(len(doiDF)) if len(doiDF['affiliations'][k][0]) != 0 and doiDF['affiliations'][k][0][0] == {}]

        doiDF.drop(emptyBrackets, inplace = True)
        doiDF.reset_index(inplace = True)
        doiDF.drop(columns = ['index'], inplace = True)

        year = [(doiDF['items'].iloc[i]['issued']['date-parts'][0][0]) for i in range(len(doiDF))]

        doiDF['year'] = year
        # #num_22_23 = len(doiDF[doiDF['year'] > 2021])

        # result = doiDF.groupby('year')['DOI'].count()

        # result_df = result.reset_index()

        doiDF.to_csv('./count/' + name + '.csv', index=False, header=False, columns=['year'])
    
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
