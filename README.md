# lit_review_graph

Explore your bibliography as a network and find important papers you could have missed.

#### Description

Do you ever come accross an important, highly cited paper and think: "How could I have missed this?"

It is often difficult to identify. 

### Usage

Create a text file with a series of DOIs:

`bibliography.txt`
```
10.1038/s41586-020-2909-1
10.1140/epjds/s13688-015-0059-8
10.1038/nature06958
10.1038/nature04292
10.1038/srep00457
10.1093/infdis/jiw273
10.1126/science.286.5439.509
```

Run the app and point it towards you bibliography:

```
python src/app.py data/bibliography.txt
```

### Limitations

`lit_review_graph` searches all of the references of the "seed" publications and will struggle with a large bibliography. I recommend dividing your references into small groups (5-10 publications) for the most clarity.

When adding a new paper, `lit_review_graph` may take some time to query the metadata for each of the connected references [Semantic Scholar](https://www.semanticscholar.org/). Requests are cached in `lit_review_graph_cache.sqlite` and start-up will be faster when you re-run the app.

[Semantic Scholar](https://www.semanticscholar.org/) is a great free source of clean information on the academic citation network but data for some papers (particularly older papers) may be missing or incomplete. 

### Other solutions

`lit_review_graph` is similar to [ResearchRabbit](https://researchrabbitapp.com/home) or [Connected Papers](https://www.connectedpapers.com/) but displays all of the references of papers in your bibliography and runs locally.