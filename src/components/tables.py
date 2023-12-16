from dash import dash_table
import pandas as pd

def format_nodes_for_bibliography_table(nodes):
    """Format nodes for the table listing publications in this bibliography"""
    
    nodes = pd.DataFrame(nodes)
    nodes = nodes[nodes["group"] == 1]
    nodes["title"] = nodes.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)
    nodes["author_names"] = nodes.apply(
        lambda row: ", ".join(row["author_names"]), axis=1
    )
    nodes.sort_values(["citationCount"], ascending=False, inplace=True)

    return nodes[["title", "year", "author_names", "citationCount"]]

def BibiliographyTable(df, id):
    return dash_table.DataTable(
        id=id,
        columns=[
            {
                "name": "Title",
                "id": "title",
                "type": "text",
                "presentation": "markdown",
            },
            {
                "name": "Year",
                "id": "year",
            },
            {
                "name": "Authors",
                "id": "author_names",
            },
            {
                "name": "Citations",
                "id": "citationCount",
            },
        ],
        data=df.to_dict("records"),
        style_cell={"textAlign": "left"},
        page_action="native",
        page_size=5,
        style_cell_conditional=[
            {
                "if": {"column_id": "title"},
                "maxWidth": "500px",
                "overflow": "auto",
                "textOverflow": "ellipsis",
            },
            {
                "if": {"column_id": "author_names"},
                "maxWidth": "150px",
                "overflow": "auto",
            },
        ],
        style_header={"fontWeight": "bold", "fontFamily": "Arial"},
    )

def get_publications_by_degree(nodes, links):
    """format nodes for the table listing publications by degree"""

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
    """format nodes for the table listing publications by citation count"""

    nodes = nodes.sort_values(["citationCount"], ascending=False).reset_index()

    nodes["citationCount_cumulative"] = np.cumsum(nodes["citationCount"])
    nodes["citationCount_cumulative_prop"] = nodes["citationCount_cumulative"] / np.sum(
        nodes["citationCount"]
    )

    return nodes


def get_publications_top_50_perc_citations(nodes):
    """format nodes for the table listing publications making up the 50% of citations"""

    nodes = nodes.copy(deep=True)

    if min(nodes["citationCount_cumulative_prop"]) > 0.5:
        nodes = nodes.iloc[0:1]
    else:
        nodes = nodes[nodes["citationCount_cumulative_prop"] < 0.5]

    nodes["title"] = nodes.apply(lambda row: f"[{row['title']}]({row['url']})", axis=1)

    return nodes[["title", "citationCount", "degree"]]

def CitationTable(df, id):
    return dash_table.DataTable(
        id=id,
        columns=[
            {
                "name": "Title",
                "id": "title",
                "type": "text",
                "presentation": "markdown",
            },
            {
                "name": "Citations",
                "id": "citationCount",
            },
            {
                "name": "Degree",
                "id": "degree",
            },
        ],
        data=df.to_dict("records"),
        style_cell={"textAlign": "left"},
        page_action="native",
        page_size=5,
        style_cell_conditional=[
            {
                "if": {"column_id": "title"},
                "maxWidth": "500px",
                "overflow": "auto",
                "textOverflow": "ellipsis",
            }
        ],
        style_header={"fontWeight": "bold", "fontFamily": "Arial"},
    )
