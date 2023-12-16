from dash import dash_table
import pandas as pd

def format_nodes_for_table(nodes):
    
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
