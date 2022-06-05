from pdftotext import PDF
from pathlib import Path
from fsub import fsub
import options
import pandas
import regex


HYBR = r'(?:×\s?)?'
BRKT = r'(?:\([^)]+\)\s?)?'
INFSP_RANK = r'\b(?i:f|ssp|subsp|var)\.'
LOWER_TAXA = r'\p{Ll}{3,}(?:-?\p{Ll}{3,})?'
LVL_GRPS = rf'^{HYBR}\pL+\s(\pL+).+?{INFSP_RANK}\s(\pL+)'
INFSP_TAIL = rf'{INFSP_RANK}\s[\p{{Ll}}-]+\K.*'
LOWERCASE = rf'^{HYBR}[A-Z]\K\pL+\s[\pL-]+|[^.]\K{INFSP_RANK}\s[\pL-]+'
PREFIX = rf'^{HYBR}[A-Z]\p{{Ll}}+\s{HYBR}{LOWER_TAXA}'
head = rf'{PREFIX}\s?(?:{BRKT}\p{{Lu}}|{INFSP_RANK})'
taxa = rf"{PREFIX}(\s?{BRKT}(?:\pL{{1,3}}\s){{0,2}}(\p{{Lu}}[\pL\pM.'-]+(?:\sf\.)?)(?:,\s(?2)(?=\s&))?((?:\s(?:&|ex)\s(?2))?)(?3))(?:\s(?:×|{INFSP_RANK})\s?{LOWER_TAXA}(?1)?)?"
elev = r'(?:\b|\pL)\K\d+(?:\s?-\s?\d+)?(?=\s?m\b)'


class Regex:
    def __init__(self, pattern):
        self.pattern = pattern

    @property
    def to_upper(self):
        self.pattern = self.pattern.replace('Ll', 'Lu')
        return self

    @property
    def to_ft(self):
        self.pattern = self.pattern.replace('m', 'ft')
        return self

    @property
    def to_m_ft(self):
        self.pattern = self.pattern.replace(r'(?=\s?m\b)', r'\s?(?:m|ft)\b')
        return self

    def set_digit_range(self, values):
        self.pattern = self.pattern.replace('d+', f'd{{{values[0]},{values[1]}}}')
        return self


class File:
    def __init__(self, file):
        self.file = file
        self.text = None

    def __str__(self):
        return self.text

    def read(self):
        extension = Path(self.file).suffix.lower()
        if extension not in ['.txt', '.pdf']:
            raise ValueError('Can only read a .txt or .pdf file.')
        is_txt_file = extension == '.txt'
        mode = 'r' if is_txt_file else 'rb'
        with open(self.file, mode) as f:
            self.text = f.read() if is_txt_file else ''.join(page for page in PDF(f, raw=True))
        return self

    def sanitize(self, patterns=None):
        if patterns and not isinstance(patterns, list):
            raise TypeError('Patterns must be a list.')
        subst = [
            (' +', ' '),
            ('[\n\f\r]{2,}', '\n'),
            ('[-—–]+', '-'),
            (r"[`'‘’“”\"]+", "'"),
            (r'\b(?:et|and)\b', '&'),
            (r'\b\p{Lu}\.\K\s(?=\p{Lu})|\p{Ll}(?:\K-\n(?=\p{Ll})|-\K\n(?=\p{Lu}))|\n\K\d{1,3}\n|\d-\K\s+(?=\d+ ?(?:m|ft)\b)', ''),
            (r'(?:\([\pL. ]+|[\p{Ll}.]\)|&|\bex)\K\n|\p{Ll}{2,}\K(?=\p{Lu})|(\b(?i:f|ssp|subsp|var)\.)(?:\s?[a-z-]+)?\K\n|\d\K\n(?=m\b)|\n(?=(?1))', ' ')
        ]
        if patterns:
            subst += [x for x in patterns]
        self.text = msub(subst, self.text)


