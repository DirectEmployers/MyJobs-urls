import xlrd

from redirect.models import DestinationManipulation


def get_book(location):
    """
    Creates an xlrd Book from the provided location

    Inputs:
    :location: string or unicode path to a local file or a file-like object

    Outputs:
    :book: instance of xlrd.book.Book
    """
    if not isinstance(location, (unicode, str)):
        book = xlrd.open_workbook(file_contents=location.read())
    else:
        book = xlrd.open_workbook(location)
    setattr(book, 'source_code_sheet', book.sheets()[0])
    return book


def get_values(sheet, source_name, view_source_column=2, source_code_column=1):
    """
    Parse source codes from an Excel worksheet, returning the result

    Inputs:
    :sheet: Excel worksheet that contains source codes
    :source_name: Parameter to use for all source codes (e.g. src for Taleo),
        Pass None if spreadsheet already contains the desired parameter
    :view_source_column: Column containing view sources; 0-based in xlrd,
        default: 2
    :source_code_column: Column containing source codes; 0-based in xlrd,
        default: 1

    Outputs:
        List of tuples: [(view_source_1, source_code), (view_source_2,...)]
    """
    view_sources = [vs.value for vs in sheet.col(view_source_column)]
    source_parts = [cell.value for cell in sheet.col(source_code_column)]

    if not view_sources[0].isdigit():
        # The first row looks like a header; skip it
        # Assumption: the first cell in the view source column does not contain
        # multiple view sources ("1 / 2".isdigit() == False)
        view_sources = view_sources[1:]
        source_parts = source_parts[1:]

    # Make a list of cell indices that contain multiple view sources
    multiple_view_sources = [view_sources.index(vs)
                             for vs in view_sources
                             if isinstance(vs, (str, unicode)) and '/' in vs]

    for index in multiple_view_sources:
        # For each entry that contains two view sources, split it into
        # its components,
        split = view_sources[index].split('/')

        # replace the dual cell with one view source,
        view_sources[index] = split[0].strip()

        # append the remaining view source to the end of the list,
        view_sources.append(split[1].strip())

        # and duplicate the source code across both
        source_parts.append(source_parts[index])
    view_sources = [int(vs) for vs in view_sources]

    # Some files already contain query parameters; in those cases, we don't
    # need to do any additional handling.
    if source_name:
        if source_name[0] not in ['?', '&']:
            source_name = '?%s' % source_name
        if source_name[-1] != '=':
            source_name = '%s=' % source_name
    else:
        source_name = ''

    # Construct source codes from the parameter we were passed (if any)
    # and the values we parsed from the spreadsheet
    source_codes = ['%s%s' % (source_name, part) for part in source_parts]

    return zip(view_sources, source_codes)


def add_source_codes(buids, codes):
    """
    Adds the specified source codes to a list of buids. Does not handle the
    case where there are non-sourcecodetag manipulations for a given buid/vs

    Inputs:
    :buids: List of buids that we are going to add source codes to
    :codes: List of tuples returned by get_values

    Outputs:
    :stats: Dictionary describing what happened in this method; contains the
        number of added and modified source codes as well as the total
    """
    stats = {
        'added': 0,
        'modified': 0,
        'total': len(buids) * len(codes)
    }

    if not isinstance(buids, (list, set)):
        buids = [buids]

    # TODO: refactor this to retrieve a list of manipulations to be modified
    # so we can reduce the number of queries
    for buid in buids:
        for code in codes:
            try:
                dm = DestinationManipulation.objects.get(
                    buid=buid, view_source=code[0], action='sourcecodetag')
            except DestinationManipulation.DoesNotExist:
                stats['added'] += 1
                DestinationManipulation.objects.create(
                    action_type=1, buid=buid, view_source=code[0],
                    action='sourcecodetag', value_1=code[1], value_2='')
            else:
                stats['modified'] += 1
                dm.value_1 = code[1]
                dm.save()
    return stats


def process_spreadsheet(location, buids, source_name, view_source_column=2,
                        source_code_column=1, add_codes=True):
    """
    Chains get_book and get_values, optionally executes add_source_codes

    Inputs:
    :location: Location of Excel spreadsheet, either as a string or in memory
    :buids: List of business units
    :source_name: Parameter name to use for source codes
    :view_source_column: Column of worksheet that contains view sources
    :source_code_column: Column of worksheet that contains source codes
    :add_codes: Boolean denoting whether we should add source codes;
        Default: True

    Outputs:
        If add_codes==True, returns summary of operations
        Else, returns source codes to be added
    """
    book = get_book(location)
    codes = get_values(book.source_code_sheet, source_name, view_source_column,
                       source_code_column)
    if add_codes:
        return add_source_codes(buids, codes)
    else:
        return codes
