suppressPackageStartupMessages({
  library(networkD3)
  library(data.table)
})

data(MisLinks)
data(MisNodes)

MisNodes

nodes <- fread("output/nodes.csv")
nodes$group <- 1
links <- fread("output/links.csv")

nodes[, id := .I - 1]

node_ids <- nodes$id
names(node_ids) <- nodes$doi

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
  forceNetwork(Links = links_degree_gt1, Nodes = nodes_degree_gt1,
               Source = "source_numeric", Target = "target_numeric",
               NodeID = "id",
               Group = "group", 
               bounded = T,
               zoom = T,
               charge = -50,
               opacity = 0.8),
  "Reference Network.html"
)


