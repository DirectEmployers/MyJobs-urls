from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from redirect.models import *


class MultiSearchFilter(admin.FieldListFilter):
    """
    Allows the selection of multiple values in a Django admin filter list.
    """
    def __init__(self, field, request, params, model, model_admin, field_path):
        super(MultiSearchFilter, self).__init__(field, request, params, model,
                                                model_admin, field_path)
        self.filter_parameters = request.GET.get(self.field_path, None)
        self.field_choices = field.get_choices(include_blank=False)

    def expected_parameters(self):
        return [self.field_path]

    def values(self):
        values = []
        value = self.used_parameters.get(self.field_path, None)
        if value:
            values = value.split(',')
        return values

    def queryset(self, request, queryset):
        values = self.values()
        filter_query = {'%s__in' % self.field_path : values}
        if values:
            return queryset.filter(**filter_query)
        else:
            return queryset

    def choices(self, cl):
        yield {
            'selected': self.filter_parameters is None,
            'query_string': cl.get_query_string({}, [self.field_path]),
            'display': _('All')}

        for name, value in self.field_choices:
            selected = name in self.values()
            name_list = set(self.values())
            if selected:
                name_list.remove(name)
            else:
                name_list.add(name)
            if name_list:
                query_string = cl.get_query_string(
                    {self.field_path: ','.join(name_list)})
            else:
                query_string = cl.get_query_string({}, [self.field_path])
            yield {
                'selected': selected,
                'query_string': query_string,
                'display': value}


class BlankValueListFilter(admin.SimpleListFilter):
    """
    Filters :field_name: based on whether or not that field has valuable text
    or is [Null, '[blank]', or '']

    Should only be used via a subclass which defines title, parameter_name,
    and field_name
    """
    title = ''
    parameter_name = ''

    field_name = ''

    def lookups(self, request, model_admin):
        return (
            ('Blank', _('Field is blank')),
            ('Exists', _('Field exists')))

    def queryset(self, request, queryset):
        query = Q(**{self.field_name: '[blank]'}) | \
                Q(**{self.field_name: ''}) | \
                Q(**{'%s__isnull' % self.field_name: True})
        if self.value() == 'Blank':
            return queryset.filter(query)
        elif self.value() == 'Exists':
            return queryset.exclude(query)
        else:
            return queryset


class BlankValueList1Filter(BlankValueListFilter):
    title = _('Value 1')
    parameter_name = 'value_1'
    field_name='value_1'


class BlankValueList2Filter(BlankValueListFilter):
    title = _('Value 2')
    parameter_name = 'value_2'
    field_name='value_2'


class DestinationManipulationAdmin(admin.ModelAdmin):
    list_filter = ['action_type',
                   ('action', MultiSearchFilter),
                   BlankValueList1Filter,
                   BlankValueList2Filter]
    search_fields = ['=buid', '=view_source']
    list_display = ['buid', 'get_view_source_name', 'action_type',
                    'action', 'value_1', 'value_2']


class ExcludedViewSourceAdmin(admin.ModelAdmin):
    list_display = ['view_source']


class CustomExcludedViewSourceAdmin(admin.ModelAdmin):
    list_display = ['buid', 'view_source']
    search_fields = ['buid', 'view_source']


class ViewSourceAdmin(admin.ModelAdmin):
    list_display = ['view_source_id', 'name', 'microsite']
    list_filter = ['microsite']
    search_fields = ['=view_source_id', 'name']

    def get_readonly_fields(self, request, obj=None):
        """
        If a new object is being created, leave view_source_id editable.
        If the user is viewing an existing object, make it read-only.
        """
        if obj:
            return self.readonly_fields + ('view_source_id',)
        else:
            return []


admin.site.register(ViewSource, ViewSourceAdmin)
admin.site.register(DestinationManipulation, DestinationManipulationAdmin)
admin.site.register(ExcludedViewSource, ExcludedViewSourceAdmin)
admin.site.register(CustomExcludedViewSource, CustomExcludedViewSourceAdmin)
