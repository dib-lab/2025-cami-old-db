#! /usr/bin/env python
import polars as pl
import argparse
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('genome_accs')
    p.add_argument('acc2taxid')
    p.add_argument('-o', '--output-parquet', required=True)
    args = p.parse_args()

    genome_accs = pl.scan_csv(args.genome_accs)
    acc2taxid = pl.scan_parquet(args.acc2taxid)

    df = genome_accs.join(acc2taxid,
                          right_on='accession.version',
                          left_on='seq_acc',
                          how='inner')

    # remove unique rows, caused by dups in acc2taxid
    df = df.unique()

    # save to parquet
    df.sink_parquet(args.output_parquet)

    # load & display
    df = pl.scan_parquet(args.output_parquet)
    print(df.describe())


if __name__ == '__main__':
    sys.exit(main())
