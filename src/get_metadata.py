import sys
import json
import pandas as pd
import requests_cache
import logging

logging.basicConfig(filename='get_metadata.log', level=logging.INFO, filemode='w')

def get_paper_metadata(session, id, fields):
    url = f"https://api.semanticscholar.org/graph/v1/paper/{id}?fields={fields}"
    r = session.get(url)
    if r.status_code == 200:
        logging.info(f"{id}")
        return r.json()
    else:
        logging.error(f"{id}")

def get_metadata_mult(session, paper_ids, fields='url,year,title,references'):
    
    all_metadata = []

    for id in paper_ids:
        metadata = get_paper_metadata(session, id, fields)
        if metadata:
            all_metadata.append(metadata)
    
    return all_metadata

def build_nodes(metadata, bibliography_paper_ids):

    nodes = []

    for citation in metadata:

        if "name" not in citation["journal"].keys():
            citation["journal"]["name"] = "Unknown"
        
        if "authors" not in citation.keys():
            citation["authors"] = [{"authorId": None, "name": "Unknown"}]
        
        if "DOI" not in citation["externalIds"].keys():
            citation["externalIds"]["DOI"] = None
                
        nodes.append({
            "paperId": citation["paperId"],
            "title": citation["title"],
            "year": citation["year"],
            "citationCount": citation["citationCount"],
            "url": citation["url"],
            "group": citation["paperId"] in bibliography_paper_ids,
            "journal": citation["journal"]["name"],
            "author_ids": [x["authorId"] for x in citation["authors"]],
            "author_names": [x["name"] for x in citation["authors"]],
            "tldr": citation["tldr"],
            "DOI": citation["externalIds"]["DOI"]
        })

    return nodes

def build_links(metadata):

    links = []
    for paper in metadata:
        for reference in paper["references"]:
            links.append({"source": paper["paperId"], "target": reference["paperId"]})

    return links

def build_graph(session, bibliography):

    bibliography_paper_ids = [x["paperId"] for x in get_metadata_mult(session, bibliography) if x]

    bibliography_metadata = get_metadata_mult(session, bibliography_paper_ids)

    links = build_links(bibliography_metadata)
    
    node_metadata = get_metadata_mult(session, 
                                      set([x["source"] for x in links if x] + [x["target"] for x in links if x]),
                                      fields='url,year,title,citationCount,authors,journal,externalIds,tldr')
    
    nodes = build_nodes(node_metadata, bibliography_paper_ids)
    
    return nodes, links

def main():

    session = requests_cache.CachedSession('lit_review_graph_cache')

    with open(sys.argv[1]) as f:
        bibliography = f.readlines()
    
    bibliography = [f"DOI:{citation.strip()}" for citation in bibliography]

    nodes, links = build_graph(session, bibliography)

    with open(f"{sys.argv[2]}/nodes.json", "w") as f:
        json.dump(nodes, f, indent=4)
    
    with open(f"{sys.argv[2]}/links.json", "w") as f:
        json.dump(links, f, indent=4)

    pd.DataFrame(nodes).to_csv(f"{sys.argv[2]}/nodes.csv", index=False)
    pd.DataFrame(links).to_csv(f"{sys.argv[2]}/links.csv", index=False)
    
    
if __name__ == "__main__":
    main()