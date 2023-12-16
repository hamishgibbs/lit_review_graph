import sys
from datetime import datetime
import requests_cache
import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto
import plotly.express as px
import logging

from components.tables import (
    BibiliographyTable, 
    CitationTable, 
    format_nodes_for_table
)
from db import (
    initialize_database,
    get_all_bibliographies,
    create_bibliography,
    delete_bibliography
)
from get_metadata import build_graph

logging.basicConfig(filename="app.log", level=logging.INFO, filemode="w")

def build_graph_from_bibliography(bibliography): # TODO: bibliography_name
    """Builds nodes and links from a bibliography of DOIs"""

    session = requests_cache.CachedSession("lit_review_graph_cache")

    # TODO: remove this, bibliography a query of DOIs from the db
    with open(bibliography) as f:
        bibliography = f.readlines()

    bibliography = [f"DOI:{citation.strip()}" for citation in bibliography]

    return build_graph(session, bibliography)


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


def get_publications_by_degree(nodes, links):

    node_ids = [x for x in nodes["paperId"]]

    for node in node_ids:
        node_degree = len(links[links["source"] == node]) + len(
            links[links["target"] == node]
        )
        nodes.loc[nodes["paperId"] == node, "degree"] = node_degree

    nodes = nodes.sort_values(["degree", "citationCount"], ascending=False)
    nodes = nodes[nodes["group"] == 0]

    nodes["title"] = nodes.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)

    return nodes[["title", "citationCount", "degree"]]


def get_publications_by_citations(nodes, links):

    nodes = nodes.sort_values(["citationCount"], ascending=False).reset_index()

    nodes["citationCount_cumulative"] = np.cumsum(nodes["citationCount"])
    nodes["citationCount_cumulative_prop"] = nodes["citationCount_cumulative"] / np.sum(
        nodes["citationCount"]
    )

    return nodes


def get_publications_top_50_perc_citations(nodes):

    nodes = nodes.copy(deep=True)

    if min(nodes["citationCount_cumulative_prop"]) > 0.5:
        nodes = nodes.iloc[0:1]
    else:
        nodes = nodes[nodes["citationCount_cumulative_prop"] < 0.5]

    nodes["title"] = nodes.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)

    return nodes[["title", "citationCount", "degree"]]


