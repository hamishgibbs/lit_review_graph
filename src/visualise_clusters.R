# check out citation distribution in each cluster X
# sample (with seed) n papers from each cluster
# find the most highly cited papers in each cluster
# could make a static map of the module network (not the paper network itself)


suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
})

nodes <- fread("output/nodes.csv")
nodes[, id := .I]

links <- fread("output/infomap/links.csv", col.names = c("source", "target"))

communities <- fread("output/infomap/links.clu", skip = 10, col.names = c("node_id", "module", "flow"))

nodes[communities, on = c("id" = "node_id"), module := module]

nodes_ordered <- nodes[order(module, -citationCount)][, module_order := 1:length(citationCount), by = c("module")]

ggplot(nodes_ordered) + 
  geom_path(aes(x = module_order, y = citationCount,
                color=as.character(module))) + 
  scale_y_continuous(trans="log10") + 
  scale_x_continuous(trans="log10")

fwrite(nodes_ordered[,.SD[sample(.N, min(5,.N))],by = "module"][, c("module", "title")], "output/infomap/module_title_sample.csv")

fwrite(subset(nodes_ordered, module_order %in% 1:5)[, c("module", "title")], "output/infomap/module_title_top_cited.csv")

links[nodes, on = c("source"="id"), source_module := module]
links[nodes, on = c("target"="id"), target_module := module]

module_network <- links[, .(strength = .N), by = c("source_module", "target_module")]

module_network <- subset(module_network, source_module != target_module)
n_nodes_per_module <- nodes[, .(n_nodes = .N), by = c("module")]
n_nodes_per_module[, module := as.character(module)]

library(ggraph)
library(tidygraph)

graph <- as_tbl_graph(highschool) %>% 
  mutate(Popularity = centrality_degree(mode = 'in'))

graph <- as_tbl_graph(module_network)

graph <- graph %>% 
  activate(nodes) %>% 
  left_join(n_nodes_per_module, by = c("name" = "module"))

set.seed(1)
ggraph(graph, layout = 'fr') + 
  geom_edge_fan(aes(alpha = after_stat(index)), show.legend = FALSE) + 
  geom_node_label(aes(label = name, size = n_nodes, color=name)) + 
  theme_graph(foreground = 'steelblue', fg_text_colour = 'white')  
