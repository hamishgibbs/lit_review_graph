from dash import dash_table

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
