import requests
import time
import subprocess
import logging
import yaml

# ---------------- Load Config ---------------- #
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

PROM_URL = config["prometheus"]["url"]
SCRAPE_INTERVAL = config["prometheus"]["scrape_interval"]
THRESHOLD = config["thresholds"]["cpu_mem_diff_percent"]

SERVERS = config["servers"]
INSTANCES = config["instances"]

NGINX_CONF_PATH = config["nginx"]["config_path"]
ACCESS_LOG = config["nginx"]["access_log"]
ERROR_LOG = config["nginx"]["error_log"]

rr_index = 0

metrics_cache = {
    vm: {"cpu": 0.0, "mem": 0.0} for vm in SERVERS
}

# ---------------- Logging ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ---------------- Prometheus Queries ---------------- #
CPU_QUERY = """
100 - avg by (instance) (
  irate(node_cpu_seconds_total{mode="idle"}[5s])
) * 100
"""

MEM_QUERY = """
(1 - (
  node_memory_MemAvailable_bytes
  /
  node_memory_MemTotal_bytes
)) * 100
"""

# ---------------- Prometheus Query ---------------- #
def query_prometheus(query):
    try:
        r = requests.get(PROM_URL, params={"query": query}, timeout=2)
        r.raise_for_status()
        results = r.json()["data"]["result"]
        return {i["metric"]["instance"]: float(i["value"][1]) for i in results}
    except Exception as e:
        logger.error(f"Prometheus query failed: {e}")
        return {}

# ---------------- Metric Collection ---------------- #
def collect_metrics():
    cpu_data = query_prometheus(CPU_QUERY)
    mem_data = query_prometheus(MEM_QUERY)

    for vm, instance in INSTANCES.items():
        metrics_cache[vm]["cpu"] = cpu_data.get(instance, 0.0)
        metrics_cache[vm]["mem"] = mem_data.get(instance, 0.0)

    logger.info(f"Metrics updated: {metrics_cache}")

# ---------------- Backend Selection ---------------- #
def select_backends():
    global rr_index

    vms = list(metrics_cache.keys())
    vm1, vm2 = vms[0], vms[1]

    cpu_diff = abs(metrics_cache[vm1]["cpu"] - metrics_cache[vm2]["cpu"])
    mem_diff = abs(metrics_cache[vm1]["mem"] - metrics_cache[vm2]["mem"])

    # STATIC Round Robin
    if cpu_diff < THRESHOLD and mem_diff < THRESHOLD:
        servers_list = list(SERVERS.values())
        rr_index += 1
        logger.info("STATIC mode: round-robin")
        return servers_list

    # DYNAMIC Least Load
    scores = {
        vm: metrics_cache[vm]["cpu"] + metrics_cache[vm]["mem"]
        for vm in metrics_cache
    }

    selected_vm = min(scores, key=scores.get)
    logger.info(f"DYNAMIC mode: selected {selected_vm}")
    return [SERVERS[selected_vm]]

# ---------------- Generate NGINX Config ---------------- #
def generate_nginx_config(backends):
    lines = ["upstream backend_pool {"]

    for backend in backends:
        lines.append(f"    server {backend};")

    lines.append("}")

    lines.append(f"""
server {{
    listen 80 default_server;
    server_name _;

    access_log {ACCESS_LOG};
    error_log {ERROR_LOG};

    location / {{
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_pass http://backend_pool;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
""")
    return "\n".join(lines)

# ---------------- Update NGINX ---------------- #
def update_nginx(backends):
    config_data = generate_nginx_config(backends)

    with open(NGINX_CONF_PATH, "w") as f:
        f.write(config_data)

    try:
        subprocess.run(["nginx", "-s", "reload"], check=True)
        logger.info("Nginx reloaded successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Nginx reload failed: {e}")

# ---------------- Main Loop ---------------- #
def main():
    while True:
        collect_metrics()
        backends = select_backends()
        update_nginx(backends)
        time.sleep(SCRAPE_INTERVAL)

if __name__ == "__main__":
    main()
