import json
import os
import sys
import random
import colorsys
from neo4j import GraphDatabase

def distinct_random_color():
    # Генерируем равномерно распределенные оттенки
    hue = random.random()  # 0.0 - 1.0
    saturation = 0.7 + random.random() * 0.3  # 70-100%
    lightness = 0.4 + random.random() * 0.3  # 40-70%

    rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgb[0] * 255),
        int(rgb[1] * 255),
        int(rgb[2] * 255)
    )

# === Чтение конфигурации ===
CONFIG_PATH = "config.json"

if not os.path.exists(CONFIG_PATH):
    print(f"Конфигурационный файл {CONFIG_PATH} не найден. Создайте файл с параметрами подключения.")
    sys.exit(1)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

URI = config.get("uri", "neo4j://localhost:7687")
USER = config.get("user", "neo4j")
PASSWORD = config.get("password", "neo4j")
DATABASE = config.get("database", "neo4j")

AUTH = (USER, PASSWORD)

DEBUG = config.get("debug", False)

def log_debug(msg):
    if DEBUG:
        print(msg)

# === Проверка аргументов ===
if len(sys.argv) < 3:
    print("Использование: python3 clusterization.py <relation_type> <node_type>")
    print("Например: python3 clusterization.py БирскBusRouteSegment БирскBusStop")
    sys.exit(1)

relation_type = sys.argv[1]
node_type = sys.argv[2]

driver = GraphDatabase.driver(URI, auth=AUTH)

def point_to_geojson(point):
    if not point:
        return None
    return {"type": "Point", "coordinates": [point.x, point.y]}

# === Запрос ===
query = f"""
MATCH (a:`{node_type}`)-[r:`{relation_type}`]->(b:`{node_type}`)
RETURN 
    elementId(a) AS id_a,
    a.name AS name_a,
    a.location AS loc_a,
    a.leiden_community AS leiden_a,
    elementId(b) AS id_b,
    b.name AS name_b,
    b.location AS loc_b,
    b.leiden_community AS leiden_b,
    r.name AS rel_name,
    r.duration AS duration,
    r.route AS route
"""

features_nodes = {}
features_links = []
colors_by_community = {}  # чтобы одинаковые сообщества были одного цвета

with driver.session(database=DATABASE) as session:
    result = session.run(query)
    for record in result:
        id_a = record["id_a"]
        id_b = record["id_b"]
        loc_a = record["loc_a"]
        loc_b = record["loc_b"]

        leiden_a = record["leiden_a"]
        leiden_b = record["leiden_b"]

        # --- Цвет для каждого сообщества ---
        if leiden_a not in colors_by_community:
            colors_by_community[leiden_a] = distinct_random_color()
        if leiden_b not in colors_by_community:
            colors_by_community[leiden_b] = distinct_random_color()

        color_a = colors_by_community[leiden_a]
        color_b = colors_by_community[leiden_b]

        # --- Узлы ---
        if id_a not in features_nodes and loc_a:
            features_nodes[id_a] = {
                "type": "Feature",
                "geometry": point_to_geojson(loc_a),
                "properties": {
                    "id": id_a,
                    "name": record["name_a"],
                    "leiden_community": leiden_a,
                    "color": color_a,
                    "popup": f"<div style='background-color:white; color:black; padding:5px; border-radius:4px; font-family:sans-serif; font-size:12px;'><b>{record['name_a']}</b><br>Community: {leiden_a}</div>"
                }
            }
        if id_b not in features_nodes and loc_b:
            features_nodes[id_b] = {
                "type": "Feature",
                "geometry": point_to_geojson(loc_b),
                "properties": {
                    "id": id_b,
                    "name": record["name_b"],
                    "leiden_community": leiden_b,
                    "color": color_b,
                    "popup": f"<div style='background-color:white; color:black; padding:5px; border-radius:4px; font-family:sans-serif; font-size:12px;'><b>{record['name_b']}</b><br>Community: {leiden_b}</div>"
                }
            }

        # --- Связи ---
        if loc_a and loc_b:
            features_links.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [loc_a.x, loc_a.y],
                        [loc_b.x, loc_b.y]
                    ]
                },
                "properties": {
                    "name": record["rel_name"],
                    "duration": record["duration"],
                    "route": record["route"]
                }
            })

driver.close()

# === Два отдельных GeoJSON ===
geojson_nodes = {
    "type": "FeatureCollection",
    "features": list(features_nodes.values())
}

geojson_links = {
    "type": "FeatureCollection",
    "features": features_links
}

if DEBUG:
    file_nodes = f"nodes_{node_type}.geojson"
    file_links = f"links_{relation_type}.geojson"

    with open(file_nodes, "w", encoding="utf-8") as f:
        json.dump(geojson_nodes, f, ensure_ascii=False, indent=2)

    with open(file_links, "w", encoding="utf-8") as f:
        json.dump(geojson_links, f, ensure_ascii=False, indent=2)

log_debug("Узлы сохранены в файл nodes.geojson")

if DEBUG:
    print("Цвета сообществ:")
    for k, v in colors_by_community.items():
        print(f"  Community {k}: {v}")


# === Генерация HTML-файла ===
def generate_leaflet_html_inline(nodes_data, links_data, output_html="clusterization_map.html"):
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Neo4j Graph Map</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const nodesData = {json.dumps(nodes_data, ensure_ascii=False)};
        const linksData = {json.dumps(links_data, ensure_ascii=False)};

        const map = L.map('map').setView([0, 0], 2);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        const nodesLayer = L.geoJSON(nodesData, {{
            pointToLayer: function(feature, latlng) {{
                const color = feature.properties.color || '#000000';
                return L.circleMarker(latlng, {{
                    radius: 8,
                    fillColor: color,
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }});
            }},
            onEachFeature: function(feature, layer) {{
                if (feature.properties.popup) {{
                    layer.bindPopup(feature.properties.popup);
                }}
            }}
        }}).addTo(map);

        const linksLayer = L.geoJSON(linksData, {{
            style: {{ color: 'gray', weight: 1.5, opacity: 0.6 }}
        }}).addTo(map);

        const group = new L.featureGroup([...nodesLayer.getLayers(), ...linksLayer.getLayers()]);
        map.fitBounds(group.getBounds());
    </script>
</body>
</html>
"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    log_debug(f"Карта сохранена в {output_html}")

# === В конце скрипта вызываем функцию ===
generate_leaflet_html_inline(geojson_nodes, geojson_links)