## NetPath Networks

For a slightly larger example, we have two NetPath networks -- BCR and Wnt -- and a background network of the union of all NetPath pathways.  Files from the graphlet repo (they have also been packaged and sent to Chris way back in the day).  

### Background Network
- `np-union-full.txt`: NetPath union file with pathway annotation, interaction type, and common node names.
- `np-union.txt`: First three columns of `np-union-full.txt`.

### Wnt Pathway
- `wnt-nodes.txt`: Wnt nodes with receptor/tf and common name.
- `wnt-edges.txt`: Edges in the Wnt pathway (prec-rec ground truth edges). *Update 7/29: duplicate edges were removed.*
- `sources.wnt.txt`: Wnt receptors as a single-column.
- `targets.wnt.txt`: Wnt transcription factors as a single column.

### BCR Pathway
- `bcr-nodes.txt`: BCR nodes with receptor/tf and common name.
- `bcr-edges.txt`: Edges in the BCR pathway (prec-rec ground truth edges). *Update 7/29: duplicate edges were removed.*
- `sources.bcr.txt`: BCR receptors as a single-column.
- `targets.bcr.txt`: BCR transcription factors as a single column.
