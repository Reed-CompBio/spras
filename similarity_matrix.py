import pandas as pd
import argparse

# send in a list of tupples (the file name for now, and the edges)
# return a list of dfs

def make_dataframe(list_of_tuples):
    list_of_dfs = []
    
    for tuple in list_of_tuples:
        col_label = str(tuple[0])

        dataframe = pd.DataFrame(
            {
                col_label: 'yes', #tuple[1]
            }, index= tuple[1]
        )
        list_of_dfs.append(dataframe)
   
    return list_of_dfs


# will take in a list of dataframes
# return the pandas table
def concat_dfs(list_of_dataframes):
   
    result = pd.concat(list_of_dataframes, axis= 1, join = 'outer')
    result = result.fillna('no') #result.fillna('-') 

    return result

# will take in the list of files
# returns a list of tuples (the name [for now the file name] and the list of edges)
def parse_files(edge_files):
    list_of_tuples = []
    
    for file in edge_files:
        with open(file,'r') as f:
            lines = [line[:3] for line in f.readlines()]
        
        line = []
        for char in lines:
            newChar = char.replace(' ','')
            line.append(newChar)
            
        result = [''.join(sorted(ele)) for ele in line]
            
        print (result)
        list_of_tuples.append((file, result))
    
    return list_of_tuples

def main(args):
    
    list_of_tuples = parse_files(args.edge_files)
    list_of_dataframes = make_dataframe(list_of_tuples)
    con_dfs = concat_dfs(list_of_dataframes)
    print(con_dfs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
  
    parser.add_argument('--edge_files',
                        nargs='+',
                        type = str, 
                        required=True)
    
    # python similarity_matrix.py --edge_files s1.txt /Users/nehatalluri/Desktop/jobs/research/spras/output/data0-mincostflow-params-SZPZVU6/pathway.txt
    
    args = parser.parse_args()

main(args)



