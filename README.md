# Lightning Network Measurements

This repository contains a reproducible Python pipeline for refreshing measurements from:

> Empirical Evaluation of Nodes and Channels of the Lightning Network

The pipeline is intentionally snapshot-oriented: feed it a recent Lightning public graph export, and it produces CSV/JSON summaries plus plots for the requested metrics.

## Project Scope

The project currently supports:

- LND `describegraph` JSON snapshots
- node implementation inference
- channel implementation-pair distribution
- public channel capacity distribution when capacity data is present
- graph metrics with NetworkX
- degree and centrality outputs
- optional node geolocation enrichment
- optional channel lifetime estimates from repeated snapshots

Important limitation: public Lightning graph data does not reveal true channel balances. It can expose public channel capacity, but not the current balance split between channel endpoints.

## Supported Inputs

Primary input:

- `lncli describegraph` exported to `data/raw/describegraph-<DATE>.json`

Optional inputs:

- `--node-geo-csv data/raw/node_geo.csv`: keyed by `pub_key`, with any of `country_code`, `country_name`, `continent`, `city`, `latitude`, `longitude`.
- `--history-dir data/raw/history`: dated graph snapshots named with a `YYYYMMDD` or `YYYY-MM-DD` token. This enables observed channel lifetimes across snapshots.
- `--current-block-height <height>`: computes current-channel age from the `short_channel_id` block height when historical close data is unavailable.

The graph loader currently targets LND `describegraph` JSON. It also accepts compact normalized files with top-level `nodes` and `edges`.

## Repository Structure

```text
lightning_measurements/
  README.md
  LND_FIRST_TIME_SETUP.md
  PROJECT_DOCUMENTATION.md
  requirements.txt
  pyproject.toml
  examples/
    sample_describegraph.json
  src/
    ln_measurements/
      cli.py
      io.py
      classify.py
      metrics.py
      plots.py
```

Generated data is intentionally ignored by Git:

```text
data/raw/
outputs/
```

This keeps large raw graph snapshots and reproducible outputs outside normal version control.

## Setup From A Fresh Machine

Choose a local project folder:

```powershell
$PROJECT_DIR = "C:\Users\<your-username>\Documents\lightning-research"
```

Clone or copy this repository into:

```text
<PROJECT_DIR>\lightning_measurements
```

Go into the project:

```powershell
cd "$PROJECT_DIR\lightning_measurements"
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Install dependencies using the virtual environment Python:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Test the package with sample data:

```powershell
$env:PYTHONPATH="$PROJECT_DIR\lightning_measurements\src"

.\.venv\Scripts\python.exe -m ln_measurements.cli `
  --graph "$PROJECT_DIR\lightning_measurements\examples\sample_describegraph.json" `
  --out-dir "$PROJECT_DIR\lightning_measurements\outputs\sample-test" `
  --current-block-height 900000
```

Expected result:

```text
Wrote Lightning measurement outputs to ...
```

## Collect A Real LND Snapshot

Set up LND using the detailed guide:

```text
LND_FIRST_TIME_SETUP.md
```

After LND is synced, confirm:

```powershell
cd C:\lnd
.\lncli.exe getinfo
```

Continue only when:

```json
"synced_to_chain": true,
"synced_to_graph": true
```

Create a raw data folder:

```powershell
mkdir "$PROJECT_DIR\lightning_measurements\data\raw"
```

Set the snapshot date:

```powershell
$DATE = "YYYY-MM-DD"
```

Collect the graph:

```powershell
.\lncli.exe describegraph | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\describegraph-$DATE.json"
```

Save metadata:

```powershell
.\lncli.exe getinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\getinfo-$DATE.json"
```

```powershell
.\lncli.exe getnetworkinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\networkinfo-$DATE.json"
```

Copy the `block_height` value from:

```powershell
.\lncli.exe getinfo
```

## Run Analysis On Real Data

```powershell
cd "$PROJECT_DIR\lightning_measurements"
$env:PYTHONPATH="$PROJECT_DIR\lightning_measurements\src"

.\.venv\Scripts\python.exe -m ln_measurements.cli `
  --graph "$PROJECT_DIR\lightning_measurements\data\raw\describegraph-$DATE.json" `
  --out-dir "$PROJECT_DIR\lightning_measurements\outputs\$DATE" `
  --current-block-height <BLOCK_HEIGHT>
```

Replace `<BLOCK_HEIGHT>` with the value from `lncli getinfo`.

Optional arguments:

```powershell
--node-geo-csv "$PROJECT_DIR\lightning_measurements\data\raw\node_geo.csv"
--history-dir "$PROJECT_DIR\lightning_measurements\data\raw\history"
--exact-path-metrics
```

Missing geolocation data simply yields `unknown` geography buckets. Missing history means the pipeline reports channel age proxies rather than closed-channel lifetimes.
For large graphs, exact average-shortest-path computation is skipped unless you add `--exact-path-metrics`.

## Outputs

- `nodes_classified.csv`: node metadata, inferred implementation, confidence, policy defaults used.
- `implementation_distribution.csv`: inferred node implementation distribution.
- `geographic_distribution.csv`: country/continent buckets when geolocation is supplied.
- `channels.csv`: normalized channel table.
- `channel_pair_distribution.csv`: implementation-pair distribution by channel count and capacity.
- `capacity_distribution.csv`: descriptive stats and histogram buckets for channel capacity.
- `degree_distribution.csv`: node degree counts.
- `centrality.csv`: degree, betweenness, closeness, eigenvector approximation.
- `graph_metrics.json`: node/channel counts, density, components, clustering, path summaries.
- `channel_lifetimes.csv`: observed first/last-seen channel windows from historical snapshots, or age proxies.
- `plots/*.png`: quick visual checks for the main distributions.

## Notes On Implementation Inference

Lightning gossip does not directly reveal node implementation. The classifier follows the paper's default-parameter method:

- LND: color `#3399ff`, `cltv_expiry_delta` in `{40, 144}`, `htlc_minimum_msat = 1000`, `fee_proportional_millionths = 1`
- Core Lightning/C-Lightning: color derived from the first three bytes of `node_id`, `cltv_expiry_delta = 14`, `htlc_minimum_msat = 1000`, `fee_proportional_millionths = 10`
- Eclair: color `#49daaa`, `cltv_expiry_delta = 144`, `htlc_minimum_msat = 1`, `fee_proportional_millionths = 100`

The output includes a confidence score and leaves ties or no-signal nodes as `unknown`.
