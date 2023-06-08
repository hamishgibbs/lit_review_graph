# Literature Review Graph

Explore your bibliography as a network and find important papers you could have missed.

## Overview

How many times have you come across an important, highly cited paper and thought: "How could I have missed this??"

`lit_review_graph` is an attempt to find those papers by looking at the papers referenced by the papers you reference.

`lit_review_graph` is similar to [ResearchRabbit](https://researchrabbitapp.com/home) or [Connected Papers](https://www.connectedpapers.com/) but runs locally and displays the complete reference network for the papers in your bibliography.

## Usage

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

Run the app and point it to your bibliography:

```
python src/app.py bibliography.txt
```

## Limitations

`lit_review_graph` searches all of the references of papers in your bibliography and will struggle with a large network. I recommend dividing your references into small groups (5-10 publications) for the most clarity.

When adding a new paper, `lit_review_graph` may take some time to query the metadata for each of the connected references from [Semantic Scholar](https://www.semanticscholar.org/). Requests are cached in `lit_review_graph_cache.sqlite` and start-up will be faster when you re-run the app.

[Semantic Scholar](https://www.semanticscholar.org/) is a great free source of information on the academic citation network but data for some papers (particularly older papers) may be missing or incomplete. 