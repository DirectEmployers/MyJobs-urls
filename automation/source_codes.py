from django.db import transaction

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
    # Make source codes easy to look up by view source
    code_dict = {code[0]: code for code in codes}

    if not isinstance(buids, (list, set)):
        buids = [buids]
    # Pulling buids from the database returns integers; In order to do set
    # operations between the two, these need to be ints as well
    buids = [int(buid) for buid in buids]

    all_view_sources = [code[0] for code in codes]
    all_manipulations = set((buid, vs) for buid in buids
                            for vs in all_view_sources)
    existing = set(DestinationManipulation.objects.filter(
        buid__in=buids, view_source__in=all_view_sources,
        action='sourcecodetag').values_list('buid', 'view_source'))
    new = all_manipulations.difference(existing)

    stats = {
        'added': len(new),
        'modified': len(existing),
        'total': len(all_manipulations)
    }

    # Bulk create manipulations that don't exist yet
    new_list = []
    for new_info in new:
        manipulation_info = code_dict[new_info[0]]
        new_list.append(DestinationManipulation(
            action_type=1, buid=new_info[0], view_source=manipulation_info[0],
            action='sourcecodetag', value_1=manipulation_info[1]))
    DestinationManipulation.objects.bulk_create(new_list)

    # Doesn't work; leaving this so there is a commit record
    #DestinationManipulation.objects.filter(
    #    buid__in=[info[0] for info in existing],
    #    view_source__in=[info[1] for info in existing],
    #    action='sourcecodetag').update(value_1=code_dict[F('view_source')][1])
    # Committing manually after all of this is supposed to be faster than
    # after each individual operation. Found originally at the first link,
    # new 1.6 functionality at the second. This still does one query per update
    # http://voorloopnul.com/blog/doing-bulk-update-and-bulk-create-with-django-orm/
    # https://docs.djangoproject.com/en/1.6/topics/db/transactions/#id5
    transaction.set_autocommit(False)
    try:
        for existing_info in existing:
            manipulation_info = code_dict[existing_info[0]]
            DestinationManipulation.objects.filter(
                buid=existing_info[0], view_source=manipulation_info[0],
                action='sourcecodetag').update(
                    value_1=manipulation_info[1])
    finally:
        transaction.set_autocommit(True)

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
