# Lightning Network Measurement Reproduction: Project Documentation

## 1. Project Goal

The goal of this project is to reproduce and update measurements from the paper:

> Empirical Evaluation of Nodes and Channels of the Lightning Network

The original paper studied the Lightning Network using public topology and gossip information. Our goal is to collect recent Lightning Network data and compute similar measurements for a modern snapshot.

The target metrics are:

1. Node implementation distribution
2. Geographic distribution
3. Channel implementation-pair distribution
4. Channel balance/capacity distribution
5. Channel lifetime, if current or historical data allows
6. Network graph metrics:
   - node count
   - channel count
   - degree distribution
   - centrality
   - connected components
   - clustering

The preferred analysis stack is:

- Python
- pandas
- NetworkX
- matplotlib or plotly
- JSON and CSV outputs

## 2. Repository Exploration

We first explored the old repository:

```text
https://github.com/lnresearch/topology
```

This repository is not a complete reproduction package for the paper. It is mainly a toolkit for reading archived Lightning gossip datasets and reconstructing historical network topology snapshots.

### 2.1 Main Repository Structure

The main files and folders are:

```text
README.org
pyproject.toml
requirements.txt
setup.py
lntopo/
```

### 2.2 README.org

The README explains:

- Lightning gossip messages
- how data was collected
- the custom `.gsp.bz2` dataset format
- available historical datasets
- limitations of gossip data

The historical datasets are based on raw Lightning gossip messages collected from Core Lightning, formerly c-lightning.

### 2.3 lntopo/common.py

This file contains low-level readers.

Important classes:

- `DatasetStream`
  - Reads `.gsp` datasets.
  - Checks for the `GSP` file header.
  - Reads CompactSize-prefixed raw gossip messages.

- `DatasetFile`
  - Click command-line adapter.
  - Supports `.bz2` compressed dataset files.

- `GossipStore`
  - Reads a Core Lightning `gossip_store` file.
  - Streams raw gossip messages from the local node database.

This is useful for historical replay and raw gossip parsing.

### 2.4 lntopo/parser.py

This file parses BOLT 7 gossip messages.

It supports:

- `channel_announcement`
- `channel_update`
- `node_announcement`

Important parsed fields include:

- channel short ID
- node public keys
- channel direction
- node alias
- node color
- node addresses
- CLTV delta
- HTLC minimum
- HTLC maximum
- base fee
- proportional fee
- timestamp

This is useful because the paper inferred node implementations partly from public node and policy defaults.

### 2.5 lntopo/timemachine.py

This file reconstructs a historical Lightning graph by replaying gossip messages.

Main command:

```bash
lntopo-cli timemachine restore DATASET TIMESTAMP --fmt json
```

It:

- replays gossip messages up to a timestamp
- keeps latest node announcements and channel updates
- removes outdated channels based on a two-week cutoff
- builds a NetworkX directed graph
- exports graph formats such as DOT, GML, GraphML, or JSON

This is useful for reconstructing historical topology from archived gossip datasets.

### 2.6 lntopo/__main__.py

This file defines the CLI interface.

Main commands:

- `timemachine restore`
- `nodes trace`
- `messages parse`

The `nodes trace` command extracts messages related to one node from a Core Lightning `gossip_store`.

The `messages parse` command parses one raw hex-encoded gossip message.

## 3. What The Old Repository Does Not Provide

The old repository does not provide a full measurement pipeline for our target metrics.

It does not directly compute:

- node implementation distribution
- geographic distribution
- channel implementation-pair distribution
- capacity distribution tables
- centrality tables
- paper-style plots
- daily snapshot comparison
- channel lifetime from repeated modern snapshots

It also does not include a live 2026 data collector.

The old repository is best reused for:

- historical gossip replay
- parsing archived gossip messages
- understanding the old data collection method
- comparison with older Lightning snapshots

For our 2026 reproduction, we decided to build a modern analysis pipeline around current graph snapshots.

