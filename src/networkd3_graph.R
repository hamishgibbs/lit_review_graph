suppressPackageStartupMessages({
  library(networkD3)
  library(data.table)
  library(ggplot2)
  library(igraph)
})

nodes <- fread("output/nodes.csv")
links <- fread("output/links.csv")

nodes[, id := .I - 1]

node_ids <- nodes$id
names(node_ids) <- nodes$paperId

links$source_numeric <- as.numeric(node_ids[links$source])
links$target_numeric <- as.numeric(node_ids[links$target])

# why are there missing?
links <- links[!is.na(target_numeric)]

node_degree <- links[, .(degree = .N), by = c("target_numeric")]

links_degree_gt1 <- links[target_numeric %in% subset(node_degree, degree > 1)$target_numeric]

nodes_degree_gt1 <- subset(nodes, id %in% unique(c(links_degree_gt1$source_numeric, links_degree_gt1$target_numeric)))

nodes_degree_gt1[, id := .I - 1]

nodes_degree_gt1$id <- nodes_degree_gt1$id - min(nodes_degree_gt1$id)

node_ids <- nodes_degree_gt1$id
names(node_ids) <- nodes_degree_gt1$doi

links_degree_gt1$source_numeric <- as.numeric(node_ids[links_degree_gt1$source])
links_degree_gt1$target_numeric <- as.numeric(node_ids[links_degree_gt1$target])

networkD3::saveNetwork(
  forceNetwork(Links = links, Nodes = nodes,
               Source = "source_numeric", Target = "target_numeric",
               NodeID = "id",
               Group = "group", 
               bounded = T,
               zoom = T,
               charge = -50,
               opacity = 0.8),
  "output/networkD3/Reference Network.html"
)

subset(nodes, id %in% c(739, 904, 216))

g <- as_tbl_graph(links, directed = F)

g <- g %>% 
  activate(nodes) %>% 
  left_join(nodes, by = c("name" = "paperId")) %>% 
  mutate(degree = tidygraph::centrality_degree()) %>% 
  filter(degree > 1)

set.seed(1)
ggraph(g, layout = 'fr') + 
  geom_edge_fan(alpha=0.9) + 
  geom_node_point(aes(size = citationCount,
                      color = group), alpha = 0.2)

# What papers not in the bibliography have the highest degree?
top_degree <- g %>% 
  activate(nodes) %>% 
  filter(!group) %>% 
  arrange(-degree) %>% 
  pull(title)

# What are the highest citation papers not in the bibliography?
top_citation <- g %>% 
  activate(nodes) %>% 
  filter(!group) %>% 
  arrange(-citationCount) %>% 
  pull(title)

# What is the overlap in the top n of these? 
n <- 10
intersect(top_degree[1:n], top_citation[1:n])

# What is the effect on network density with the 
# removal of each of the references in the bibliography?
bibliography <- g %>% 
  activate(nodes) %>% 
  filter(group) %>% 
  pull(name)

density_contribution <- list()

graph_density <- g %>% activate(edges) %>% igraph::graph.density()
  
for (i in 1:length(bibliography)){
  paperId <- bibliography[i]
  density <- g %>% 
    activate(nodes) %>% 
    filter(name != paperId) %>% 
    activate(edges) %>% igraph::graph.density()
  density_contribution[[i]] <- data.frame(
    paperId,
    density,
    title = g %>% activate(nodes) %>% filter(name == paperId) %>% pull(title)
  )
}

density_contribution <- do.call(rbind, density_contribution)

ggplot(density_contribution) + 
  geom_bar(aes(x = title, y = density - graph_density), stat="identity") + 
  scale_x_discrete(labels = function(x) stringr::str_sub(x, start = 1, end = 30)) +
  theme(axis.text.x = element_text(angle = 80, hjust = 1))

# What contribution does each paper make to the total citations of the graph? 
View(nodes[order(-group, -citationCount)])

ggplot(nodes[order(-group, -citationCount)]) + 
  geom_point(aes(x = 1:length(group), y = cumsum(citationCount) / sum(citationCount), color=group)) + 
  scale_y_continuous(labels = scales::percent)



