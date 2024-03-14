import sys
import tarfile
import json
import random
import jsonlines


if (len(sys.argv) != 5):
    print("Usage: python3 get-crossref-sample.py <crossref tar gz file> <sample size> <samples per crossref file> <output file>")
    sys.exit(-1)

sampleSize = int(sys.argv[2])
sampleNumFromFile = int(sys.argv[3])
outfile = sys.argv[4]

papers = []

with tarfile.open(sys.argv[1], "r:gz") as tar:

    while True:
        member = tar.next()
        # returns None if end of tar
        if not member:
            break
        if member.isfile():
            current_file = tar.extractfile(member)

            try:
                file_content = json.load(current_file)
                json_papers = file_content['items']

                papers.extend(random.sample(json_papers, sampleNumFromFile))

                if (len(papers) >= sampleSize):
                    break

            except (ValueError, KeyError) as json_error:
                print(f'=> Cannot parse json file: {member.name}')


data = {}
data["items"] = papers

json_object = json.dumps(data, indent=4)
 
with open(outfile, "w") as outfile:
    outfile.write(json_object)