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

Grab accession2taxid from a bunch of places:
```
curl -JLO https://openstack.cebitec.uni-bielefeld.de:8080/swift/v1/CAMI_2_DATABASES/ncbi_taxonomy_accession2taxid.tar
cd ncbi_taxonomy
tar xvf ../ncbi_taxonomy_accession2taxid.tar

curl -JLO https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/wgs.accession2taxid.gz
curl -JLO https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/dead_wgs.accession2taxid.gz
curl -JLO https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/dead_nucl.accession2taxid.gz

cd ../
```

## Allocate resources

```
srun -p high2 --time=48:00:00 --nodes=1 --cpus-per-task=64 --mem=80GB --pty /bin/bash
```

## Extract NCBI lineages

Based initially on scripts from https://github.com/dib-lab/2018-ncbi-lineages/.

Make a list of the genomes:
```
find genomes -type f > genome-list.txt
```

Then extract nucleotide accessions from the genomes:
```
./get-seq-acc-for-genomes.py genome-list.txt -o genome-list.accs.csv
```

Build a combined list of nucleotide accessions to taxids:
```
./tsv-to-parquet.py \
    ncbi_taxonomy/ncbi_taxonomy_accession2taxid/nucl_gb.accession2taxid.gz \
    ncbi_taxonomy/wgs.accession2taxid.gz \
    ncbi_taxonomy/dead_nucl.accession2taxid.gz \
    ncbi_taxonomy/dead_wgs.accession2taxid.gz \
        -o accession2taxid.parquet
```

Get the taxIDs for the sequence accessions from the genome list:
```
./join-seqacc-taxid.py genome-list.accs.csv accession2taxid.parquet -o genome-list.taxid.parquet
```

Finally, make lineage & manysketch files:
```
./make-manysketch-and-lineage.py genome-list.taxid.parquet genome-list.accs.csv \
    --nodes ncbi_taxonomy/nodes.dmp --names ncbi_taxonomy/names.dmp \
    --output-manysketch-csv manysketch.csv --output-lineage lineages.csv
```

aaaaaand... build!
```
sourmash scripts manysketch manysketch.csv -p k=21,k=31,k=51,dna -p skipm1n3 -p skipm2n3 -o cami-refseq-db.sig.zip
```
