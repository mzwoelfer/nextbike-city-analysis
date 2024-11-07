import pandas as pd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

ox.config(use_cache=True, log_console=False)

southwest_lat, southwest_lon = 50.52289, 8.60267
northeast_lat, northeast_lon = 50.63589, 8.74256

bbox = (northeast_lat, southwest_lat, northeast_lon, southwest_lon)
G = ox.graph_from_bbox(*bbox, network_type="bike")

fig, ax = ox.plot_graph(G, show=False, close=False, node_size=0.25)


trips = pd.read_csv("trips.csv")
for _, row in trips.iterrows():
    try:
        start_node = ox.distance.nearest_nodes(
            G, row["start_longitude"], row["start_latitude"]
        )
        end_node = ox.distance.nearest_nodes(
            G, row["end_longitude"], row["end_latitude"]
        )

        route = nx.shortest_path(G, start_node, end_node, weight="length")

        ox.plot_graph_route(
            G,
            route,
            ax=ax,
            route_linewidth=2,
            route_color="blue",
            orig_dest_size=3,
            node_size=0.5,
            bgcolor="white",
            show=False,
            close=False,
        )

    except Exception as e:
        print(
            f"Could not plot the route between nodes {start_node} and {end_node}: {e}"
        )

plt.savefig("giessen_minimal_route.png", dpi=300)
plt.show()
