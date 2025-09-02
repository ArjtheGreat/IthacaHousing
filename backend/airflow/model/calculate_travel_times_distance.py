import networkx as nx
import osmnx as ox
import shapely
from shapely import MultiLineString


uris_lat, uris_lon = 42.4475, -76.4836

def get_graph_and_uris_node(mode, dist, uris_lat, uris_lon):
    """
    Creates graph from ithaca street network and identifies connections from starting node to uris
    """
    G = ox.graph_from_point((uris_lat, uris_lon), dist=dist, network_type=mode)

    speed_kph = {'walk': 3.5, 'bike': 10, 'drive': 25}[mode]
    for u, v, k, data in G.edges(keys=True, data=True):
        data["speed_kph"] = speed_kph
    G = ox.add_edge_travel_times(G)

    uris_node = ox.distance.nearest_nodes(G, uris_lon, uris_lat)
    return G, uris_node

def compute_all_travel_times(apartments_for_rent,  dist=2000):
    """
    Computes travel times for all three modes using OSMNX
    """
    for mode in ['walk', 'bike', 'drive']:
        print(f"Processing mode: {mode}")
        G, uris_node = get_graph_and_uris_node(mode, dist, uris_lat, uris_lon)
        times = []
        routes = []

        apartment_nodes = ox.distance.nearest_nodes(G, apartments_for_rent['longitude'], apartments_for_rent['latitude'])

        for apt_node in apartment_nodes:
            try:
                route = nx.shortest_path(G, apt_node, uris_node, weight="travel_time")
                G_proj = ox.project_graph(G)
                route_gdf = ox.routing.route_to_gdf(G_proj, route)
                route_gdf = route_gdf.to_crs("EPSG:4326")
                lines = list(route_gdf["geometry"])

                multi_line = MultiLineString(lines)

                merged_line = shapely.line_merge(multi_line)
  
                time_min = sum(G[u][v][k]["travel_time"] for u, v, k in zip(route[:-1], route[1:], [0]*len(route)))
                if mode == "drive":
                    time_min *= 1.8
                times.append(round(time_min / 60, 2))
                routes.append(merged_line)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                times.append(None)
                routes.append(None)  # Add None to routes list to match length

        apartments_for_rent[f"{mode}_time"] = times
        apartments_for_rent[f"{mode}_routes"] = routes

    return apartments_for_rent