## 4. Data Collection Options Considered

We considered several ways to collect data.

### 4.1 Option A: LND describegraph

Command:

```powershell
lncli describegraph
```

This returns the public Lightning graph known by an LND node.

It includes:

- nodes
- public channels
- node aliases
- node colors
- public addresses
- channel policies
- channel fees
- CLTV settings
- HTLC settings
- channel capacity, depending on backend and graph state

This was selected as the easiest starting method.

Advantages:

- one command
- JSON output
- easy to parse with Python
- works well with pandas and NetworkX
- enough for most topology metrics

Limitations:

- it is one node's view of the public graph
- it does not reveal private channels
- it does not reveal real channel balances
- with our Neutrino setup, capacity values came out as zero

### 4.2 Option B: Core Lightning listnodes/listchannels

Commands:

```bash
lightning-cli listnodes
lightning-cli listchannels
```

This is also useful and may expose graph data from Core Lightning.

Advantages:

- direct Core Lightning graph view
- channel policies are separated by direction
- compatible with the old repository's collection philosophy

Limitations:

- requires setting up Core Lightning
- still does not expose private channel balances

### 4.3 Option C: Core Lightning gossip_store

Core Lightning stores raw gossip messages in `gossip_store`.

Advantages:

- closest to old `lnresearch/topology` approach
- useful for historical reconstruction from the time collection starts
- captures raw gossip messages

Limitations:

- more engineering effort
- needs continuous collection
- only provides history after collection begins

### 4.4 Option D: Third-Party APIs

Examples:

- Amboss
- public Lightning explorers

Advantages:

- easy access
- useful for cross-checking results
- may provide enriched metadata

Limitations:

- rate limits
- API terms
- less transparent methodology
- not ideal as the primary academic dataset

### 4.5 Final Choice

We selected:

```text
LND describegraph snapshots
```

Reason:

It is the simplest practical way to collect current public Lightning graph data and begin the reproduction study.

## 5. Local Project Pipeline Created

We created a new self-contained folder:

```text
lightning_measurements/
```

The important files are:

```text
lightning_measurements/
  README.md
  PROJECT_DOCUMENTATION.md
  requirements.txt
  pyproject.toml
  examples/
    sample_describegraph.json
  src/
    ln_measurements/
      __init__.py
      cli.py
      io.py
      classify.py
      metrics.py
      plots.py
```

### 5.1 README.md

Explains:

- supported inputs
- how to install dependencies
- how to run the pipeline
- output files
- implementation inference notes

### 5.2 cli.py

This is the command-line entry point.

It accepts:

- `--graph`
- `--out-dir`
- `--node-geo-csv`
- `--history-dir`
- `--current-block-height`
- `--exact-path-metrics`

It produces CSV, JSON, and plot outputs.

### 5.3 io.py

This loads graph JSON files and normalizes them into:

- nodes table
- channels table
- channel policies table

It originally expected UTF-8 JSON. After our first real run failed, we updated it to handle:

- UTF-8
- UTF-8 with BOM
- UTF-16
- UTF-16 little-endian

This was necessary because Windows PowerShell redirection saved our JSON as UTF-16.

### 5.4 classify.py

This infers node implementation from public graph metadata.

The classifier uses signals inspired by the paper:

- node color
- CLTV delta
- HTLC minimum
- proportional fee

The implementation categories are:

- `lnd`
- `core-lightning`
- `eclair`
- `unknown`

The output includes:

- inferred implementation
- confidence score
- per-implementation scores

### 5.5 metrics.py

This computes:

- channel implementation-pair distribution
- channel capacity distribution
- NetworkX graph metrics
- degree distribution
- centrality
- geographic distribution if geolocation is provided
- channel lifetime proxy or observed lifetime from multiple snapshots

We updated it to use a NetworkX `MultiGraph` so that multiple channels between the same two nodes are counted correctly.

It now distinguishes:

- `public_channel_count`
- `unique_node_pair_count`

