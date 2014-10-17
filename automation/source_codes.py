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
    return book


def get_source_code_sheet(book):
    sheet = book.sheets()[0]
    return sheet


def get_values(sheet, source_name, view_source_column=2, source_code_column=1):
    view_sources = [vs.value for vs in sheet.col(view_source_column)]
    source_parts = [cell.value for cell in sheet.col(source_code_column)]

    if not view_sources[0].isdigit():
        view_sources = view_sources[1:]
        source_parts = source_parts[1:]

    multiple_view_sources = [view_sources.index(vs)
                             for vs in view_sources
                             if isinstance(vs, (str, unicode)) and '/' in vs]
    for index in multiple_view_sources:
        split = view_sources[index].split('/')
        view_sources[index] = split[0].strip()
        view_sources.append(split[1].strip())
        source_parts.append(source_parts[index])
    view_sources = [int(vs) for vs in view_sources]

    if source_name:
        if source_name[0] not in ['?', '&']:
            source_name = '?%s' % source_name
        if source_name[-1] != '=':
            source_name = '%s=' % source_name
    else:
        source_name = ''

    source_codes = ['%s%s' % (source_name, part) for part in source_parts]

    return zip(view_sources, source_codes)


def add_source_codes(buids, codes):
    for buid in buids:
        for code in codes:
            try:
                dm = DestinationManipulation.objects.get(
                    buid=buid, view_source=code[0], action='sourcecodetag')
            except DestinationManipulation.DoesNotExist:
                DestinationManipulation.objects.create(
                    action_type=1, buid=buid, view_source=code[0],
                    action='sourcecodetag', value_1=code[1], value_2='')
            else:
                dm.value_1 = code[1]
                dm.save()


def process_spreadsheet(location, buids, source_name, view_source_column=2,
                        source_code_column=1, add_codes=True):
    book = get_book(location)
    sheet = get_source_code_sheet(book)
    codes = get_values(sheet, source_name, view_source_column,
                       source_code_column)
    if not isinstance(buids, (list, set)):
        buids = [buids]
    if add_codes:
        add_source_codes(buids, codes)
