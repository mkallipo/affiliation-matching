import pandas as pd
import logging
import os

all_files = os.listdir()

txt_list = [filename for filename in all_files if filename.endswith('.txt') and filename != 'dois_iis.txt' and filename!= 'output.txt']


file_path = 'dois_iis.txt'

with open(file_path, 'r') as file:
    dois_iis = [line.strip() for line in file]
        
        
def common_elements(list1, list2):
    common_list = []
    i = 0  # Index for list1
    j = 0  # Index for list2

    while i < len(list1) and j < len(list2):
        if list1[i] == list2[j]:
            common_list.append(list1[i])
            i += 1
            j += 1
        elif list1[i] < list2[j]:
            i += 1
        else:
            j += 1

    return common_list


def common_dois(txt):
    with open(txt, 'r') as file:
        l = [line.strip() for line in file]

        
        dois_common = 'dois_common'

        l_common = common_elements(l, dois_iis)
        
        if len(l_common)>0:
            file_name_without_extension = os.path.splitext(os.path.basename(txt))[0]
            output_txt = os.path.join(dois_common, f"{file_name_without_extension}.txt")
        
            
       
        
            with open(output_txt, 'w') as file:
                for item in l_common:
                    file.write(item + "\n")

    



for txt in txt_list:
    print('processing file ' + txt)
    try:
        common_dois(txt)
        print('file ' + txt + ' done')

    except Exception as Argument:

        logging.exception("Error in thred code for file: " + txt)