This distinction matters because the Lightning Network can have multiple channels between the same two nodes.

### 5.6 plots.py

This generates PNG plots for:

- implementation distribution
- channel pair distribution
- capacity distribution
- degree distribution

### 5.7 sample_describegraph.json

We created a small synthetic example to test the pipeline before using real data.

It includes:

- one sample LND node
- one sample Core Lightning node
- one sample Eclair node
- two sample channels

The sample confirmed that the classifier and output generation worked.

## 6. LND Setup

We then set up LND on Windows.

### 6.1 Downloaded LND

We downloaded the Windows AMD64 LND release from:

```text
https://github.com/lightningnetwork/lnd/releases
```

The required executables are:

```text
lnd.exe
lncli.exe
```

They were placed in:

```text
C:\lnd
```

### 6.2 Created LND Config Folder

We created:

```powershell
$env:USERPROFILE\.lnd
```

And created:

```powershell
$env:USERPROFILE\.lnd\lnd.conf
```

### 6.3 LND Configuration

The configuration used:

```ini
[Application Options]
alias=ln-research-snapshot-node
color=#3399ff
debuglevel=info

[Bitcoin]
bitcoin.active=1
bitcoin.mainnet=1
bitcoin.node=neutrino

[Neutrino]
neutrino.addpeer=btcd-mainnet.lightning.computer

[Fee]
fee.url=https://nodes.lightning.computer/fees/v1/btc-fee-estimates.json
```

This config runs LND on:

- Bitcoin mainnet
- Neutrino light-client backend
- public graph sync

We used Neutrino because it is easier than running a full Bitcoin Core node.

## 7. LND Sync Result

After setup, we ran:

```powershell
.\lncli.exe getinfo
```

Important output:

```json
{
  "version": "0.20.1-beta commit=v0.20.1-beta",
  "alias": "ln-research-snapshot-node",
  "block_height": 950663,
  "synced_to_chain": true,
  "synced_to_graph": true,
  "chains": [
    {
      "chain": "bitcoin",
      "network": "mainnet"
    }
  ]
}
```

This means:

- LND is connected to Bitcoin mainnet.
- Chain sync is complete enough for our graph collection.
- Lightning graph sync is complete.

This was the key milestone before collecting data.

## 8. Data Collection

After LND was synced, we collected the Lightning graph snapshot.

Command:

```powershell
.\lncli.exe describegraph | Out-File -Encoding utf8 "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\raw\describegraph-2026-05-23.json"
```

We also recommended saving metadata:

```powershell
.\lncli.exe getinfo | Out-File -Encoding utf8 "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\raw\getinfo-2026-05-23.json"
```

```powershell
.\lncli.exe getnetworkinfo | Out-File -Encoding utf8 "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\raw\networkinfo-2026-05-23.json"
```

Metadata is important because it records:

- LND version
- block height
- graph sync status
- node identity
- collection context

## 9. Running The Analysis

We ran:

```powershell
cd "C:\Users\avadh\OneDrive\Documents\New project"
```

```powershell
$env:PYTHONPATH="C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\src"
```

```powershell
python -m ln_measurements.cli `
  --graph "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\raw\describegraph-2026-05-23.json" `
  --out-dir "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\outputs\2026-05-23" `
  --current-block-height 950663
