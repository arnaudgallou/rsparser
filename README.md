Parse species' elevation data from `.pdf` or `.txt` files.

# Usage

```
python3 rsparser.py file
```

For help, use:
```
python3 rsparser.py -h
```

# Options

`-s`, `--start`: word or character string that delimits the starting point of the parser.

`-e`, `--end`: word or character string that delimits the ending point of the parser.

`-u`, `--unit`: unit of elevation values. Either `meter` (the default) or `feet`. Can be abbreviated as `m` and `ft`.

`-c`, `--case`: case of taxa names. Either `lowercase` (the default) or `uppercase`. Can be abbreviated as `L` and `U`.

`-d`, `--digit`: set the number of digits used to detect elevation values. Can be useful to avoid matching unwanted numerical values such as trees height. By default, detects any numerical values of one or more digits.

`-p`, `--parse_elevs`: if set, will parse all elevation values to extract the minimum and maximum elevations for each taxa. Automatically detects the unit and converts elevations to meter. Override the `-u`/`--unit` argument.

`-i`, `--id`: if set, will index each taxa.

`-v`, `--view`: print the text content of a file.

`-n`, `--output_name`: name of the output file.

# Dependencies

The parser requires to have `Python 3.x` as well as the `pdftotext`, `regex` and `pandas` modules installed.

# Examples

Parsing a `.txt` file with elevation values in feet and taxa names in uppercase:
```
python3 rsparser.py file.txt -u ft -c uppercase -i
```

Parsing a specific section of the file using the `-s`/`--start` and `-e`/`--end` arguments with an anchor. The anchor can be any word or character string at the beginning of a line.
```
python3 rsparser.py file.pdf --start Checklist --end 'Literature cited'
```

Extracting taxa with elevation values between 3 and 4 digits only:
```
python3 rsparser.py file.pdf -d 3 4
```

# Editing the file content

It is sometimes useful to edit or remove content from the file (e.g. special characters before taxa names, page's header and footer) for better results. You can use the `fsub` dictionary for that purpose. Simply add new keys with a list of patterns and replacements as values. **Keys must be the name of the files to parse.**

For example:
```
fsub = {
  'file_name1': [(r'\n\K\p{Greek}', ''), ('ﬃ', 'ffi')], # removes all leading Greek letters and replace the character 'ﬃ' with 'ffi' in file_name1
  'file_name2': [('\n.*(?:Phytotaxa|Smith et al)[^\n]+', '')] # removes any lines containing 'Phytotaxa' or 'Smith et al' in file_name2
}
```

# Notes

In some cases, `pdftotext` struggles with reading multi-column `.pdf` files properly. It is particularly true for scans that were converted to text using OCR tools. In such cases, I would recommend splitting the `.pdf` files into individual columns (e.g. using [`mutool`](https://www.mupdf.com/docs/manual-mutool-poster.html)) before parsing them.
