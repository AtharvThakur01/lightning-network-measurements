# Daily Metrics Runbook For This System

This document contains the exact commands to run on this system to collect a daily Lightning Network graph snapshot and generate metrics outputs.

Current system paths used in this project:

```text
LND folder:
C:\lnd

Project folder:
C:\Users\avadh\OneDrive\Documents\New project

Measurement project folder:
C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements
```

This workflow generates metrics for:

- node count
- public channel count
- unique node pairs
- connected components
- average degree
- clustering
- centrality
- implementation distribution
- channel implementation-pair distribution
- geographic distribution, if `node_geo` enrichment is available

Capacity distribution is excluded for now because the current Neutrino-based LND setup returned unreliable zero channel capacities.

## 1. Start LND

Open PowerShell window 1.

Run:

```powershell
cd C:\lnd
.\lnd.exe --configfile="$env:USERPROFILE\.lnd\lnd.conf"
```

Keep this PowerShell window open.

This starts the LND daemon. The `lncli.exe` command will not work unless `lnd.exe` is running.

## 2. Unlock Wallet If Needed

Open PowerShell window 2.

Run:

```powershell
cd C:\lnd
.\lncli.exe unlock
```

If the wallet is already unlocked, continue to the next step.

## 3. Confirm Sync Status

Run:

```powershell
.\lncli.exe getinfo
```

Continue only when both values are true:

```json
"synced_to_chain": true,
"synced_to_graph": true
```

If `synced_to_graph` is false, keep LND running and wait. Check again later:

```powershell
.\lncli.exe getinfo
```

Do not collect a snapshot before graph sync is complete, because the graph may be incomplete.

## 4. Set Daily Variables

For the June 10, 2026 run:

```powershell
$PROJECT_DIR = "C:\Users\avadh\OneDrive\Documents\New project"
$DATE = "2026-06-10"
```

For a different day, only change `$DATE`.

Example:

```powershell
$DATE = "2026-06-11"
```

## 5. Create Required Folders

Run:

```powershell
New-Item -ItemType Directory -Force "$PROJECT_DIR\lightning_measurements\data\raw"
New-Item -ItemType Directory -Force "$PROJECT_DIR\lightning_measurements\data\geo"
New-Item -ItemType Directory -Force "$PROJECT_DIR\lightning_measurements\outputs"
```

These folders store:

- raw graph snapshots
- optional geolocation database/files
- generated analysis outputs

## 6. Save LND Metadata

Run:

```powershell
cd C:\lnd
```

Save `getinfo`:

```powershell
.\lncli.exe getinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\getinfo-$DATE.json"
```

Save `getnetworkinfo`:

```powershell
.\lncli.exe getnetworkinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\networkinfo-$DATE.json"
```

These files document the collection environment, including:

- LND version
- block height
- chain sync status
- graph sync status
- network summary

## 7. Get Current Block Height

Run:

```powershell
.\lncli.exe getinfo
```

Find:

```json
"block_height": XXXXX
```

Copy the block height number. In later commands it is written as:

```text
<BLOCK_HEIGHT>
```

Replace `<BLOCK_HEIGHT>` with the actual number from your `getinfo` output.

## 8. Collect The Daily Lightning Graph Snapshot

Run:

```powershell
.\lncli.exe describegraph | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\describegraph-$DATE.json"
```

Check that the file was created:

```powershell
Get-Item "$PROJECT_DIR\lightning_measurements\data\raw\describegraph-$DATE.json"
```

The file should be large because it contains the public Lightning Network graph.

## 9. Go To The Measurement Project Folder

Run:

```powershell
cd "$PROJECT_DIR\lightning_measurements"
```

Check the folder:

```powershell
dir
```

Expected important items:

```text
src
examples
data
outputs
requirements.txt
README.md
```

## 10. Check Python Environment

Run:

```powershell
.\.venv\Scripts\python.exe -c "import pandas, networkx, matplotlib; print('dependencies ok')"
```

If this fails, install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Set the Python path:

```powershell
$env:PYTHONPATH="$PWD\src"
```

Test that the project package is visible:

```powershell
.\.venv\Scripts\python.exe -c "import ln_measurements; print('project found')"
```

Expected output:

```text
project found
```

## 11. Run Base Analysis Without Geography

Run this first to generate `nodes_classified.csv`, which contains node metadata and addresses:

```powershell
.\.venv\Scripts\python.exe -m ln_measurements.cli `
  --graph ".\data\raw\describegraph-$DATE.json" `
  --out-dir ".\outputs\$DATE-base" `
  --current-block-height <BLOCK_HEIGHT>
```

Example:

```powershell
.\.venv\Scripts\python.exe -m ln_measurements.cli `
  --graph ".\data\raw\describegraph-2026-06-10.json" `
  --out-dir ".\outputs\2026-06-10-base" `
  --current-block-height 951234
```

Replace `951234` with the real block height.

Expected output:

```text
Wrote Lightning measurement outputs to outputs\2026-06-10-base
```

## 12. Geographic Distribution Setup

Geographic distribution needs IP geolocation enrichment.

The main analysis pipeline expects a CSV file with this structure:

```text
pub_key,country_code,country_name,continent,city,latitude,longitude
```

For this date, the expected file is:

```text
.\data\raw\node_geo-2026-06-10.csv
```

### 12.1 Download A Geolocation Database

Recommended database:

```text
GeoLite2-Country.mmdb
```

Place it here:

```text
C:\Users\avadh\OneDrive\Documents\New project\lightning_measurements\data\geo\GeoLite2-Country.mmdb
```

Do not upload this database to GitHub unless the license allows it.

### 12.2 Install Geo Dependency

