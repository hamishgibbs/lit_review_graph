suppressPackageStartupMessages({
  library(networkD3)
  library(data.table)
  library(ggplot2)
  library(igraph)
})

data(MisLinks)
data(MisNodes)

MisNodes

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
  "Reference Network.html"
)

subset(nodes, id == 325)

View(links[, .(n_citations = .N), by = c("target")][order(-n_citations)])
n_citations <- links[, .(n_citations = .N), by = c("source")][order(-n_citations)]
n_citations[, prop_citations := n_citations / sum(n_citations)]

ggplot(data = n_citations) + 
  geom_path(aes(x = 1:length(n_citations), y = cumsum(prop_citations)))

nodes[, prop_citations := `is-referenced-by-count` / sum(`is-referenced-by-count`)]

ggplot(nodes[order(-`is-referenced-by-count`)]) + 
  geom_path(aes(x = 1:length(`is-referenced-by-count`), y = cumsum(prop_citations)))

g <- igraph::graph_from_data_frame(links)

clust <- igraph::cluster_infomap(g)

n_nodes <- data.table(clust$membership)[, .(n_nodes = .N), by = c("V1")][order(-n_nodes)]

ggplot(n_nodes) + 
  geom_path(aes(x = 1:length(n_nodes), y = n_nodes), stat="identity")

vertices <- data.table(get.data.frame(g, what="vertices"))

vertices$cluster <- clust$membership

nodes[vertices, on=c("paperId"="name"), membership := cluster]

n_nodes[1:4]

ggplot(subset(nodes, membership %in% 1:4)[order(-`is-referenced-by-count`)]) + 
  geom_path(aes(x = 1:length(`is-referenced-by-count`), y = `is-referenced-by-count`, 
                color=as.character(membership)))


fwrite(subset(nodes, membership %in% 1:4)[order(-`is-referenced-by-count`)][, head(.SD, 5), by = c("membership")],
          "~/Downloads/top_citations_per_cluster.csv")


