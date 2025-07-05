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


want_taxonomy = ['superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'strain']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('genome_file_list')
    p.add_argument('acc2taxid_file')
    p.add_argument('--nodes-dmp', required=True)
    p.add_argument('--names-dmp', required=True)
    p.add_argument('--output-manysketch-csv', required=True)
    p.add_argument('--output-lineage-csv', required=True)
    args = p.parse_args()

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

    # build mapping from first sequence id => taxid
    seqacc_to_genomeacc = {}
    for n, (genome_acc, filename) in enumerate(genome_acc_to_filename.items()):
        if n % 100 == 0:
            print('reading genome', n, 'of', len(genome_acc_to_filename))
        # get first seq ID
        for record in screed.open(filename):
            name = record.name
            seqacc = name.split(' ')[0]
            seqacc_to_genomeacc[seqacc] = genome_acc
            break

    print(f'found {len(seqacc_to_genomeacc)} accessions, yay.')
    assert len(seqacc_to_genomeacc) == len(genome_acc_to_filename)

    # now, get the info from the accession2taxid file
    genomeacc_to_taxid = {}
    with gzip.open(args.acc2taxid_file, 'rt', newline='') as fp:
        r = csv.DictReader(fp, delimiter='\t')
        for row_n, row in enumerate(r):
            if row_n % 1000000 == 0 and row_n:
                found = len(genomeacc_to_taxid)
                total = len(seqacc_to_genomeacc)
                print(f'... reading row {row_n}; found {found} of {total}')

            seqacc = row['accession.version']
            if seqacc in seqacc_to_genomeacc:
                taxid = row['taxid']
                genome_acc = seqacc_to_genomeacc[seqacc]
                genomeacc_to_taxid[genome_acc] = int(taxid)

                if len(genomeacc_to_taxid) == len(seqacc_to_genomeacc):
                    # early exit ;)
                    break

    if len(genomeacc_to_taxid) != len(seqacc_to_genomeacc):
        print('WARNING: we do not have taxids for every acc.')
        with_taxids = set(genomeacc_to_taxid)
        with_seqacc = set(seqacc_to_genomeacc.values())
        print(with_seqacc - with_taxids)
    else:
        print('Found all taxids. Proceeding with confidence!!')

    # finally, integrate it all
    acc_to_lin = {}

    manysketch_fp = open(args.output_manysketch_csv, 'wt')
    manysketch_w = csv.writer(manysketch_fp)
    manysketch_w.writerow(['name', 'genome_filename', 'protein_filename'])

    lineage_fp = open(args.output_lineage_csv, 'wt')
    lineage_w = csv.writer(lineage_fp)
    lineage_w.writerow(['name', 'taxid'] + want_taxonomy)

    n_written = 0
    for acc, taxid in genomeacc_to_taxid.items():
        lin_dict = taxfoo.get_lineage_as_dict(taxid, want_taxonomy)
        genus = lin_dict['genus']
        species = lin_dict['species']
        strain = lin_dict.get('strain', '')
        if strain:
            name = f"{acc} {strain}"
        else:
            name = f"{acc} {species}"
        filename = genome_acc_to_filename[acc]
        manysketch_w.writerow([name, filename, ''])

        taxrow = [ acc, taxid ]
        taxrow += [ lin_dict.get(rank, '') for rank in want_taxonomy ]
        lineage_w.writerow(taxrow)

        n_written += 1

    print(f'wrote {n_written} rows to manysketch & lineage CSVs')

 
if __name__ == '__main__':
    main()
