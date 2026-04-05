# AI Engineering Labs

> CMU 17-445/17-645/17-745 Machine Learning in Production (MLIP) - Spring 2026
>
> 10 Hands-on Labs covering the full lifecycle of ML systems: from API integration, data streaming, version control, model testing, containerization, CI/CD, AI agent security, monitoring, pipeline versioning, to model explainability.

---

## Labs Overview

| Lab | Topic | Core Skills |
|-----|-------|-------------|
| [Lab 01](#lab-1-calling-building-and-securing-apis) | API Calling, Building & Security | LLM integration, REST API design, credential management |
| [Lab 02](#lab-2-kafka-for-data-streaming) | Kafka Data Streaming | Producer-Consumer model, topic/offset, kcat CLI |
| [Lab 03](#lab-3-git-version-control) | Git Version Control | Merge conflicts, PR workflow, revert vs reset |
| [Lab 04](#lab-4-model-testing-with-wb--llms) | Model Testing with W&B & LLMs | Data slicing, regression testing, synthetic stress tests |
| [Lab 05](#lab-5-containerizing-ml-models-with-docker) | Docker Containerization | Dockerfile, Docker Compose, volumes vs bind mounts |
| [Lab 06](#lab-6-continuous-integration-with-github-actions) | CI with GitHub Actions | Workflows, coverage thresholds, self-hosted runners |
| [Lab 07](#lab-7-building-and-securing-tool-calling-agents-with-mcp) | MCP Tool-Calling Agents & Security | MCP servers, tool calling, prompt injection attacks |
| [Lab 08](#lab-8-monitoring-with-prometheus--grafana) | Monitoring with Prometheus & Grafana | PromQL, dashboards, metrics collection |
| [Lab 09](#lab-9-data--pipeline-versioning-dvc--roar) | Data & Pipeline Versioning | DVC, Roar, reproducibility, experiment tracking |
| [Lab 10](#lab-10-explainability-with-alibi--shap) | Model Explainability | SHAP values, PD plots, anchor explanations, fairness |

---

## Lab 1: Calling, Building and Securing APIs

### What You Do

- Use a third-party LLM API (recommended: Groq-hosted Llama via LiteLLM) to generate a **structured JSON travel itinerary**
- Build a Flask web app exposing the endpoint `GET /api/v1/itinerary`, which accepts a `destination` parameter and returns JSON with `destination`, `price_range`, `ideal_visit_times`, and `top_attractions`
- Learn **credential security**: load API keys from environment variables or files instead of hardcoding, ensure secrets are never committed to Git
- Test the API endpoint using curl or Postman

### Key Concepts

- **RESTful API** design and invocation
- **LLM API** usage: LiteLLM library, structured JSON output, schema validation
- **Credential management**: environment variables, `.gitignore`, secret rotation, remediation after accidental leaks
- Flask web framework basics

### Deliverables

1. Invoke an LLM API and generate a schema-enforced JSON travel itinerary
2. Run the API endpoint with the LLM call and demonstrate it works
3. Commit code without credentials; explain why hardcoding credentials is dangerous

---

## Lab 2: Kafka for Data Streaming

### What You Do

- Establish an SSH tunnel to a remote Kafka server
- Implement **Producer** mode: write city data to a Kafka topic
- Implement **Consumer** mode: read messages from the broker and save to `kafka_log.csv`
- Use the CLI tool `kcat` to manage and monitor Kafka topics and messages
- (Optional) Preview movie log streams for the course group project

### Key Concepts

- Apache Kafka core concepts: **Topic**, **Offset**, **Broker**, **Partition**
- **Producer-Consumer model**: publish and subscribe to message streams
- `auto_offset_reset` parameter: `earliest` vs `latest` and their trade-offs
- How offsets ensure **message continuity** when a consumer disconnects and reconnects
- SSH tunneling for secure remote access

### Deliverables

1. Establish SSH tunnel; explain topics, offsets, and message continuity
2. Implement producer and consumer modes; explain `auto_offset_reset` trade-offs
3. Use `kcat` to manage and monitor Kafka topics

---

## Lab 3: Git Version Control

### What You Do

- **Exercise 1**: Create and resolve a **merge conflict** — make conflicting changes on two branches, merge, resolve, then `git commit --amend` the merge commit
- **Exercise 2**: Fork a repository, configure remotes (`origin` → your fork, `upstream` → original repo), push a branch, and open a **Pull Request**
- **Exercise 3**: Use `git revert` to safely roll back an intentional bad commit while preserving history

### Key Concepts

- Git **branching** (create, switch, merge)
- **Merge conflict** resolution
- `git commit --amend` to modify the most recent commit
- **Clone vs Fork**: clone copies the repo locally; fork creates a server-side copy under your account
- **Pull Request** workflow and its purpose in code review
- **Remote management**: `origin` vs `upstream`
- `git revert` (creates a new undo commit, preserves history) vs `git reset` (rewrites history) — when to use each
- `git log --oneline --graph --decorate` for visualizing branch history

### Deliverables

1. Create and fix a merge conflict, then amend the merge commit
2. Create a pull request; explain clone vs fork and why PRs are used
3. Demonstrate `git revert`; explain when revert is preferred over reset

---

## Lab 4: Model Testing with W&B & LLMs

### What You Do

- Run a candidate sentiment analysis model alongside a baseline model on tweet data
- Define **at least 5 hypothesis-driven data slices** (e.g., by hashtags, negation words, emoji density, unusual length, @mentions)
- Log results to **Weights & Biases (W&B)**: `df_long`, `slice_metrics`, `regression_metrics`, `df_eval`; build comparative visualizations
- Use an LLM to generate **10 targeted synthetic test tweets** to stress-test the model's weak slices
- Analyze why overall accuracy can be misleading

### Key Concepts

- **Model evaluation beyond accuracy**: slicing data to uncover hidden failure modes
- **Data slicing**: segmenting predictions by data properties to identify weak spots
- **Weights & Biases** platform: logging, tables, interactive visualizations
- **Regression testing**: comparing candidate model vs baseline to detect regressions
- **Synthetic data generation** with LLMs for targeted stress testing
- Deployment confidence assessment

### Deliverables

1. Run the pipeline and define at least 5 hypothesis-driven slices with explanations
2. Log to W&B; build visualizations; explain why accuracy can be misleading
3. Complete the LLM stress test; interpret results; discuss deployment confidence

---

## Lab 5: Containerizing ML Models with Docker

### What You Do

- Containerize an ML **training pipeline**: train a Wine classifier inside a Docker container, save the model to a **shared named volume**
- Containerize an **inference service**: serve predictions via Flask, persist logs to the host using a **bind mount** (`./logs/predictions.log`)
- Use **Docker Compose** to orchestrate both containers
- Demonstrate the effect of destroying the named volume on the inference service's health endpoint

### Key Concepts

- **Dockerfile** structure and purpose
- **Docker Compose** for multi-container orchestration
- **Named Volume vs Bind Mount**:
  - Named Volume: Docker-managed persistent storage for sharing data between containers
  - Bind Mount: maps a host directory into a container for direct file access (e.g., logs)
- Docker's value for **reproducibility and portability** in ML workflows
- Container data sharing patterns

### Deliverables

1. Train model in container, save to shared volume; explain Docker's value for ML reproducibility
2. Containerize inference service; show `predictions.log` on host; explain Dockerfile's role
3. Call health endpoint before/after destroying volume; explain named volumes vs bind mounts

---

## Lab 6: Continuous Integration with GitHub Actions

### What You Do

- Set up a GitHub Actions CI workflow with `pytest` and **coverage thresholds**
- Create a PR showing CI **failing** (coverage < 70%) and then **passing** (coverage >= 70%) after adding tests
- Add a CI step to run an **ML demo pipeline** that logs the model's R² score
- Configure a **self-hosted runner** on your own machine to execute CI jobs

### Key Concepts

- **CI/CD** concepts and their value in software quality
- **GitHub Actions** workflow syntax: `jobs`, `steps`, `runs-on`, triggers
- **Test coverage**: `pytest --cov`, `--cov-fail-under` thresholds
- When and whether enforcing coverage is useful
- **GitHub-hosted vs self-hosted runners**: trade-offs in cost, security, customization, and maintenance
- Why full-scale model training doesn't belong in CI (runtime and cost constraints)

### Deliverables

1. PR with failing and passing coverage checks; explain coverage enforcement value
2. Run workflow on self-hosted runner; explain hosted vs self-hosted differences
3. Run ML pipeline in CI; explain CI value for automated checks vs full training limitations

---

## Lab 7: Building and Securing Tool-Calling Agents with MCP

### What You Do

- Build an airline customer-service **agent** connected to a **Model Context Protocol (MCP)** server
- Extend the MCP server with two new tools:
  - `current_time`: returns current UTC time so the agent can handle time-dependent requests (e.g., "book a flight for tomorrow")
  - `airport_info`: retrieves airport information from Wikipedia
- Simulate an **indirect prompt injection attack** through the `airport_info` tool by returning malicious payloads, testing whether the agent follows injected instructions

### Key Concepts

- **MCP (Model Context Protocol)**: how agents discover, select, and invoke tools
- **Tool-calling agent** architecture and workflow
- **Indirect prompt injection**: injecting malicious instructions through external data sources (e.g., compromised Wikipedia content)
- Security risks of **untrusted data sources** and **malicious MCP servers**
- LLM defense capabilities and their limitations against injection attacks

### Deliverables

1. Extend MCP server with `current_time` and `airport_info`; demonstrate both solving previously impossible queries
2. Simulate indirect prompt injection; show whether agent followed or ignored the attack
3. Explain MCP tool-calling flow and key security considerations

---

## Lab 8: Monitoring with Prometheus & Grafana

### What You Do

- Deploy **Prometheus** and **Grafana** via Docker; configure **Node Exporter** for host-level metrics
- Implement HTTP **response status code counters** and **latency histograms** in `kafka-monitoring.py`
- Verify Prometheus targets and run **PromQL** queries
- Create a Grafana dashboard with **4 panels**:
  1. Total successful requests (status 200)
  2. Request rate over time (5-min window)
  3. Node CPU usage (system mode)
  4. 95th percentile request latency (P95)

### Key Concepts

- **Prometheus**: pull-based monitoring, time-series storage, counter reset handling
- **PromQL**: `rate()`, `histogram_quantile()`, metric aggregation
- **Grafana**: data source configuration, dashboard panel creation, visualization best practices
- **Node Exporter**: system-level metrics (CPU, memory, etc.)
- Metric aggregation across multiple service instances
- Monitoring's role in production ML systems

### Deliverables

1. Set up Docker with Prometheus/Grafana; implement status code and latency metrics
2. Verify targets; run PromQL queries; explain how Prometheus stores data and handles counter resets
3. Create 4-panel Grafana dashboard with clear labels; explain multi-instance aggregation

---

## Lab 9: Data & Pipeline Versioning (DVC & Roar)

### What You Do

- Use the Breast Cancer Wisconsin dataset (569 samples, 30 features) to train a Random Forest classifier
- **DVC (Data Version Control)**:
  - Define pipeline stages declaratively in `dvc.yaml` (preprocess → train → evaluate)
  - Version datasets and models alongside Git
  - Track and compare experiments with `dvc exp`
- **Roar (Run Observation & Artifact Registration)**:
  - Run code normally; Roar automatically infers the dependency DAG by observing file I/O
  - View artifact lineage on the GLaaS platform
- Run 2-3 experiments with different hyperparameters using both tools; compare results
- Fill in a comparison summary table and reflect on when to use each approach

### Key Concepts

- **Declarative vs Observational** pipeline management philosophies
- **DVC**: `dvc.yaml` pipeline definition, data versioning, experiment tracking, DAG visualization, selective re-execution (only re-run changed stages)
- **Roar**: automatic dependency inference, zero-config lineage tracking, artifact registration
- **Reproducibility**: different mechanisms for ensuring the same data + params → same model
- Team collaboration: `dvc.yaml` in Git vs lineage on GLaaS
- Data provenance: tracing which data and parameters produced a given model

### Deliverables

1. Show `dvc dag` and `roar dag` outputs plus GLaaS lineage
2. Run 2-3 experiments with both tools; demonstrate result comparison and provenance tracing
3. Complete summary table; discuss reflection questions with TA

---

## Lab 10: Explainability with Alibi & SHAP

### What You Do

- **Alibi Explain**:
  - Generate **Partial Dependence (PD) Plots** to analyze how individual features affect predictions
  - Examine feature importance rankings and interpret heatmaps
  - Run **Anchor Explanations** on image classification data to identify critical pixel regions
- **SHAP**:
  - Compute SHAP values to quantify each feature's contribution to predictions
  - Compare SHAP results with PD analysis for consistency
- Discuss whether the model's relied-upon features raise **fairness or bias concerns**

### Key Concepts

- **Global explainability**: which features matter most to the model overall
- **Local explainability**: what drives a specific individual prediction
- **Partial Dependence Plots**: how changing a feature's value affects the model output
- **Anchor Explanations**: finding sufficient conditions that "anchor" a prediction — if these conditions hold, the prediction is almost certain
- **SHAP values**: game-theoretic Shapley values quantifying each feature's marginal contribution
- **Black-box vs white-box** explanation methods
- **Fairness and bias** detection through feature analysis

### Deliverables

1. Complete all TODOs in the notebook; generate PD plots; discuss feature importance and heatmap findings
2. Run Anchor explanations on image data; discuss parameters and results
3. Complete SHAP comparison; identify strongest features; discuss fairness/bias concerns

---

## Course Context

These 10 labs cover the **full lifecycle of ML systems** in the CMU MLIP course:

```
API Integration → Data Streaming → Version Control → Model Testing
      ↓                                                    ↓
Containerization → CI/CD → Agent Security → Monitoring
      ↓                                        ↓
Pipeline Versioning    →    Model Explainability
```

The core philosophy: building production ML systems requires far more than model training — it demands robust engineering practices across APIs, data pipelines, testing, deployment, security, monitoring, versioning, and interpretability.
