# Prepping CAMI II databases for sourmash

Using data sets at https://cami-challenge.org/reference-databases/.

## Download and unpack

(Data sets are already on farm at `~ctbrown/scratch3/2025-cami-old-db`)

Grab RefSeq genomic:
```
curl -JLO https://openstack.cebitec.uni-bielefeld.de:8080/swift/v1/CAMI_2_DATABASES/RefSeq_genomic_20190108.tar

mkdir -p genomes
cd genomes
tar xf ../RefSeq_genomic_20190108.tar
cd ../
```

Grab taxonomy:
```
curl -JLO https://openstack.cebitec.uni-bielefeld.de:8080/swift/v1/CAMI_2_DATABASES/ncbi_taxonomy.tar
tar tvf ncbi_taxonomy.tar
cd ncbi_taxonomy
tar xzf taxdump.tar.gz
cd ..
```

Grab accession2taxid:
```
curl -JLO https://openstack.cebitec.uni-bielefeld.de:8080/swift/v1/CAMI_2_DATABASES/ncbi_taxonomy_accession2taxid.tar
cd ncbi_taxonomy
tar xvf ../ncbi_taxonomy_accession2taxid.tar
```

## Extract NCBI lineages

Based on scripts from https://github.com/dib-lab/2018-ncbi-lineages/:

Make a list of the genomes:
```
find genomes -type f > genome-list.txt
```

Then run a script to make a manysketch output file and a lineages file:
```
./make-manysketch-and-lineage.py genome-list.txt \
    ncbi_taxonomy/ncbi_taxonomy_accession2taxid/nucl_gb.accession2taxid.gz \
    --nodes ncbi_taxonomy/nodes.dmp --names ncbi_taxonomy/names.dmp \
    --output-manysketch-csv manysketch.csv --output-lineage lineages.csv
```
