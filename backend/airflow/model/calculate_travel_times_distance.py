import networkx as nx
import osmnx as ox
import shapely
from shapely import MultiLineString
import geopandas as gpd
import shapely
from shapely.geometry import Point

CAMPUS_POINTS = [
    {"name": "Uris Hall",        "lat": 42.4472,   "lon": -76.4822 },
    {"name": "Agriculture Quad", "lat": 42.448796, "lon": -76.478018},
    {"name": "Arts Quad",        "lat": 42.448966, "lon": -76.484175},
    {"name": "Engineering Quad", "lat": 42.444668, "lon": -76.482570},
]

def build_graphs(dist=2000, center_lat=42.4472, center_lon=-76.4822):
    """
    Builds graphs using NetworkX for different modes (walk, bike, drive)
    """
    modes = ["walk", "bike", "drive"]
    graphs = {}

    for mode in modes:
        try:
            print(f"Building base {mode} graph…")
            G = ox.graph_from_point((center_lat, center_lon), dist=dist, network_type=mode)
            speed_kph = {'walk': 3.5, 'bike': 10, 'drive': 25}[mode]
            for _, _, _, data in G.edges(keys=True, data=True):
                data["speed_kph"] = speed_kph
            G = ox.add_edge_travel_times(G)
            graphs[mode] = G
        except Exception as e:
            print(f"⚠️ Failed to build {mode} graph: {e}")
            graphs[mode] = None
    return graphs


def compute_all_travel_times(apartments_for_rent, graphs):
    """
    Iterates through each mode graph and for each reference point calculates the time for each mode from each apartment 
    """
    for mode, G in graphs.items():
        if G is None:
            print(f"⚠️ No {mode} graph available — skipping.")
            continue

        print(f"\n🚶‍♂️ Processing mode: {mode}")

        try:
            valid_mask = apartments_for_rent["longitude"].notna() & apartments_for_rent["latitude"].notna()
            apartment_nodes = ox.distance.nearest_nodes(
                G,
                apartments_for_rent.loc[valid_mask, "longitude"],
                apartments_for_rent.loc[valid_mask, "latitude"]
            )
        except Exception as e:
            print(f"⚠️ Failed to map apartment nodes for {mode}: {e}")
            continue

        for ref in CAMPUS_POINTS:
            ref_name = ref["name"].replace(" ", "").lower() 
            ref_lat, ref_lon = ref["lat"], ref["lon"]
            print(f"  → Computing travel times to {ref['name']}")

            try:
                ref_node = ox.distance.nearest_nodes(G, ref_lon, ref_lat)
            except Exception as e:
                print(f"⚠️ Could not find {ref['name']} node: {e}")
                apartments_for_rent[f"{mode}_time_{ref_name}"] = [None]*len(apartments_for_rent)
                continue

            times = [None] * len(apartments_for_rent)
            
            valid_indices = apartments_for_rent.index[valid_mask]
            for i, apt_node in enumerate(apartment_nodes):
                try:
                    time_min = nx.shortest_path_length(G, apt_node, ref_node, weight="travel_time") / 60
                    if mode == "drive":
                        time_min *= 1.8
                    pos = apartments_for_rent.index.get_loc(valid_indices[i])
                    times[pos] = round(time_min, 2)
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    pos = apartments_for_rent.index.get_loc(valid_indices[i])
                    times[pos] = None
                except Exception as e:
                    print(f"❌ Failed route to {ref['name']}: {e}")
                    pos = apartments_for_rent.index.get_loc(valid_indices[i])
                    times[pos] = None

            apartments_for_rent[f"{mode}_time_{ref_name}"] = times

    return apartments_for_rent


def make_isochronic_map(apartments_for_rent):
    """
    Makes 15 and 30 minute isochronic maps for apartment listings
    """
    G_city = ox.graph_from_place("City of Ithaca, New York, USA", network_type="walk")
    G_town = ox.graph_from_place("Town of Ithaca, New York, USA", network_type="walk")

    G_walk = nx.compose(G_city, G_town)

    for u, v, data in G_walk.edges(data=True):
        data["travel_time"] = data["length"] / 1.3

    def make_isochrone(G, center_node, cutoff=900): 
        subgraph = nx.ego_graph(G, center_node, radius=cutoff, distance="travel_time")
        nodes = [ (G.nodes[n]['x'], G.nodes[n]['y']) for n in subgraph.nodes() ]
        polygon = shapely.geometry.MultiPoint(nodes).convex_hull
        return polygon

    isochrones = []
    for _, row in apartments_for_rent.iterrows():
        center_node = ox.distance.nearest_nodes(G_walk, row["longitude"], row["latitude"])
        poly15 = make_isochrone(G_walk, center_node, cutoff=900)
        isochrones.append({"id": row["ListingId"], "iso15": poly15})

    iso_df = gpd.GeoDataFrame(isochrones, geometry="iso15", crs="EPSG:4326")

    apartments_for_rent = apartments_for_rent.merge(iso_df, left_on="ListingId", right_on="id")
    
    apartments_for_rent['iso15'] = apartments_for_rent['iso15'].apply(
        lambda x: gpd.GeoSeries([x], crs="EPSG:4326").to_json() if x is not None else None
    )
    
    return apartments_for_rent