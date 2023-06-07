import pandas as pd

def main():

    nodes = pd.read_csv("output/nodes.csv")
    nodes.drop_duplicates(subset=["paperId"], inplace=True)
    nodes["id"] = nodes.index
    nodes.set_index("paperId", inplace=True)
    

    links = pd.read_csv("output/links.csv")
    links.dropna(inplace=True)

    # quickfix - some links are not in the nodes dataframe? 
    links_not_in_nodes = set(links["source"].to_list() + links["target"].to_list()).difference(set(nodes.index))
    
    links = links[~links["source"].isin(links_not_in_nodes)]
    links = links[~links["target"].isin(links_not_in_nodes)]

    links["source"] = nodes.loc[links["source"].to_list(), "id"].to_list()
    links["target"] = nodes.loc[links["target"].to_list(), "id"].to_list()
    links.to_csv("output/infomap/links.csv", sep=" ", header=False, index=False)

if __name__ == "__main__":
    main()  