```

The analysis completed successfully.

Output location:

```text
C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\outputs\2026-05-23
```

## 10. Output Files Generated

The pipeline generated:

```text
capacity_distribution.csv
centrality.csv
channels.csv
channel_lifetimes.csv
channel_pair_distribution.csv
degree_distribution.csv
geographic_distribution.csv
graph_metrics.json
implementation_distribution.csv
nodes_classified.csv
plots/
```

### 10.1 graph_metrics.json

This contains high-level graph metrics.

Observed result:

```json
{
  "average_clustering": 0.15771359995756962,
  "average_degree": 9.62484049340706,
  "component_count": 75,
  "largest_component_average_shortest_path_length": "skipped; rerun with --exact-path-metrics",
  "largest_component_channel_count": 31348,
  "largest_component_diameter_approx": 12,
  "largest_component_node_count": 6882,
  "node_count": 7053,
  "public_channel_count": 33942,
  "simple_graph_density": 0.0012647534802334066,
  "unique_node_pair_count": 31453
}
```

Interpretation:

- There were 7,053 public nodes in the snapshot.
- There were 33,942 public channels.
- There were 31,453 unique node pairs.
- The largest connected component contained 6,882 nodes.
- The graph had 75 connected components.

The distinction between public channels and unique node pairs matters because two nodes may have more than one channel between them.

### 10.2 implementation_distribution.csv

Observed result:

```text
implementation,node_count,node_share
lnd,4633,0.6567904734902184
unknown,1831,0.25956903884320953
core-lightning,368,0.05216898213779416
eclair,222,0.031471505528778
```

Interpretation:

- LND was the dominant inferred implementation.
- A large fraction remains unknown because public heuristics are imperfect.
- Core Lightning and Eclair were inferred for smaller shares.

This is an inferred distribution, not direct self-reported implementation data.

### 10.3 channel_pair_distribution.csv

This file groups channels by inferred implementation pair.

Examples:

```text
lnd-unknown
lnd-lnd
unknown-unknown
eclair-lnd
core-lightning-lnd
```

This supports the metric:

```text
Channel implementation-pair distribution
```

### 10.4 capacity_distribution.csv

The output showed all channel capacities as zero.

This is an important limitation of the current data collection setup.

Observed:

```text
mean capacity = 0
max capacity = 0
```

Interpretation:

The Neutrino-backed `describegraph` snapshot gave a useful topology graph, but did not provide usable channel capacity values.

Therefore:

- topology metrics are usable
- implementation metrics are usable
- channel pair metrics are usable
- capacity distribution is not usable yet

To compute capacity distribution properly, the next best step is to use LND with a full Bitcoin Core backend or use another source that provides public channel capacities correctly.

## 11. How This Helps The Project

This setup gives us a working measurement pipeline from raw Lightning data to research outputs.

The flow is:

```text
LND syncs public Lightning graph
        ↓
lncli describegraph exports graph JSON
        ↓
Python normalizes nodes/channels/policies
        ↓
classifier infers implementations
        ↓
NetworkX computes graph metrics
        ↓
CSV/JSON/plots are generated
```

This directly supports the reproduction study because it gives current Lightning Network measurements.

We can already report:

- node count
- public channel count
- unique node-pair count
- largest component size
- component count
- degree distribution
- centrality
- inferred implementation distribution
- inferred channel implementation-pair distribution

We cannot yet report:

- accurate channel capacity distribution from this Neutrino snapshot
- true channel balances
- true historical channel lifetimes from only one snapshot

## 12. Important Research Limitations

### 12.1 Public Graph Only

Lightning has private channels. `describegraph` only exposes the public graph known by the node.

Therefore all measurements are about:

```text
public Lightning Network topology
```

not the complete Lightning Network.

### 12.2 One Node's View

`describegraph` returns the graph from our LND node's view.

Different nodes may have slightly different gossip states.

### 12.3 Implementation Inference Is Heuristic

Lightning nodes do not directly advertise:

```text
I am LND
I am Core Lightning
I am Eclair
```

So we infer implementation from public defaults such as:

- color
- CLTV delta
- HTLC minimum
- fee rate

This creates an `unknown` category and possible misclassification.

### 12.4 Capacity Is Not Balance

Public gossip can reveal channel capacity, but not the current distribution of funds inside the channel.

Therefore:

- `capacity distribution` is feasible
- `balance distribution` is not available from public graph data alone

To measure real balances, one would need:

- private node-local channel balances, or
- probing methods, which introduce ethical and methodological concerns

### 12.5 Channel Lifetime Needs Repeated Snapshots

One snapshot cannot measure true channel lifetime.

With repeated daily snapshots, we can estimate:

- first observed date
- last observed date
- observed lifetime window

This is not the same as exact open and close time, but it is useful for a reproducible public-observation study.

## 13. What We Should Do Next

### Step 1: Save Metadata Files

Make sure these files are saved:

```powershell
.\lncli.exe getinfo | Out-File -Encoding utf8 "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\raw\getinfo-2026-05-23.json"
```

```powershell
.\lncli.exe getnetworkinfo | Out-File -Encoding utf8 "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\raw\networkinfo-2026-05-23.json"
```

### Step 2: Collect Daily Snapshots

Run daily:

```powershell
.\lncli.exe describegraph | Out-File -Encoding utf8 "C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\raw\describegraph-YYYY-MM-DD.json"
```

This enables observed channel lifetime analysis.

### Step 3: Add Geolocation

Extract public IP addresses from `nodes_classified.csv`.

Use a reproducible IP geolocation database such as:

- MaxMind GeoLite2
- DB-IP

Then create a CSV:

```text
node_geo.csv
```

With columns such as:

```text
pub_key,country_code,country_name,continent,city,latitude,longitude
```

Then rerun:

```powershell
python -m ln_measurements.cli `
  --graph "PATH\describegraph-2026-05-23.json" `
  --out-dir "PATH\outputs\2026-05-23-with-geo" `
  --node-geo-csv "PATH\node_geo.csv" `
  --current-block-height 950663
