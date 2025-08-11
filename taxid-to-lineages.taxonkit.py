#! /usr/bin/env python
import argparse
import numpy as np
import csv
import re
import pytaxonkit


WANT_TAXONOMY = ['superkingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'strain']
RANK_FORMATSTR = "{k};{p};{c};{o};{f};{g};{s};{t}" # this needs to match WANT_TAXONOMY, in format specified by taxonkit reformat cmd

 
def taxonkit_get_lineages_as_dict(taxidlist, ranks=WANT_TAXONOMY, formatstr=RANK_FORMATSTR, data_dir=None):
    # get lineage, taxpath for taxids using taxonkit
    n_failed = 0
    taxinfo = {}
    try:
        tk_lineage = pytaxonkit.lineage(taxidlist, fill_missing=True, pseudo_strain=True, formatstr=formatstr, threads=2, data_dir=data_dir)
        #tk_lineage = pytaxonkit.lineage(taxidlist, formatstr=formatstr, threads=2, data_dir=data_dir) #for taxonkit >=0.20
    except Exception as e:
        print(f"ERROR: Failed to retrieve lineage data with taxonkit: {e}")
        return taxinfo, len(taxidlist)
    
    for taxid in taxidlist:
        taxid_row = tk_lineage[tk_lineage['TaxID'] == taxid]
        if not taxid_row.empty:
            try:
                lin = taxid_row.iloc[0]['Lineage']
                if lin is np.nan:
                    print(f"ERROR: taxonkit lineage for taxid {taxid} is empty")
                    print(taxid_row)
                    continue
                names = lin.split(';')
                taxpath = taxid_row.iloc[0]['LineageTaxIDs'].replace(';', '|')
                # for taxonkit 0.20 and later, use instead:
                #names = lin.split(';')[1:] # skip "cellular organisms" prefix
                #taxpath = '|'.join(taxid_row.iloc[0]['LineageTaxIDs'].split(';')[1:])
            except KeyError as e:
                print(f"ERROR: KeyError for taxid {taxid}: {e}")
                print(f"taxid row: {taxid_row}")
                n_failed += 1
                continue
        else:
            names = []
            taxpath = ''
        
        n_taxids = len(taxpath.split('|'))
        if len(names) != n_taxids or len(names) != len(ranks):
            print(f"ERROR: taxonkit lineage for taxid {taxid} has mismatched lengths")
            print(f"names: {len(names)} taxids: {n_taxids} ranks: {len(ranks)}")
            n_failed += 1
            continue
        
        taxinfo[taxid] = (taxpath, names)
    
    return taxinfo, n_failed

def main(args):

    w = csv.writer(args.output)
    w.writerow(['ident', 'taxid', 'taxpath'] + WANT_TAXONOMY)

    # --- Collect ALL input rows (per-ident) and the set of unique taxids ---
    rows = []                 # list of (ident, taxid:int, lineage_cols:list[str])
    unique_taxids = set()

    # get taxids from input csv #
    with open(args.info, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ident = row['ident']
            taxid_str = row.get('taxid', '')
            if not taxid_str or not taxid_str.isdigit():
                print(f"WARNING: taxid '{taxid_str}' for ident {ident} is not a valid number. Skipping.")
                continue
            taxid = int(taxid_str)
            lineage_cols = [row.get(col, "") for col in WANT_TAXONOMY]
            rows.append((ident, taxid, lineage_cols))
            unique_taxids.add(taxid)

    # --- Compute lineages ONCE per unique taxid ---
    taxid2lineage, n_fail = taxonkit_get_lineages_as_dict(unique_taxids, WANT_TAXONOMY, RANK_FORMATSTR, data_dir=args.data_dir)
    print(f"Got {len(taxid2lineage)} lineages for {len(unique_taxids)} unique taxids, {n_fail} failed")
    
     # --- Write ONE output row PER IDENT (accession) ---
    lineages_count = 0
    failed_lineages = 0
    mismatches = 0

    for ident, taxid, lineage_cols in rows:
        lineage = taxid2lineage.get(taxid)
        if lineage:
            taxpath, lin_names = lineage

            # Compare (ignoring the last 'strain' rank)
            if lin_names[:-1] != lineage_cols[:-1]:
                for lin_name, lineage_col in zip(lin_names, lineage_cols):
                    if lin_name.startswith("unclassified") and lineage_col == "":
                        continue
                    if lin_name != lineage_col:
                        mismatches += 1
                        # print warning. Note that most of these mismatches are minimal and just due to stain info or level of detail
                        print(f"WARNING: taxid {taxid} (ident {ident}) mismatch: {lin_name} != {lineage_col}")

            w.writerow([ident, taxid, taxpath, *lin_names])
            lineages_count += 1
        else:
            print(f"WARNING: taxid {taxid} not in taxdump or incompatible lineage (ident {ident}). Writing empty lineage.")
            w.writerow([ident, taxid, "", *([""] * len(WANT_TAXONOMY))])
            failed_lineages += 1

    failed_lineages += n_fail
    print(f"output {lineages_count} lineages")
    print(f"failed {failed_lineages} lineages")
    if mismatches > 0:
        print(f"WARNING: found {mismatches} mismatched lineage names. Check the warnings for details.")
                    

if __name__ == "__main__":
    p = argparse.ArgumentParser(description='Map numbers from one file to another based on matching IDs.')
    p.add_argument('info', help='csv with ident --> taxid mapping (CSV format)')
    p.add_argument('--data-dir', help='directory containing NCBI taxdump data (optional; default uses version associated with pytaxonkit)')
    p.add_argument('-o', '--output', help='output lineages file', type=argparse.FileType('wt'))

    args = p.parse_args()
    main(args)
