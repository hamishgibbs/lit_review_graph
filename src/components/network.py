import numpy as np
import dash_cytoscape as cyto

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

def PublicationCytoscape(cynodes, cylinks):

    cyto.Cytoscape(
                        id="cytoscape",
                        elements=cynodes + cylinks,
                        layout={"name": "cose"},
                        style={"width": "70%", "height": "600px"},
                        stylesheet=[
                            {
                                "selector": "node",
                                "style": {
                                    "width": "mapData(citationCountLog, 0, 100, 0.01, 100)",
                                    "height": "mapData(citationCountLog, 0, 100, 0.05, 100)",
                                },
                            },
                            {
                                "selector": "edge",
                                "style": {
                                    "width": 0.2,
                                },
                            },
                            {
                                "selector": "node",
                                "style": {
                                    "background-color": "mapData(group, 0, 1, rgb(199, 206, 219), rgb(84, 101, 255))"
                                },
                            },
                        ],
                    )