```

### Step 4: Fix Capacity Collection

Because the Neutrino snapshot produced zero capacities, choose one of these:

Option A:

- run LND with Bitcoin Core backend

Option B:

- collect from Core Lightning

Option C:

- use a trusted external public graph source only for capacity cross-checking

The most research-clean solution is:

```text
LND + Bitcoin Core backend
```

### Step 5: Generate Presentation Tables

Create clean tables for:

- graph summary
- implementation distribution
- channel pair distribution
- top central nodes
- degree distribution

### Step 6: Write Methodology Section

The methodology should explain:

- why LND `describegraph` was used
- snapshot date and block height
- public graph limitation
- implementation inference method
- capacity limitation
- lifetime limitation

## 14. Current Status

Completed:

- explored old repo
- identified reusable old components
- selected easiest data collection method
- set up LND on Windows
- created LND wallet
- synced to Bitcoin chain
- synced to Lightning graph
- collected first graph snapshot
- built Python analysis pipeline
- ran analysis successfully
- generated first 2026 metric outputs
- fixed graph channel counting to use MultiGraph

Current usable results:

- node count
- public channel count
- unique node-pair count
- component count
- largest component size
- clustering
- average degree
- inferred implementation distribution
- channel implementation-pair distribution
- centrality tables

Current limitation:

- channel capacity distribution is not usable yet because all capacities were zero in the Neutrino-based snapshot

Next major goal:

```text
Collect a capacity-complete graph snapshot using LND with Bitcoin Core backend or another reliable graph source.
```

## 15. Short Explanation For Presentation

We reproduced the data collection foundation for a modern Lightning Network topology study. We first examined the historical `lnresearch/topology` repository and found that it mainly provides raw gossip parsing and historical graph reconstruction tools, not a complete modern analysis pipeline. We then selected LND `describegraph` as the easiest current data source because it provides a full public Lightning graph snapshot in JSON format. We installed and configured LND on Windows using Neutrino, created a wallet, waited until both chain sync and graph sync were complete, collected a graph snapshot, and processed it with a custom Python pipeline using pandas and NetworkX. The pipeline generated CSV and JSON outputs for node counts, channel counts, graph metrics, implementation inference, and channel implementation-pair distribution. The first run produced 7,053 public nodes and 33,942 public channels. However, the Neutrino snapshot returned zero channel capacities, so capacity analysis requires a stronger backend such as LND connected to Bitcoin Core.
