# First-Time LND Setup Guide For Lightning Network Graph Collection

## 1. Purpose Of This Setup

This guide explains how to set up an LND Lightning client for the first time on Windows and use it to collect a public Lightning Network graph snapshot.

The snapshot is collected with:

```powershell
lncli describegraph
```

This graph snapshot is used for a Lightning Network measurement study. It gives public topology data such as:

- public nodes
- public channels
- node aliases
- node colors
- node addresses
- channel policies
- channel fees
- CLTV settings
- HTLC settings

This setup does not require opening Lightning channels or putting money into the wallet.

## 2. What We Are Setting Up

We are setting up:

```text
LND = Lightning Network Daemon
lncli = command-line tool used to talk to LND
```

LND will run on:

```text
Bitcoin mainnet
Neutrino backend
```

Neutrino is a light-client mode. It is easier for a first setup because it avoids running a full Bitcoin Core node.

## 3. Folder Layout Used

In our setup, LND binaries were placed here:

```text
C:\lnd
```

The configuration file was placed here:

```text
C:\Users\<your-username>\.lnd\lnd.conf
```

Each user should choose their own project folder.

```text
<PROJECT_DIR>
```

For example:

```text
C:\Users\<your-username>\Documents\lightning-research
```

The collected graph snapshot should be stored under a raw data folder inside the user's project directory:

```text
<PROJECT_DIR>\lightning_measurements\data\raw
```

## 4. Step 1: Download LND

Open the official LND releases page:

```text
https://github.com/lightningnetwork/lnd/releases
```

Download the Windows AMD64 release zip.

The file name will look similar to:

```text
lnd-windows-amd64-*.zip
```

Unzip the file.

Inside the extracted folder, locate:

```text
lnd.exe
lncli.exe
```

## 5. Step 2: Create The LND Program Folder

Create this folder:

```text
C:\lnd
```

Move these two files into it:

```text
C:\lnd\lnd.exe
C:\lnd\lncli.exe
```

## 6. Step 3: Open PowerShell

Open Windows PowerShell.

Go to the LND folder:

```powershell
cd C:\lnd
```

Check that LND works:

```powershell
.\lnd.exe --version
```

Check that `lncli` works:

```powershell
.\lncli.exe --version
```

Both commands should print version information.

## 7. Step 4: Create The LND Configuration Folder

Create the LND config folder:

```powershell
mkdir $env:USERPROFILE\.lnd
```

Open the config file in Notepad:

```powershell
notepad $env:USERPROFILE\.lnd\lnd.conf
```

If Notepad asks whether to create the file, choose yes.

## 8. Step 5: Add The LND Configuration

Paste this into `lnd.conf`:


[Application Options]
alias=ln-research-snapshot-node
color=#3399ff
debuglevel=info
maxpendingchannels=0

[Bitcoin]
bitcoin.active=1
bitcoin.mainnet=1
bitcoin.node=neutrino

[Neutrino]
neutrino.addpeer=btcd-mainnet.lightning.computer

Save the file and close Notepad.

### What This Config Means

```ini
alias=ln-research-snapshot-node
```

This gives your LND node a readable name.

```ini
color=#3399ff
```

This sets the advertised node color.

```ini
bitcoin.active=1
```

This enables Bitcoin support.

```ini
bitcoin.mainnet=1
```

This connects to Bitcoin mainnet.

```ini
bitcoin.node=neutrino
```

This uses Neutrino light-client mode.

```ini
neutrino.addpeer=btcd-mainnet.lightning.computer
```

This gives Neutrino a peer to connect to.

```ini
fee.url=...
```

This gives LND a fee-estimation source required for Neutrino on mainnet.

## 9. Step 6: Start LND

In PowerShell:

```powershell
cd C:\lnd
```

Start LND using the config file:

```powershell
.\lnd.exe --configfile="$env:USERPROFILE\.lnd\lnd.conf"
```

Keep this PowerShell window open.

This window is now running the LND daemon. It will print logs while it starts and syncs.

## 10. Step 7: Open A Second PowerShell Window

Do not close the first PowerShell window.

Open a second PowerShell window.

Go to the LND folder:

```powershell
cd C:\lnd
```

This second window will be used for `lncli` commands.

## 11. Step 8: Create The LND Wallet

In the second PowerShell window, run:

```powershell
.\lncli.exe create
```

LND will ask for a wallet password.

Choose a password and save it somewhere safe.

When asked whether you already have a cipher seed, answer:

```text
n
```

When asked for an optional seed passphrase, you can press Enter to skip.

LND will then show a 24-word seed phrase.

Save the seed phrase somewhere safe.

Important:

For this research setup, you do not need to fund the wallet. The wallet is needed so LND can run normally, but the measurement task only needs public graph data.

## 12. Step 9: Unlock Wallet On Later Starts

