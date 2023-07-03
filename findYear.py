import pandas as pd


file = '42.json'


crossrefDF = pd.read_json(file, orient='records')



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
#num_22_23 = len(doiDF[doiDF['year'] > 2021])



result = doiDF.groupby('year')['DOI'].count()

result_df = result.reset_index()

result_df.to_csv('output.csv', index=False)
