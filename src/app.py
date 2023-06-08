import sys
import os
import requests_cache
import numpy as np
import pandas as pd
from dash import Dash, html, dash_table, dcc
from dash.dependencies import Input, Output
import dash_cytoscape as cyto
import plotly.express as px

from get_metadata import build_graph

def CitationTable(df):

    return dash_table.DataTable(
        id='table-degree',
        columns=[{
            "name": "Title",
            "id": "title",
            "type": "text",
            "presentation": "markdown"
        },
        {
            "name": "Citations",
            "id": "citationCount",
        },
        {
            "name": "Degree",
            "id": "degree",
        }
        ],
        data=df.to_dict('records'),
        style_cell={'textAlign': 'left'},
        page_action='native',
        page_size=5,
        style_cell_conditional=[
        {
            'if': {'column_id': 'title'},
            'maxWidth': '500px',
            'overflow': 'auto',
            'textOverflow': 'ellipsis',
        }
        ])
    

def build_graph_from_bibliography(bibliography):
    
    session = requests_cache.CachedSession('lit_review_graph_cache')
    
    with open(bibliography) as f:
        bibliography = f.readlines()
    
    bibliography = [f"DOI:{citation.strip()}" for citation in bibliography]

    return build_graph(session, bibliography)

def build_cytoscape(nodes, links):

    cynodes = []

    for node in nodes:
        cynodes.append({
            "data": {
                "id": node["paperId"],
                "title": node["title"],
                "journal": node["journal"],
                "year": node["year"],
                "author_names": ", ".join(node["author_names"]),
                "citationCount": node["citationCount"],
                "citationCountLog": np.log2(np.where(node["citationCount"] == 0, 1e-100, node["citationCount"])),
                "url": node["url"],
                "group": int(node["group"]),
                "tldr": node["tldr"],
                "DOI": node["DOI"]
            }
        })

    cylinks = []

    for link in links:

        if not link["target"]:
            continue

        cylinks.append({
            "data": {
                "source": link["source"],
                "target": link["target"]
            }
        })

    return cynodes, cylinks

def get_publications_by_degree(nodes, links):
    
    node_ids = [x for x in nodes["paperId"]]

    for node in node_ids:
        node_degree = len(links[links["source"] == node]) + len(links[links["target"] == node])
        nodes.loc[nodes["paperId"] == node, "degree"] = node_degree

    nodes = nodes.sort_values(["degree", "citationCount"], ascending=False)
    nodes = nodes[nodes["group"] == 0]
    nodes = nodes[nodes["degree"] > 1]

    nodes['title'] = nodes.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)

    return nodes[["title", "citationCount", "degree"]]

def get_publications_by_citations(nodes, links):

    nodes = nodes.sort_values(["group", "citationCount"], ascending=False).reset_index()

    nodes["citationCount_cumulative"] = np.cumsum(nodes["citationCount"]) 
    nodes["citationCount_cumulative_prop"] = nodes["citationCount_cumulative"] / np.sum(nodes["citationCount"])

    return nodes

def get_publications_top_50_perc_citations(nodes):

    nodes = nodes[nodes["citationCount_cumulative_prop"] < 0.5]

    nodes['title'] = nodes.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)

    return nodes[["title", "citationCount", "degree"]]

def main():

    nodes, links = build_graph_from_bibliography(sys.argv[1])
    
    cynodes, cylinks = build_cytoscape(nodes, links)

    nodes, links = pd.DataFrame(nodes), pd.DataFrame(links)

    nodes_by_degree = get_publications_by_degree(nodes, links)
    nodes_by_citation = get_publications_by_citations(nodes, links)
    nodes_top_50_perc_citations = get_publications_top_50_perc_citations(nodes_by_citation)
    nodes_by_citation["index"] = nodes_by_citation.index

    app = Dash(__name__, external_stylesheets=['/assets/style.css'])

    app.layout = html.Div([
        dcc.Markdown([
            "# Literature Review Graph",
            # TODO Some reporting on which paperIds errored
            f"Input bibliography: {sys.argv[1]} ({nodes['group'].sum()} publications)",
            f"## Graph metrics:",
            f"Number of connected publications: {len(nodes)}  ",
            f"Number of connections: {len(links)}",
            f"## Graph explorer:",
        ]),
        html.Div([
            cyto.Cytoscape(
                id='cytoscape',
                elements=cynodes + cylinks,
                layout={'name': 'cose'},
                style={'width': '80%', 'height': '600px'},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            "width": "mapData(citationCountLog, 0, 100, 0.01, 100)",
                            "height": "mapData(citationCountLog, 0, 100, 0.05, 100)",
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            "width": 0.2,
                        }
                    },
                    {
                        'selector': 'node',
                        'style': {
                            'background-color': 'mapData(group, 0, 1, blue, red)'
                        }
                    }
                ]
            ),
            html.Div(id='node-info',
                     style={'width': '20%', 'height': '600px', 'overflow': 'auto', 'line-height': '1.2'}),
        ], style={'display': 'flex'}),
        dcc.Markdown([
            "## Publications by degree:",
            "Publications not present in the bibliography that have the most connections to other publications",
        ]),
        CitationTable(nodes_by_degree),
        dcc.Markdown([
            "## Publications by citation count:",
        ]),
        dcc.Graph(
            id='graph-citation-count',
            figure=px.scatter(nodes_by_citation, 
                            x="index", 
                            y="citationCount_cumulative", 
                            color="group",
                            color_discrete_map={0: "blue", 1: "red"},
                            hover_data={
                                "citationCount_cumulative": False,
                                "group": False,
                                "index": False,
                                "title": True,
                                "citationCount": True,
                                "degree": True,
                            }
                            ).update_layout(
                                showlegend=False, 
                                plot_bgcolor='white',
                                xaxis_title="Publication",
                                yaxis_title="Cumulative citation count"
                            ).add_vline(
                                x=nodes_top_50_perc_citations.index[-1], line_width=1, line_dash="dash", line_color="red"
                            )
        ),
        dcc.Markdown([
            f"These {nodes_top_50_perc_citations.shape[0]} papers constitute 50% of the citations in this network (*shown by red dashed line*):",
        ]),
        CitationTable(nodes_top_50_perc_citations),
        dcc.Markdown([
            "Created by [Hamish Gibbs](https://github.com/hamishgibbs). Publication data from [Semantic Scholar](https://www.semanticscholar.org/).",
        ])
    ])

    @app.callback(Output('node-info', 'children'),
                  Input('cytoscape', 'tapNodeData'))
    def display_node_data(data):
        if data is None:
            return "Click a publication to display its information"

        content = [
            dcc.Link(data["title"], href=data["url"], target='_blank', style={'color': 'blue', 'text-decoration': 'underline'}),
            dcc.Markdown(f"{data['author_names']}"),
            dcc.Markdown(f"*Published: {data['journal']} ({data['year']})*"),
            dcc.Markdown(f"*Cited by: {data['citationCount']}*")
        ]

        if data["tldr"]:
            content.append(dcc.Markdown(f"*[Summary](https://github.com/allenai/scitldr): {data['tldr']['text']}*"))
        
        if data["DOI"]:
            content.append(dcc.Markdown(f"*DOI: {data['DOI']}*"))

        return content

    app.run_server(debug=True)

if __name__ == '__main__':
    main()