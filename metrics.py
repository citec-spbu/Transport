#!/usr/bin/env python3
import json
import os
import sys
from neo4j import GraphDatabase

# === Настройки подключения ===
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

# === Аргумент — тип узлов ===
if len(sys.argv) < 2:
    print("Использование: python3 metrics.py <node_type>")
    print("Пример: python3 metrics.py BusStop")
    sys.exit(1)

node_type = sys.argv[1]
metric_field = "pageRank"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# === Запрос ===
query = f"""
MATCH (n:`{node_type}`)
WHERE n.location IS NOT NULL
RETURN elementId(n) AS id,
       n.name AS name,
       n.location AS loc,
       coalesce(n.{metric_field}, 0.0) AS metric
"""

nodes = []
metrics = []

with driver.session(database=DATABASE) as session:
    result = session.run(query)
    for rec in result:
        loc = rec["loc"]
        if not loc:
            continue
        lat, lon = loc.y, loc.x
        metric = float(rec["metric"]) if rec["metric"] is not None else 0.0
        nodes.append({
            "id": rec["id"],
            "name": rec["name"],
            "lat": lat,
            "lon": lon,
            "metric": metric
        })
        metrics.append(metric)

driver.close()

if not nodes:
    print("Нет узлов с координатами.")
    sys.exit(1)

# === Нормализация ===
min_m, max_m = min(metrics), max(metrics)
span = max_m - min_m if max_m != min_m else 1.0
for n in nodes:
    n["norm"] = (n["metric"] - min_m) / span

sorted_nodes = sorted(nodes, key=lambda x: x["metric"], reverse=True)

# === Генерация HTML ===
def generate_html(nodes, metric_field, output_html=f"heatmap_{metric_field}.html"):
    sorted_for_map = sorted(nodes, key=lambda x: x["metric"])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Heatmap - {metric_field}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html, body {{margin:0; padding:0; height:100%;}}
  #map {{width:100%; height:100%;}}
  .legend {{
      position: absolute;
      bottom: 20px;
      left: 20px;
      background: #ffffff !important;
      padding: 8px 12px;
      border-radius: 6px;
      box-shadow: 0 0 8px rgba(0,0,0,0.2);
      font-family: sans-serif;
      opacity: 1 !important;
      font-size: 12px;
      z-index: 9999;
      mix-blend-mode: normal !important;
  }}
  .legend .bar {{
      width: 150px;
      height: 10px;
      background: linear-gradient(to right, #0011ff, #00ffff, #ffff00, #ff7b00, #ff0000);
      border-radius: 4px;
      margin-top: 4px;
  }}
</style>
</head>
<body>
<div id="map"></div>
<div class="legend">
  <div><b>{metric_field}</b></div>
  <div class="bar"></div>
  <div style="display:flex; justify-content:space-between;">
    <span>Low</span><span>High</span>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const nodes = {json.dumps(sorted_for_map, ensure_ascii=False)};

function getColor(v) {{
  const c = [
    [0.0, [0,17,255]],
    [0.25,[0,255,255]],
    [0.5, [255,255,0]],
    [0.75,[255,123,0]],
    [1.0,[255,0,0]]
  ];
  for (let i = 1; i < c.length; i++) {{
    if (v <= c[i][0]) {{
      const [r1,g1,b1] = c[i-1][1];
      const [r2,g2,b2] = c[i][1];
      const t = (v - c[i-1][0]) / (c[i][0]-c[i-1][0]);
      const r = Math.round(r1 + (r2-r1)*t);
      const g = Math.round(g1 + (g2-g1)*t);
      const b = Math.round(b1 + (b2-b1)*t);
      return `rgb(${{r}},${{g}},${{b}})`;
    }}
  }}
  return "rgb(255,0,0)";
}}

const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    maxZoom: 18,
    opacity: 0.65,
    attribution: '© OpenStreetMap, © CartoDB'
}}).addTo(map);

