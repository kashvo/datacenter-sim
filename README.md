# datacenter-sim
Scalable multi-user login load testing framework — Locust + FastAPI + Prometheus + Grafana, built to simulate millions of concurrent users.
# Data Centre Login Load Simulation Framework

> A scalable, open-source framework for simulating real-world multi-user login
> traffic against a server — built to test how authentication systems behave
> under realistic ramp-up, peak, and sustained concurrency conditions, from
> hundreds to millions of users.

![Python](https://img.shields.io/badge/python-3.11-blue)
![Locust](https://img.shields.io/badge/load%20testing-locust-brightgreen)
![FastAPI](https://img.shields.io/badge/server-fastapi-009688)
![Docker](https://img.shields.io/badge/infra-docker-2496ED)
![Prometheus](https://img.shields.io/badge/monitoring-prometheus-E6522C)
![Grafana](https://img.shields.io/badge/dashboards-grafana-F46800)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## What this is

Most server load tests send flat, constant traffic — but real production traffic
ramps up, spikes, sustains, and cools down, often through multiple interfaces at
once. This framework reproduces that realism for a **login/authentication
endpoint**, one of the most concurrency-sensitive parts of any system.

It simulates a **login storm** — thousands (or millions) of fake users logging in
within a short window — while monitoring the target server live and automatically
identifying the exact point where it starts to break down.

---

## Architecture

```
                    ┌─────────────────┐
                    │  workload_profiles/
                    │  login_storm.yaml │  ← defines user count, ramp/peak/cooldown
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   Locust          │  ← simulates fake login traffic
                    │ (master + workers)│     scales horizontally
                    └────────┬─────────┘
                             │ HTTP requests
                    ┌────────▼─────────┐
                    │  FastAPI server   │  ← /login /logout /me /health /metrics
                    │   (test target)   │
                    └────────┬─────────┘
                             │ metrics
          ┌──────────────────┼──────────────────┐
          ▼                                       ▼
   ┌─────────────┐                       ┌──────────────┐
   │ Prometheus  │──────────────────────▶│   Grafana    │
   │ + Node Exp. │     live dashboards   │  dashboards   │
   └─────────────┘                       └──────────────┘
          │
          ▼
   ┌─────────────────────┐
   │ analysis/analyse.py  │ ← Pandas: bottleneck detection,
   │ → PDF report          │   SLA verdict, charts
   └─────────────────────┘
```

---

## Tech stack

| Layer | Tools |
|---|---|
| Language & config | Python 3.11, YAML, Git |
| Test target server | FastAPI, Uvicorn |
| Load generation | Locust (distributed master/worker) |
| Infrastructure | Docker, Docker Compose |
| Monitoring | Prometheus, Node Exporter, Grafana |
| Analysis & reporting | Pandas, Matplotlib, Seaborn, WeasyPrint |

All tools are 100% open source — zero licensing cost.

---

## Folder structure

```
datacenter-sim/
├── app/                     # FastAPI login server
│   ├── main.py              # /login /logout /me /health /metrics
│   ├── Dockerfile
│   └── requirements.txt
├── simulation/               # Locust load generation
│   ├── locustfile.py
│   └── loadshapes.py         # ramp-up / peak / cooldown curves
├── infra/                     # Infrastructure
│   ├── docker-compose.yml
│   └── prometheus.yml
├── monitoring/                # Grafana dashboards
│   └── dashboards/*.json
├── analysis/                  # Analysis & reporting
│   ├── analyse.py
│   └── reports/
├── workload_profiles/         # Test scenario configs
│   └── login_storm.yaml
├── docs/                       # Whitepaper, diagrams, notes
├── .gitignore
└── README.md
```

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/yourname/datacenter-sim.git
cd datacenter-sim
pip install -r app/requirements.txt
```

### 2. Start the full stack

```bash
cd infra
docker-compose up --build
```

This starts: the FastAPI login server, Locust master + workers, Prometheus,
Node Exporter, and Grafana — all on one Docker network.

### 3. Open the dashboards

| Service | URL |
|---|---|
| FastAPI server | http://localhost:8000 |
| Locust UI | http://localhost:8089 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

### 4. Run a test

```bash
python simulation/run_test.py --profile workload_profiles/login_storm.yaml
```

### 5. Scale up workers (for higher simulated user counts)

```bash
docker-compose up --scale locust-worker=4
```

### 6. Generate the report

```bash
python analysis/analyse.py --run results/latest.csv
```

Outputs a PDF report to `analysis/reports/` with latency/throughput charts,
bottleneck detection, and an SLA pass/fail verdict.

---

## Scalability approach

"Scalable to millions of users" is achieved architecturally, not by literally
running a million-user test on a laptop:

- **Config-driven scale** — `target_users` in the YAML profile controls the
  entire test; changing one number changes scale.
- **Locust distributed mode** — one master coordinates many worker nodes, each
  generating load independently.
- **Horizontal scaling** — `docker-compose up --scale locust-worker=N` adds
  capacity without code changes.
- **Bottleneck identification** — analysis identifies the exact ceiling (CPU,
  DB connections, thread pool, etc.) that limits scale, and what to fix to go higher.

---

## SLA thresholds (default)

| Metric | Threshold |
|---|---|
| p95 login latency | < 500ms |
| Error rate | < 1% |
| CPU utilisation | < 80% |
| Memory utilisation | < 90% |

Configurable in `workload_profiles/login_storm.yaml`.

---

## Team

| Role | Responsibility |
|---|---|
| App developers (2) | FastAPI login server |
| Simulation developer (1) | Locust load generation, scaling |
| Monitoring & analysis (3) | Docker infra, Grafana dashboards, bottleneck tuning, reporting |

---

## License

MIT — free to use, modify, and distribute.
