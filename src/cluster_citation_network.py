# Drop any nodes that are cited by nobody (even if they cite others)
# In future - can show that most (?) research is never picked up by anyone else
# Create an adjacency matrix from the network
# Use hierarchical clustering from the communities package
# output number and size of clusters at each hierarchcal level 
# output cluster membership for each node at each level
# when done - check whether clusters seem meaningful
# Look at the distribution of citations for each cluster 
# Identify which clusters contain the seed papers 
# and which papers in the cluster make up a large proportion of the citations
# These are the papers to read
# Visualize each cluster (to keep the size of the visualized network down) - could replace non-cluster connections to a single node

import numpy as np
import pandas as pd
from communities.algorithms import girvan_newman

def drop_uncited_links(links):

    uncited_ids = np.setdiff1d(
        links["source"].unique(), 
        links["target"].unique()
    )

    return links[~links["source"].isin(uncited_ids)]

def build_adjacency_matrix(links):

    n = len(set(list(links["source_numeric"].unique()) + list(links["target_numeric"].unique())))

    adjacency_matrix = np.zeros(
      (n, n)
    )

    for row in links.iterrows():
        adjacency_matrix[row[1]["source_numeric"], row[1]["target_numeric"]] = 1

    return adjacency_matrix

def main():
    links = pd.read_csv("output/links.csv")
    cited_links = drop_uncited_links(links)
    
    unique_ids = np.sort(list(set(list(cited_links["source"].unique()) + list(cited_links["target"].unique()))))

    numeric_ids = {id: i for i, id in enumerate(unique_ids)}

    cited_links["source_numeric"] = cited_links["source"].apply(lambda x: numeric_ids[x])
    cited_links["target_numeric"] = cited_links["target"].apply(lambda x: numeric_ids[x])

    adjacency_matrix = build_adjacency_matrix(cited_links)

    print(adjacency_matrix)
    print(girvan_newman(adjacency_matrix)[2])




if __name__ == "__main__":
    main()
