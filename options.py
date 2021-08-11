from pathlib import Path
import argparse

def load_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        'file',
        type=str,
        help='file to parse.'
    )
    ap.add_argument(
        '-s', '--start',
        type=str,
        help='word or character string that delimits the starting point of the parser.'
    )
    ap.add_argument(
        '-e', '--end',
        type=str,
        help='word or character string that delimits the ending point of the parser.'
    )
    ap.add_argument(
        '-u', '--unit',
        type=str,
        default='meter',
        choices=['m', 'meter', 'ft', 'feet'],
        help="unit of elevation values. Either 'meter' (the default) or 'feet'. Can be abbreviated as 'm' and 'ft'."
    )
    ap.add_argument(
        '-c', '--case',
        type=str,
        default='lowercase',
        choices=['L', 'lowercase', 'U', 'uppercase'],
        help="case of taxa names. Either 'lowercase' (the default) or 'uppercase'. Can be abbreviated as 'L' and 'U'."
    )
    ap.add_argument(
        '-d', '--digit',
        type=str,
        nargs='+',
        help='set the number of digits used to detect elevation values. Can be useful to avoid matching unwanted numerical values such as trees height. By default, detects any numerical values of one or more digits.'
    )
    ap.add_argument(
        '-p', '--parse_elevs',
        nargs='?',
        const='1',
        help='if set, will parse all elevation values to extract the minimum and maximum elevations for each taxa. Automatically detects the unit and convert elevations to meter. Override the -u/--unit argument.'
    )
    ap.add_argument(
        '-i', '--id',
        nargs='?',
        const='1',
        help="if set, will index each taxa."
    )
    ap.add_argument(
        '-v', '--view',
        nargs='?',
        const='1',
        help='print the text content of a file.'
    )
    ap.add_argument(
        '-n', '--output_name',
        type=str,
        help='name of the output file (without extension).'
    )
    return ap.parse_args()

def process_args():
    args = load_arguments()
    ap = argparse.ArgumentParser()
    args.file = Path(args.file)
    if args.file.suffix.lower() not in ['.txt', '.pdf']:
        ap.error('file must be a .txt or .pdf file')
    if args.digit and len(args.digit) != 2:
        ap.error(f'argument -d/--digit takes 2 values, {len(args.digit)} given')
    if args.parse_elevs and args.unit:
        args.unit = None
    args.outfile = args.file_name = args.file.stem
    if args.output_name:
        args.outfile = args.output_name
    return args
