#! /usr/bin/env python
"""
"""

import sys
import os
import argparse
import gzip
import screed
import csv
import ncbi_taxdump_utils
import polars as pl


want_taxonomy = ['superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'strain']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('joined_parquet')
    p.add_argument('genome_file_list')
    p.add_argument('--nodes-dmp', required=True)
    p.add_argument('--names-dmp', required=True)
    p.add_argument('--output-manysketch-csv', required=True)
    p.add_argument('--output-lineage-csv', required=True)
    args = p.parse_args()

    # load joined parquet
    accs_to_taxid = pl.scan_parquet(args.joined_parquet).collect()
    print(accs_to_taxid.describe())

    # load taxdump stuff
    print('loading taxdump')
    taxfoo = ncbi_taxdump_utils.NCBI_TaxonomyFoo()

    taxfoo.load_nodes_dmp(args.nodes_dmp)
    taxfoo.load_names_dmp(args.names_dmp)

    # get list of genome files & assembly accessions (GCF/GCA)
    print('loading genome file info')
    genome_files = [ x.strip() for x in open(args.genome_file_list) ]

    genome_acc_to_filename = {}
    for filename in genome_files:
        x = os.path.basename(filename) # get filename w/o dir
        x = x.split('_', 3)[:2] # pull off GCF_XYZ info
        acc = '_'.join(x)         # make back into GCF_XYZ string
        genome_acc_to_filename[acc] = filename

    # now! output the various thingers.

    manysketch_fp = open(args.output_manysketch_csv, 'wt')
    manysketch_w = csv.writer(manysketch_fp)
    manysketch_w.writerow(['name', 'genome_filename', 'protein_filename'])

    lineage_fp = open(args.output_lineage_csv, 'wt')
    lineage_w = csv.writer(lineage_fp)
    lineage_w.writerow(['name', 'taxid'] + want_taxonomy)

    n_written = 0
    seen = set()
    missing_taxid_info = []

    for row in accs_to_taxid.iter_rows(named=True):
        acc = row['genome_acc']
        taxid = row['taxid']
        if taxid is None:
            print(f'WARNING for {acc} - no taxid.')
            continue

        if acc in seen:
            print(f'Duplicate?! {acc}')
            continue

        lin_dict = taxfoo.get_lineage_as_dict(taxid, want_taxonomy)
        species = lin_dict.get('species', '')
        strain = lin_dict.get('strain', '')
        if strain:
            name = f"{acc} {strain}"
        elif species:
            name = f"{acc} {species}"
        else:
            name = f"{acc}"
            print(f'WARNING for {acc} - no species or strain for taxid {taxid}')
            missing_taxid_info.append(acc)
            continue

        seen.add(acc)
        filename = genome_acc_to_filename[acc]
        manysketch_w.writerow([name, filename, ''])

        taxrow = [ acc, taxid ]
        taxrow += [ lin_dict.get(rank, '') for rank in want_taxonomy ]
        lineage_w.writerow(taxrow)

        n_written += 1

    print(f'wrote {n_written} rows to manysketch & lineage CSVs')

    expected_genome_accs = set(genome_acc_to_filename)
    missing_genomes= expected_genome_accs - seen
    print(f'missing information for {len(missing_genomes)} genomes.')

    if missing_genomes:
        filename = 'report.missing-info-genomes.txt'
        with open(filename, 'wt') as fp:
            print("\n".join(missing_genomes), file=fp)
        print(f"wrote list of missing genomes to '{filename}'")
        print('(this list includes any genomes missing taxinfo, output next')

    if missing_taxid_info:
        filename = 'report.missing-taxid-info.txt'
        with open(filename, 'wt') as fp:
            print("\n".join(missing_taxid_info), file=fp)
        print(f"wrote list of genomes missing taxinfo to '{filename}'")

 
if __name__ == '__main__':
    main()
