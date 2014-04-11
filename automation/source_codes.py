import xlrd

from redirect.models import DestinationManipulation


def get_book(file_name):
    book = xlrd.open_workbook(file_name)
    return book


def get_source_code_sheet(book):
    sheet = book.get_sheet(0)
    return sheet


def get_values(sheet, source_name, view_source_column=2, source_code_column=1):
    view_sources = sheet.col(view_source_column)
    view_sources = [vs.value for vs in view_sources]
    try:
        int(view_sources[0])
    except ValueError:
        header = True
        view_sources = view_sources[1:]
    else:
        header = False
    # TODO: Check for multiple view sources per cell

    source_parts = sheet.col(source_code_column)
    if header:
        source_parts = source_parts[1:]

    if source_name[0] not in ['?', '&']:
        source_name = '?%s' % source_name
    if source_name[-1] != '=':
        source_name = '%s=' % source_name

    source_codes = ['%s%s' % (source_name, part) for part in source_parts]

    return zip(view_sources, source_codes)


def add_source_codes(buids, codes):
    for buid in buids:
        for code in codes:
            try:
                dm = DestinationManipulation.objects.filter(
                    buid=buid, view_source=code[0], action='sourcecodetag')
            except DestinationManipulation.DoesNotExist:
                DestinationManipulation.objects.create(
                    action_type=1, buid=buid, view_source=code[0],
                    action='sourcecodetag', value_1=code[1], value_2='')
            else:
                dm.value_1 = code[1]
                dm.save()


def main(file_name, buids, source_name, view_source_column=2, source_code_column=1):
    book = get_book(file_name)
    sheet = get_source_code_sheet(book)
    codes = get_values(sheet, source_name, view_source_column, source_code_column)
    if not isinstance(buids, (list, set)):
        buids = [buids]
    add_source_codes(buids, codes)