Run:

```powershell
.\.venv\Scripts\python.exe -m pip install geoip2
```

If you later add this permanently to the project, add this line to `requirements.txt`:

```text
geoip2>=4.8
```

### 12.3 Create `node_geo` CSV

If a geolocation helper script is available, run it to create:

```text
.\data\raw\node_geo-$DATE.csv
```

The helper should use:

```text
.\outputs\$DATE-base\nodes_classified.csv
.\data\geo\GeoLite2-Country.mmdb
```

and produce:

```text
.\data\raw\node_geo-$DATE.csv
```

If the helper script is not implemented yet, geographic output will remain mostly `unknown`. The next implementation task is to add a script that:

1. Reads `nodes_classified.csv`.
2. Parses the `addresses` column.
3. Extracts IPv4/IPv6 addresses.
4. Marks `.onion` addresses as Tor.
5. Marks missing addresses as unknown.
6. Looks up countries using `GeoLite2-Country.mmdb`.
7. Writes `node_geo-$DATE.csv`.

## 13. Run Final Analysis With Geography

Only run this step after `node_geo-$DATE.csv` exists.

Run:

```powershell
.\.venv\Scripts\python.exe -m ln_measurements.cli `
  --graph ".\data\raw\describegraph-$DATE.json" `
  --out-dir ".\outputs\$DATE" `
  --node-geo-csv ".\data\raw\node_geo-$DATE.csv" `
  --current-block-height <BLOCK_HEIGHT>
```

Example:

```powershell
.\.venv\Scripts\python.exe -m ln_measurements.cli `
  --graph ".\data\raw\describegraph-2026-06-10.json" `
  --out-dir ".\outputs\2026-06-10" `
  --node-geo-csv ".\data\raw\node_geo-2026-06-10.csv" `
  --current-block-height 951234
```

If `node_geo-$DATE.csv` is not available yet, run final analysis without geography:

```powershell
.\.venv\Scripts\python.exe -m ln_measurements.cli `
  --graph ".\data\raw\describegraph-$DATE.json" `
  --out-dir ".\outputs\$DATE" `
  --current-block-height <BLOCK_HEIGHT>
```

## 14. Verify Final Outputs

Run:

```powershell
dir ".\outputs\$DATE"
```

Expected files:

```text
centrality.csv
channels.csv
channel_lifetimes.csv
channel_pair_distribution.csv
degree_distribution.csv
geographic_distribution.csv
graph_metrics.json
implementation_distribution.csv
nodes_classified.csv
plots
```

Capacity files may also be generated, but ignore them for now:

```text
capacity_distribution.csv
capacity_distribution.png
```

## 15. Check Main Metrics

Graph metrics:

```powershell
Get-Content ".\outputs\$DATE\graph_metrics.json"
```

Implementation distribution:

```powershell
Get-Content ".\outputs\$DATE\implementation_distribution.csv"
```

Channel pair distribution:

```powershell
Get-Content ".\outputs\$DATE\channel_pair_distribution.csv" -TotalCount 10
```

Degree distribution:

```powershell
Get-Content ".\outputs\$DATE\degree_distribution.csv" -TotalCount 10
```

Geographic distribution:

```powershell
Get-Content ".\outputs\$DATE\geographic_distribution.csv" -TotalCount 20
```

## 16. Check Plots

Run:

```powershell
dir ".\outputs\$DATE\plots"
```

Expected plots:

```text
implementation_distribution.png
channel_pair_distribution.png
degree_distribution.png
capacity_distribution.png
```

Ignore the capacity plot for now.

## 17. Compare With Previous Snapshot

Compare graph metrics:

```powershell
Get-Content ".\outputs\2026-05-23\graph_metrics.json"
Get-Content ".\outputs\$DATE\graph_metrics.json"
```

Compare implementation distribution:

```powershell
Get-Content ".\outputs\2026-05-23\implementation_distribution.csv"
Get-Content ".\outputs\$DATE\implementation_distribution.csv"
```

If geographic distribution is available for both dates:

```powershell
Get-Content ".\outputs\2026-05-23\geographic_distribution.csv" -TotalCount 20
Get-Content ".\outputs\$DATE\geographic_distribution.csv" -TotalCount 20
```

## 18. Record Daily Summary

Record these values in project notes or a CSV:

```text
Date:
Block height:
Synced to chain:
Synced to graph:
Node count:
Public channel count:
Unique node pairs:
Component count:
Largest component node count:
Average degree:
Average clustering:
LND share:
Core Lightning share:
Eclair share:
Unknown share:
Top countries:
Notes:
```

Use:

```text
outputs\<DATE>\graph_metrics.json
outputs\<DATE>\implementation_distribution.csv
outputs\<DATE>\geographic_distribution.csv
```

## 19. Methodology Notes For Report

Use this statement for geography:

```text
Geographic distribution was estimated from public clearnet IP addresses advertised in Lightning node announcements. Tor-only nodes and nodes without public addresses were marked separately. The inferred geography reflects hosting/server location and not necessarily the physical location of the node operator.
```

Use this statement for capacity:

```text
Capacity distribution is excluded from this run because the current Neutrino-based LND setup does not provide reliable channel capacity values.
```

## 20. Daily Checklist

Each day:

```text
1. Start LND
2. Unlock wallet if needed
3. Wait for synced_to_chain=true and synced_to_graph=true
4. Set PROJECT_DIR and DATE
5. Save getinfo and getnetworkinfo
6. Copy block height
7. Save describegraph
8. Run base analysis
9. Create node_geo CSV if geolocation is available
10. Run final analysis
11. Verify outputs
12. Record summary
13. Compare with previous snapshot
```