def main():

    # Initialize db
    # list_bibliographies()
    # Wait for a bibliography to be selected? 
    db_path = sys.argv[1]
    initialize_database(db_path)

    # Query first bibliograph in db
    # This will have to become state
    bibliographies = get_all_bibliographies(db_path)

    nodes, links = build_graph_from_bibliography("data/bibliography_bias.txt")
    print("")

    cynodes, cylinks = build_cytoscape(nodes, links)

    nodes, links = pd.DataFrame(nodes), pd.DataFrame(links)

    nodes_by_degree = get_publications_by_degree(nodes, links)
    nodes_by_citation = get_publications_by_citations(nodes, links)
    nodes_top_50_perc_citations = get_publications_top_50_perc_citations(
        nodes_by_citation
    )
    nodes_by_citation["index"] = nodes_by_citation.index

    app = Dash(
        __name__, external_stylesheets=["/assets/style.css", dbc.themes.BOOTSTRAP]
    )

    app.title = "Literature Review Graph"

    app.layout = html.Div(
        [
            html.Link(rel="icon", href="/assets/favicon.ico"),
            dcc.Markdown(
                [
                    "# 📕 Literature Review Graph",
                    # TODO Some reporting on which paperIds errored
                    f"Local database: {sys.argv[1]}",
                ]
            ),
            html.Div([
                dcc.Markdown("## Bibliographies:"),
                dbc.Button("Add", id="add-bibliography", n_clicks=0),
            ]),
            dbc.Modal([
                dbc.ModalHeader("Add bibliography"),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Name"),
                            dbc.Input(type="text", id="input-bibliography-name"),
                        ])
                ]),
                ]),
                dbc.ModalFooter(
                    dbc.Button("Save", id="save-bibliography", className="ml-auto")
                )
            ], id="modal-bibliography"),
            html.Div([
                dbc.Row([
                    dbc.Col(bib[1], width='auto'),
                    dbc.Col(dbc.Button("Select", id={'type': 'load-bib', 'index': bib[0]}), width='auto'),
                    dbc.Col(dbc.Button("Delete", id={'type': 'delete-bib', 'index': bib[0]}), width='auto')
                ]) for bib in bibliographies
            ], style={'width': '300px', 'overflowY': 'scroll', 'height': '500px'}),
            dcc.Markdown("## Bibliography:"),
            BibiliographyTable(format_nodes_for_table(nodes), "table-bibliography"),
            dcc.Markdown(
                [
                    f"## Graph metrics:",
                    f"Number of connected publications: {len(nodes)}  ",
                    f"Number of connections: {len(links)}",
                    f"## Graph explorer:",
                ]
            ),
            html.Div(
                [
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
                    ),
                    dbc.Toast(
                        [html.P("This is the content of the toast", className="mb-0")],
                        id="node-info",
                        header="Publication information",
                        style={
                            "width": "30%",
                            "height": "600px",
                            "overflow": "auto",
                            "line-height": "1.2",
                        },
                    ),
                ],
                style={"display": "flex"},
            ),
            dcc.Markdown(
                [
                    "## Publications by degree:",
                    "Publications not present in the bibliography that have the most connections to other publications",
                ]
            ),
            CitationTable(nodes_by_degree, "table-degree"),
            dcc.Markdown(
                [
                    "## Publications by citation count:",
                ]
            ),
            dcc.Graph(
                id="graph-citation-count",
                figure=px.scatter(
                    nodes_by_citation,
                    x="index",
                    y="citationCount_cumulative",
                    color="group",
                    color_discrete_map={
                        0: "rgb(199, 206, 219)",
                        1: "rgb(84, 101, 255)",
                    },
                    hover_data={
                        "citationCount_cumulative": False,
                        "group": False,
                        "index": False,
                        "title": True,
                        "citationCount": True,
                        "degree": True,
                    },
                )
                .update_layout(
                    showlegend=False,
                    plot_bgcolor="white",
                    xaxis_title="Publication",
                    yaxis_title="Cumulative citation count",
                )
                .add_vline(
                    x=nodes_top_50_perc_citations.index[-1],
                    line_width=1,
                    line_dash="dash",
                    line_color="red",
                )
                .update_yaxes(
                    range=[
                        0,
                        nodes_by_citation["citationCount_cumulative"].max() * 1.01,
                    ]
                ),
            ),
            dcc.Markdown(
                [
                    f"These {nodes_top_50_perc_citations.shape[0]} papers constitute 50% of the citations in this network (*shown by red dashed line*):",
                ]
            ),
            CitationTable(nodes_top_50_perc_citations, "table-citation-count"),
            dcc.Markdown(
                [
                    "Created by [Hamish Gibbs](https://github.com/hamishgibbs). Publication data from [Semantic Scholar](https://www.semanticscholar.org/).",
                ]
            ),
        ]
    )

    @app.callback(Output("node-info", "children"), Input("cytoscape", "tapNodeData"))
    def display_node_data(data):
        if data is None:
            return "Click a publication to display its information"

        content = [
            dcc.Link(
                data["title"],
                href=data["url"],
                target="_blank",
                style={"color": "blue", "text-decoration": "underline"},
            ),
            dcc.Markdown(f"{data['author_names']}"),
            dcc.Markdown(f"*Published: {data['journal']} ({data['year']})*"),
            dcc.Markdown(f"*Cited by: {data['citationCount']}*"),
        ]

        if data["tldr"]:
            content.append(
                dcc.Markdown(
                    f"*[Summary](https://github.com/allenai/scitldr): {data['tldr']['text']}*"
                )
            )

        if data["DOI"]:
            content.append(dcc.Markdown(f"*DOI: {data['DOI']}*"))

        return content

    @app.callback(
        Output("modal-bibliography", "is_open"),
        [Input("add-bibliography", "n_clicks"), Input("save-bibliography", "n_clicks")],
        [State("modal-bibliography", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        Output('save-bibliography', 'n_clicks'),
        Input('save-bibliography', 'n_clicks'),
        [State('modal-bibliography', 'is_open'), State('input-bibliography-name', 'value')]
    )
    def save_bibliography(n, is_open, name_value):
        if n:
            mtime = datetime.now().timestamp()
            create_bibliography(db_path, name_value, mtime)
            logging.info(f"Created bibliography: {name_value}, {mtime}")
        return n

    @app.callback(
        Output('output-container', 'children'),
        [Input({'type': 'load-bib', 'index': ALL}, 'n_clicks'),
        Input({'type': 'delete-bib', 'index': ALL}, 'n_clicks')]
    )
    def handle_click(*args):
        ctx = callback_context

        if not ctx.triggered:
            return "No bibliography selected"

        button_id = ctx.triggered[0]['prop_id']
        if 'load-bib' in button_id:
            bib_name = button_id.split('"')[3]
            return f"Loading {bib_name}"
        elif 'delete-bib' in button_id:
            bib_name = button_id.split('"')[3]
            # Add logic to delete bibliography
            return f"Deleted {bib_name}"

    debug = "--debug" in sys.argv

    app.run_server(debug=debug)


if __name__ == "__main__":
    main()
