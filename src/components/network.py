import numpy as np

def build_cytoscape(nodes, links):

    cynodes = []

    for node in nodes:
        cynodes.append(
            {
                "data": {
                    "id": node["paperId"],
                    "title": node["title"],
                    "journal": node["journal"],
                    "year": node["year"],
                    "author_names": ", ".join(node["author_names"]),
                    "citationCount": node["citationCount"],
                    "citationCountLog": np.log2(
                        np.where(
                            node["citationCount"] == 0, 1e-100, node["citationCount"]
                        )
                    ),
                    "url": node["url"],
                    "group": int(node["group"]),
                    "tldr": node["tldr"],
                    "DOI": node["DOI"],
                }
            }
        )

    cylinks = []

    for link in links:

        if not link["target"]:
            continue

        cylinks.append({"data": {"source": link["source"], "target": link["target"]}})

    return cynodes, cylinks