class Parser:
    def __init__(self, text, opts):
        self.head = Regex(head)
        self.taxa = Regex(taxa)
        self.elev = Regex(elev)
        self.text = text
        self.opts = opts
        self.data = []
        self.lines = []
        if self.opts.case in ['U', 'uppercase']:
            self.head, self.taxa = [x.to_upper for x in [self.head, self.taxa]]
        if self.opts.parse_elevs:
            self.elev = self.elev.to_m_ft
        elif self.opts.unit in ['ft', 'feet']:
            self.elev = self.elev.to_ft
        if self.opts.digit:
            self.elev = self.elev.set_digit_range(self.opts.digit)

    def process_text(self):
        """Reshape text to gather taxa info on individual lines."""
        head = self.head.pattern
        tail = self.elev.pattern
        parse_elevs = self.opts.parse_elevs
        flag = 0
        skip = True
        for line in self.text.splitlines():
            line = line.strip()
            if self.opts.end and line.startswith(self.opts.end):
                break
            elif self.opts.start and skip and line.startswith(self.opts.start):
                skip = False
            elif self.opts.start and skip:
                continue
            elif not parse_elevs and regex.search(head, line) and regex.search(tail, line):
                self.lines.append(f'\n{line}')
                flag = 0
            elif regex.search(head, line):
                self.lines.append(f'\n{line};')
                flag = 1
            elif not parse_elevs and flag and regex.search(tail, line):
                self.lines.append(f' {line}')
                flag = 0
            elif flag:
                self.lines.append(f' {line}')
            else:
                continue

    def extract_data(self):
        content = ''.join(self.lines)
        for line in content.splitlines():
            try:
                elev = self.get_elev(line)
            except (TypeError, ValueError):
                continue
            try:
                taxa = self.get_taxa(line, self.taxa.pattern)
            except TypeError:
                taxa = self.get_taxa(line, r"^[\pL&()'., -]+")
            self.data.append([taxa, *elev])

    def parse_elevs(self, string):
        out = []
        for i in regex.findall(self.elev.pattern, string):
            elevs = [int(e) for e in regex.findall(r'\d+', i)]
            if i[-2:] == 'ft':
                elevs = [ft_to_m(e) for e in elevs]
            out.extend(elevs)
        return out

    def get_elev(self, string):
        if self.opts.parse_elevs:
            elevs = self.parse_elevs(string)
            min_elev = min(elevs)
            max_elev = max(elevs)
        else:
            range_ = regex.search(self.elev.pattern, string)[0]
            elevs = [regex.search(x, range_)[0] for x in [r'^\d+', r'\d+$']]
            unit_is_ft = self.opts.unit in ['ft', 'feet']
            min_elev, max_elev = [ft_to_m(e) if unit_is_ft else int(e) for e in elevs]
        return (min_elev, max_elev)

    def get_taxa(self, string, pattern):
        taxa = regex.search(pattern, string)[0]
        if self.opts.case in ['U', 'uppercase']:
            taxa = _taxa_to_lower(taxa)
        return _clean_taxa(taxa)


def _taxa_to_lower(string):
    return regex.sub(LOWERCASE, lambda x: x.group().lower(), string)

def _clean_taxa(string):
    patterns = [(r'^[^A-Za-z]+|(?!\.)[^\pL]+$', ''), (r'\s+', ' ')]
    string = msub(patterns, string)
    if any(x in string for x in [' f.', ' ssp.', ' subsp.', ' var.']):
        taxa_lvl = regex.search(LVL_GRPS, string.replace('-', ''))
        try:
            infsp_is_sp = taxa_lvl.group(1) == taxa_lvl.group(2)
            string = regex.sub(INFSP_TAIL, '', string) if infsp_is_sp else string
        except AttributeError:
            pass
    return string

def ft_to_m(elev):
    return int(round(int(elev) * 0.3048, -1))

def msub(patterns, string):
    for pattern, replacement in patterns:
        string = regex.sub(pattern, replacement, string)
    return string

def write_csv(data, path, cols, sep=';', index=False):
    df = pandas.DataFrame(data, columns=cols)
    if index:
        df.index += 1
    return df.to_csv(f'{path}.csv', sep=sep, index=index, index_label='id')

def main():
    args = options.process_args()
    file = File(args.file).read()
    patterns = fsub[args.file_name] if args.file_name in fsub else None
    file.sanitize(patterns)
    if args.view:
        print(file)
        raise SystemExit
    parser = Parser(file.text, args)
    parser.process_text()
    parser.extract_data()
    Path('extracted').mkdir(exist_ok=True)
    index = True if args.id else False
    write_csv(
        parser.data,
        f'extracted/{args.outfile}',
        cols=['scientificName', 'elev_min', 'elev_max'],
        index=index
    )

if __name__ == '__main__':
    main()
