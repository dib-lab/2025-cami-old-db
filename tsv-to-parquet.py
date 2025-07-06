#! /usr/bin/env python
import polars
import argparse
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument('tsvs', nargs='+')
    p.add_argument('-o', '--output', help="parquet file", required=True)
    args = p.parse_args()

    lazy_frames = []
    for tsv in args.tsvs:
        lazy_frame = polars.scan_csv(tsv, separator="\t")
        lazy_frames.append(lazy_frame)

    combined = polars.concat(lazy_frames)
    combined.sink_parquet(args.output)

    print(f'wrote some undetermined number of rows to {args.output}')


if __name__ == '__main__':
    sys.exit(main())
