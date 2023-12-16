import sys
import json
from datetime import datetime
import requests_cache
import numpy as np
import pandas as pd
from dash import Dash, html, dcc, callback_context, no_update
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import plotly.express as px
import logging

from components.network import (
    build_cytoscape,
    PublicationCytoscape
)
from components.tables import (
    BibiliographyTable, 
    CitationTable, 
    format_nodes_for_bibliography_table,
    get_publications_by_degree,
    get_publications_by_citations,
    get_publications_top_50_perc_citations
)
from db import (
    initialize_database,
    get_all_bibliographies,
    create_bibliography,
    delete_bibliography,
    get_dois_for_bibliography
)
from get_metadata import build_graph_from_bibliography

logging.basicConfig(filename="app.log", level=logging.INFO, filemode="w")

def main():

    # Initialize db
    db_path = sys.argv[1]
    initialize_database(db_path)

    # Set initial active_bibliography state to None (nothing has been selected)

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
            dcc.Store(id='active-bibliography', data=None),
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
                dbc.Button("New Bibliography", id="add-bibliography", n_clicks=0),
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
                html.Div([dbc.Button(bib[1], id= {'type': 'activate-bib', 'index': bib[0]}, n_clicks=0) for bib in bibliographies],
                         id="div-bibliography-buttons"),
            ]),
            html.Div(id='div-active-bibliography'),
            BibiliographyTable(format_nodes_for_bibliography_table(nodes), "table-bibliography"),
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
                    PublicationCytoscape(cynodes, cylinks),
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

    @app.callback(
        Output('active-bibliography', 'data'),
        [Input({'type': 'activate-bib', 'index': ALL}, 'n_clicks')]
    )
    def handle_click(*args):
        """Select an active bibliography with buttons"""
        # TODO: This could be extended to a delete-bib button with 
        # if 'delete-bib' in button_id:
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        else:
            button_id = ctx.triggered[0]['prop_id']
            bib_id = json.loads(button_id.split('.')[0])['index']
            
            dois = get_dois_for_bibliography(db_path, bib_id)
            bib_name = [bib[1] for bib in bibliographies if bib[0] == bib_id][0]
            
            if not dois:
                return {'bib_id': bib_id, 'bib_name': bib_name, 'nodes': [], 'links': []}
            else:
            # TODO: make active-bibliography data have bib_id, bib_name, nodes, links
            # the below will have to be changed to take a list of the DOIs in the bib
            # nodes, links = build_graph_from_bibliography("data/bibliography_bias.txt")
                return bib_id
        
    @app.callback(
        Output('div-active-bibliography', 'children'),
        Input('active-bibliography', 'data'),
    )
    def update_active_bibliography(data):
        """Placeholder to show selected active bibliography"""
        if data is None:
            return dcc.Markdown("No bibliography selected")
        else:
            return [
                dcc.Markdown(f"## {data['bib_name']} Publications:"),
                dbc.Button("Add Publication", id="add-publication", n_clicks=0),
                ]
    
    @app.callback(
        Output("modal-bibliography", "is_open"),
        [Input("add-bibliography", "n_clicks"), Input("save-bibliography", "n_clicks")],
        [State("modal-bibliography", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        """Toggle add bibliography modal open/closed"""
        if n1 or n2:
            return not is_open
        return is_open

    @app.callback(
        Output('div-bibliography-buttons', 'children'),
        Input('save-bibliography', 'n_clicks'),
        [State('modal-bibliography', 'is_open'), State('input-bibliography-name', 'value')]
    )
    def save_bibliography(n, is_open, name_value):
        if n:
            mtime = datetime.now().timestamp()
            create_bibliography(db_path, name_value, mtime)
            logging.info(f"Created bibliography: {name_value}, {mtime}")
            updated_bibliographies = get_all_bibliographies(db_path)
        return [dbc.Button(bib[1], id= {'type': 'activate-bib', 'index': bib[0]}, n_clicks=0) for bib in updated_bibliographies]

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

    debug = "--debug" in sys.argv

    app.run_server(debug=debug)


if __name__ == "__main__":
    main()
