import json
import pandas as pd
import requests_cache

# add proper error handling for non 200 responses

def get_metadata_bibliographic(session, citation, email):
    url = f"https://api.crossref.org/works?query.bibliographic={citation}&mailto={email}&rows=1"
    r = session.get(url)
    if r.status_code == 200:
        print(f"SUCCESS: {citation}")
        return r.json()["message"]["items"][0]
    else:
        print(f"ERROR: {citation}")
        return None

def get_metadata_doi(session, doi, email):
    url = f"https://api.semanticscholar.org/graph/v1/paper/{doi}?mailto={email}"
    r = session.get(url)
    if r.status_code == 200:
        print(f"SUCCESS: {doi}")
        return r.json()
    else:
        print(f"ERROR: {doi}")
        return None

def get_metadata_mult(session, citations, email, getter):
    
    all_metadata = []

    for citation in citations:
        metadata = getter(session, citation, email)
        if metadata:
            all_metadata.append(metadata)
    
    return all_metadata

def build_nodes(metadata):

    nodes = []

    for citation in metadata:
        
        citation = citation["message"]

        title = "" if "title" not in citation or len(citation["title"]) == 0 else citation["title"][0]
        author_family_names = []
        if "author" in citation:
            for author in citation["author"]:
                if "family" in author:
                    author_family_names.append(author["family"])
        author = ",".join(author_family_names)
        citation_count = citation["is-referenced-by-count"] if "is-referenced-by-count" in citation else 0
        
        nodes.append({
            "doi": citation["DOI"],
            "title": title,
            "authors": author,
            "is-referenced-by-count": citation_count,
            "link": citation["URL"]
        })

    return nodes

def build_links(metadata):

    links = []
    for citation in metadata:
        if "message" in citation:
            citation = citation["message"]

        if "reference" not in citation:
            continue
        for reference in citation["reference"]:
            if "DOI" in reference: # For now, a record must have a DOI
                links.append({"source": citation["DOI"], "target": reference["DOI"]})

    return links

def build_graph(session, bibliography, email):

    bibliography_metadata = get_metadata_mult(session, bibliography, email, get_metadata_bibliographic)
    
    bibliography_links = build_links(bibliography_metadata)

    references_metadata = get_metadata_mult(session, set([citation["target"] for citation in bibliography_links]), email, get_metadata_doi)

    reference_links = build_links(references_metadata)

    links = bibliography_links + reference_links

    print(len(links))
    
    node_metadata = get_metadata_mult(session, 
                                      set([citation["source"] for citation in links] + [citation["target"] for citation in links]), 
                                      email,
                                      get_metadata_doi)
    
    print(len(node_metadata))
    
    nodes = build_nodes(node_metadata)
    
    return nodes, links

def main():

    email = "ucfahpd@ucl.ac.uk"

    session = requests_cache.CachedSession('lit_review_graph_cache')

    with open("data/bibliography.txt") as f:
        bibliography = f.readlines()
    
    bibliography = [citation.strip() for citation in bibliography]

    nodes, links = build_graph(session, bibliography, email)

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
