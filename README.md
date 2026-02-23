# Torrento
## Members  
[Rushikesh Kundkar](https://gitlab.com/RRkundkar777)  
[Sanket Chaudhary](https://gitlab.com/sanketchaudhari.in20)

## Description

1. A Python base torrent client supporting concurrent peer connections and multiple simultaneous torrent downloads.
2. This project was an exercise of networking P2P protocol.

## Overview

- **1.main.py :** driver / runner

- **2.metainfo.py :** decode the bencoded .torrent

- **3.tracker.py :** send the http / udp requests and get list of peers

- **4.config.py :** global configurations

- **5.peer.py:** make handshake and request the peers for piece maintaining all data

- **6.connection.py :**  make connections with multiple peers at the same time

- **7.torrent.py :**  maintaining peers objects use for rarest first strategy

- **8.download.py :**  handle the requested pieces and chunks

- **9.writedata.py :** write downloaded files to local

## Installation & Setup

1. Install the required depedencies

```python
pip install -r requirements.txt
```

2. Run the torrent file

```python
python main.py <torrent_file>
```