const markers = [];
nodes.forEach(n => {{
  const color = getColor(n.norm);
  const m = L.circleMarker([n.lat, n.lon], {{
    radius: 6,
    fillColor: color,
    color: color,
    weight: 0.3,
    opacity: 0.9,
    fillOpacity: 0.9
  }}).bindPopup(`<b>${{n.name}}</b><br>{metric_field}: ${{n.metric.toFixed(5)}}`);
  m.addTo(map);
  markers.push(m);
}});

const group = L.featureGroup(markers);
map.fitBounds(group.getBounds());
</script>
</body>
</html>"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Карта сохранена в {output_html}")


def generate_histogram(sorted_nodes, metric_field, output_html=f"{metric_field}_histogram.html"):
    # sorted_nodes — список всех узлов, отсортированных по убыванию metric (или любым образом)
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{metric_field} Histogram (Window)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body {{ font-family: sans-serif; margin: 18px; background:#fafafa; }}
  h2 {{ text-align:center; }}
  #controls {{ display:flex; gap:12px; align-items:center; justify-content:center; margin-bottom:10px; }}
  #chart-box {{ width:100%; height:70vh; }}
  canvas {{ width:100%; height:100%; }}
  .small {{ font-size:12px; color:#555; }}
  button {{ padding:6px 10px; border-radius:4px; border:1px solid #ccc; background:white; cursor:pointer; }}
  input[type=range] {{ width:400px; }}
</style>
</head>
<body>
<h2>Гситограмма по метрике {metric_field} </h2>

<div id="controls">
  <div class="small">Окно: <span id="win-size-label">50</span> столбцов</div>
  <input id="win-size" type="range" min="5" max="200" value="50" step="1" />
  <div class="small">Смещение: <span id="start-label">0</span></div>
  <input id="start" type="range" min="0" max="0" value="0" step="1" />
  <button id="left">&larr;</button>
  <button id="right">&rarr;</button>
  <button id="reset">Сброс</button>
</div>

<div id="chart-box"><canvas id="chart"></canvas></div>

<script>
const allData = {json.dumps(sorted_nodes, ensure_ascii=False)};
const labelsAll = allData.map(d => d.name);
const valuesAll = allData.map(d => d.metric);
const normsAll = allData.map(d => d.norm);

// цветовая функция 
function getColor(vNorm) {{
  const c = [
    [0.0, [0,17,255]],
    [0.25,[0,255,255]],
    [0.5, [255,255,0]],
    [0.75,[255,123,0]],
    [1.0,[255,0,0]]
  ];
  for (let i = 1; i < c.length; i++) {{
    if (vNorm <= c[i][0]) {{
      const [r1,g1,b1] = c[i-1][1];
      const [r2,g2,b2] = c[i][1];
      const t = (vNorm - c[i-1][0]) / (c[i][0]-c[i-1][0]);
      const r = Math.round(r1 + (r2-r1)*t);
      const g = Math.round(g1 + (g2-g1)*t);
      const b = Math.round(b1 + (b2-b1)*t);
      return `rgb(${{r}},${{g}},${{b}})`;
    }}
  }}
  return "rgb(255,0,0)";
}}

// константы Y
const maxValue = Math.max(...valuesAll);
const yMax = maxValue * 1.05;

// элементы управления
const winSizeInput = document.getElementById('win-size');
const winSizeLabel = document.getElementById('win-size-label');
const startInput = document.getElementById('start');
const startLabel = document.getElementById('start-label');
const leftBtn = document.getElementById('left');
const rightBtn = document.getElementById('right');
const resetBtn = document.getElementById('reset');

const ctx = document.getElementById('chart').getContext('2d');

// начальные параметры окна
let windowSize = parseInt(winSizeInput.value, 10);
let startIndex = 0;
const total = labelsAll.length;

// установить лимит для стартового варианта
startInput.max = Math.max(0, total - windowSize);
startInput.value = 0;
startLabel.textContent = 0;
winSizeLabel.textContent = windowSize;

// функция для получения данных окна
function getWindowData(start, size) {{
  const end = Math.min(total, start + size);
  const labels = labelsAll.slice(start, end);
  const values = valuesAll.slice(start, end);
  const norms = normsAll.slice(start, end);
  const colors = norms.map(n => getColor(n));
  return {{ labels, values, colors }};
}}

// инициализация графика с первым окном
let windowData = getWindowData(startIndex, windowSize);
let chart = new Chart(ctx, {{
  type: 'bar',
  data: {{
    labels: windowData.labels,
    datasets: [{{
      label: '{metric_field}',
      data: windowData.values,
      backgroundColor: windowData.colors,
      borderColor: '#444',
      borderWidth: 0.4
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    scales: {{
      x: {{
        ticks: {{
          autoSkip: true,
          maxRotation: 60,
          minRotation: 0,
          font: {{ size: 10 }}
        }}
      }},
      y: {{
        beginAtZero: true,
        min: 0,
        max: yMax,
        title: {{ display: true, text: '{metric_field}' }}
      }}
    }},
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        callbacks: {{
          label: function(ctx) {{
            return ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(6);
          }}
        }}
      }}
    }}
  }}
}});

// обновить график функцией (перерисовка)
function updateChart(start, size) {{
  const d = getWindowData(start, size);
  chart.data.labels = d.labels;
  chart.data.datasets[0].data = d.values;
  chart.data.datasets[0].backgroundColor = d.colors;
  chart.update();
}}

// обработчики
winSizeInput.addEventListener('input', (e) => {{
  windowSize = parseInt(e.target.value, 10);
  winSizeLabel.textContent = windowSize;
  // скорректировать старт, если нужно
  startInput.max = Math.max(0, total - windowSize);
  if (startIndex > startInput.max) {{
    startIndex = startInput.max;
    startInput.value = startIndex;
    startLabel.textContent = startIndex;
  }}
  updateChart(startIndex, windowSize);
}});

startInput.addEventListener('input', (e) => {{
  startIndex = parseInt(e.target.value, 10);
  startLabel.textContent = startIndex;
  updateChart(startIndex, windowSize);
}});

leftBtn.addEventListener('click', () => {{
  startIndex = Math.max(0, startIndex - Math.max(1, Math.floor(windowSize/4)));
  startInput.value = startIndex;
  startLabel.textContent = startIndex;
  updateChart(startIndex, windowSize);
}});

rightBtn.addEventListener('click', () => {{
  startIndex = Math.min(total - windowSize, startIndex + Math.max(1, Math.floor(windowSize/4)));
  startInput.value = startIndex;
  startLabel.textContent = startIndex;
  updateChart(startIndex, windowSize);
}});

resetBtn.addEventListener('click', () => {{
  windowSize = Math.min(50, total);
  startIndex = 0;
  winSizeInput.value = windowSize;
  winSizeLabel.textContent = windowSize;
  startInput.max = Math.max(0, total - windowSize);
  startInput.value = startIndex;
  startLabel.textContent = startIndex;
  updateChart(startIndex, windowSize);
}});

// пользователь может также прокручивать колесо мыши над контролом для шага смещения
document.getElementById('controls').addEventListener('wheel', (e) => {{
  e.preventDefault();
  const delta = Math.sign(e.deltaY);
  // колесо вниз — вправо, вверх — влево
  startIndex = Math.min(Math.max(0, startIndex + delta * Math.max(1, Math.floor(windowSize/10))), total - windowSize);
  startInput.value = startIndex;
  startLabel.textContent = startIndex;
  updateChart(startIndex, windowSize);
}});
</script>
</body>
</html>"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Гистограмма сохранена в {output_html}")

# === Генерация обоих файлов ===
generate_html(nodes, metric_field)
generate_histogram(sorted_nodes, metric_field)

