#! /usr/bin/env python
import polars as pl
import argparse
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('genome_accs')
    p.add_argument('acc2taxid')
    args = p.parse_args()

    genome_accs = pl.scan_csv(args.genome_accs)
    acc2taxid = pl.scan_parquet(args.acc2taxid)

    def get_nover_acc(acc):
        return acc.split('.')[0]

    genome_accs2 = genome_accs.with_columns(
        pl.col("seq_acc").map_elements(get_nover_acc, return_dtype=str).alias("seq_acc_nv")
    )
    print(genome_accs2.describe())

    genome_accs2 = genome_accs2.collect()
    acc2taxid = acc2taxid.collect()

    for r in genome_accs2.iter_rows():
        print('R', r)
        break

    for r in acc2taxid.iter_rows():
        print('R2', r)
        break

    df = acc2taxid.join(genome_accs2,
                        left_on='accession',
                        right_on='seq_acc_nv',
                        how='inner')

    df = df.collect()
    print(len(df))


if __name__ == '__main__':
    sys.exit(main())