After the wallet has been created once, future LND starts may require wallet unlock.

Start LND in the first PowerShell window:

```powershell
.\lnd.exe --configfile="$env:USERPROFILE\.lnd\lnd.conf"
```

Then in the second PowerShell window:

```powershell
.\lncli.exe unlock
```

Enter the wallet password.

## 13. Step 10: Wait For Sync

Check status with:

```powershell
.\lncli.exe getinfo
```

The important fields are:

```json
"synced_to_chain": true
```

and:

```json
"synced_to_graph": true
```

Successful output should include fields like:

```json
{
  "version": "0.20.1-beta commit=v0.20.1-beta",
  "alias": "ln-research-snapshot-node",
  "block_height": <CURRENT_BLOCK_HEIGHT>,
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

Only continue to graph collection after both sync fields are true.

## 14. Step 11: Create A Raw Data Folder

Choose your own project folder first.

Example:

```powershell
$PROJECT_DIR = "C:\Users\<your-username>\Documents\lightning-research"
```

Create the folder where graph snapshots will be saved:

```powershell
mkdir "$PROJECT_DIR\lightning_measurements\data\raw"
```

If the folder already exists, that is fine.

## 15. Step 12: Collect The Lightning Graph Snapshot

Use:

```powershell
.\lncli.exe describegraph | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\describegraph-<DATE>.json"
```

This creates the main data file:

```text
describegraph-<DATE>.json
```

This file contains the public Lightning Network graph from the point of view of your LND node.

## 16. Step 13: Save Metadata Files

Save LND status metadata:

```powershell
.\lncli.exe getinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\getinfo-<DATE>.json"
```

Save network summary metadata:

```powershell
.\lncli.exe getnetworkinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\networkinfo-<DATE>.json"
```

These files help document:

- LND version
- block height
- graph sync status
- network mode
- graph summary
- collection context

## 17. Step 14: Run The Analysis Pipeline

Go to the project folder:

```powershell
cd "$PROJECT_DIR"
```

Set the Python path:

```powershell
$env:PYTHONPATH="$PROJECT_DIR\lightning_measurements\src"
```

Run the analysis:

```powershell
python -m ln_measurements.cli `
  --graph "$PROJECT_DIR\lightning_measurements\data\raw\describegraph-<DATE>.json" `
  --out-dir "$PROJECT_DIR\lightning_measurements\outputs\<DATE>" `
  --current-block-height <BLOCK_HEIGHT>
```

The output folder will be:

```text
<PROJECT_DIR>\lightning_measurements\outputs\<DATE>
```

## 18. Step 15: Review Output Files

The analysis produces files such as:

```text
graph_metrics.json
implementation_distribution.csv
channel_pair_distribution.csv
capacity_distribution.csv
degree_distribution.csv
centrality.csv
channels.csv
nodes_classified.csv
channel_lifetimes.csv
plots/
```

These outputs are used for the Lightning Network measurement study.

## 19. What The Snapshot Helps Measure

The `describegraph` snapshot helps compute:

- public node count
- public channel count
- degree distribution
- centrality
- connected components
- clustering
- node implementation inference
- channel implementation-pair distribution
- geography after IP geolocation enrichment

It does not directly reveal:

- private channels
- real channel balances
- exact channel open and close history

## 20. Important Limitation Of This First Setup

This first setup used Neutrino because it is simple.

It successfully produced topology data, but the first collected graph snapshot showed channel capacities as zero.

That means this setup is useful for:

- topology metrics
- implementation distribution
- graph structure
- centrality
- component analysis

But for accurate channel capacity distribution, the next recommended setup is:

```text
LND with Bitcoin Core backend
```

or another reliable source that exposes public channel capacities correctly.

## 21. Daily Snapshot Collection

To estimate channel lifetime, collect snapshots repeatedly.

Example daily command:

```powershell
.\lncli.exe describegraph | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\describegraph-<NEXT_DATE>.json"
```

Also save:

```powershell
.\lncli.exe getinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\getinfo-<NEXT_DATE>.json"
```

```powershell
.\lncli.exe getnetworkinfo | Out-File -Encoding utf8 "$PROJECT_DIR\lightning_measurements\data\raw\networkinfo-<NEXT_DATE>.json"
```

With repeated snapshots, we can estimate:

- first observed date
- last observed date
- observed lifetime window

## 22. Summary

The setup process is:

```text
Download LND
  ↓
Place lnd.exe and lncli.exe in C:\lnd
  ↓
Create lnd.conf
  ↓
Start LND
  ↓
Create or unlock wallet
  ↓
Wait for chain and graph sync
  ↓
Run lncli describegraph
  ↓
Save graph JSON and metadata
  ↓
Run Python analysis pipeline
  ↓
Generate CSV, JSON, and plot outputs
```

This gives a repeatable first-time setup for collecting Lightning Network graph data with LND.
