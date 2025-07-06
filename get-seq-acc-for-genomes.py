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


def main():
    p = argparse.ArgumentParser()
    p.add_argument('genome_file_list')
    p.add_argument('-o', '--output', required=True,
                   help='CSV file of genome accessions to contig accessions')
    args = p.parse_args()

    # get list of genome files & assembly accessions (GCF/GCA)
    print('loading genome file info')
    genome_files = [ x.strip() for x in open(args.genome_file_list) ]

    genome_acc_to_filename = {}
    for filename in genome_files:
        x = os.path.basename(filename) # get filename w/o dir
        x = x.split('_', 3)[:2] # pull off GCF_XYZ info
        acc = '_'.join(x)         # make back into GCF_XYZ string
        genome_acc_to_filename[acc] = filename

    fp = open(args.output, 'w', newline='')
    w = csv.writer(fp)
    w.writerow(['genome_acc', 'seq_acc'])

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
            w.writerow([genome_acc, seqacc])
            break

    print(f'found {len(seqacc_to_genomeacc)} accessions, yay.')
    assert len(seqacc_to_genomeacc) == len(genome_acc_to_filename)

    sys.exit(0)

 
if __name__ == '__main__':
    main()
