# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'ViewSource', fields ['partner_name', 'viewsource_id']
        db.delete_unique(u'viewsource_viewsource', ['partner_name', 'viewsource_id'])

        # Removing unique constraint on 'ViewSource', fields ['viewsource_id']
        db.delete_unique(u'viewsource_viewsource', ['viewsource_id'])

        # Adding field 'ViewSource.buid'
        db.add_column(u'viewsource_viewsource', 'buid',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'ViewSource.date_new'
        db.add_column(u'viewsource_viewsource', 'date_new',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding unique constraint on 'ViewSource', fields ['buid', 'viewsource_id']
        db.create_unique(u'viewsource_viewsource', ['buid', 'viewsource_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'ViewSource', fields ['buid', 'viewsource_id']
        db.delete_unique(u'viewsource_viewsource', ['buid', 'viewsource_id'])

        # Deleting field 'ViewSource.buid'
        db.delete_column(u'viewsource_viewsource', 'buid')

        # Deleting field 'ViewSource.date_new'
        db.delete_column(u'viewsource_viewsource', 'date_new')

        # Adding unique constraint on 'ViewSource', fields ['viewsource_id']
        db.create_unique(u'viewsource_viewsource', ['viewsource_id'])

        # Adding unique constraint on 'ViewSource', fields ['partner_name', 'viewsource_id']
        db.create_unique(u'viewsource_viewsource', ['partner_name', 'viewsource_id'])


    models = {
        u'viewsource.viewsource': {
            'Meta': {'unique_together': "(('viewsource_id', 'buid'),)", 'object_name': 'ViewSource'},
            'buid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date_new': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'partner_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'partner_url': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'redirect_url': ('django.db.models.fields.URLField', [], {'max_length': '300', 'blank': 'True'}),
            'source_code': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'viewsource_id': ('django.db.models.fields.IntegerField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['viewsource']