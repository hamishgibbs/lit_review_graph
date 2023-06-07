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

def get_metadata_mult(session, citations, fields='url,year,title,citations'):
    
    all_metadata = []

    for id in citations:
        metadata = get_paper_metadata(session, id, fields)
        if metadata:
            all_metadata.append(metadata)
    
    return all_metadata

def build_nodes(metadata, bibliography_paper_ids):

    nodes = []

    for citation in metadata:
                
        nodes.append({
            "paperId": citation["paperId"],
            "title": citation["title"],
            "is-referenced-by-count": citation["citationCount"],
            "url": citation["url"],
            "group": citation["paperId"] in bibliography_paper_ids,
        })

    return nodes

def build_links(metadata):

    links = []
    for citation in metadata:
        for reference in citation["citations"]:
            links.append({"source": citation["paperId"], "target": reference["paperId"]})

    return links

def build_graph(session, bibliography):

    # This could be made recursive, to search with arbitrary depth d
    bibliography_paper_ids = [x["paperId"] for x in get_metadata_mult(session, bibliography) if x]

    bibliography_metadata = get_metadata_mult(session, bibliography_paper_ids)

    bibliography_links = build_links(bibliography_metadata)

    references_paper_ids = [x for x in set([citation["target"] for citation in bibliography_links]) if x]

    references_metadata = get_metadata_mult(session, references_paper_ids)

    reference_links = build_links(references_metadata)

    links = bibliography_links + reference_links

    print(f"Links: {len(links)}")
    print(f"Nodes: {len(set([x['source'] for x in links if x] + [x['target'] for x in links if x]))}")
    
    node_metadata = get_metadata_mult(session, 
                                      set([x["source"] for x in links if x] + [x["target"] for x in links if x]),
                                      fields='url,year,title,citationCount')
    
    nodes = build_nodes(node_metadata, bibliography_paper_ids)
    
    return nodes, links

def main():

    session = requests_cache.CachedSession('lit_review_graph_cache')

    with open("data/bibliography.txt") as f:
        bibliography = f.readlines()
    
    bibliography = [f"DOI:{citation.strip()}" for citation in bibliography]

    nodes, links = build_graph(session, bibliography)

    with open("output/nodes.json", "w") as f:
        json.dump(nodes, f, indent=4)
    
    with open("output/links.json", "w") as f:
        json.dump(links, f, indent=4)

    pd.DataFrame(nodes).to_csv("output/nodes.csv", index=False)
    pd.DataFrame(links).to_csv("output/links.csv", index=False)
    
    
if __name__ == "__main__":
    main()

# "DOI"
# "title"
# "author" <- all authors (needs to be formatted)
# "reference" <- all references
# "is-referenced-by-count" <- number of articles citing this article
