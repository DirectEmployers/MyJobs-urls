# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ViewSource'
        db.create_table(u'viewsource_viewsource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('viewsource_id', self.gf('django.db.models.fields.IntegerField')(unique=True, blank=True)),
            ('partner_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('partner_url', self.gf('django.db.models.fields.URLField')(max_length=300)),
            ('source_code', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
            ('redirect_url', self.gf('django.db.models.fields.URLField')(max_length=300, blank=True)),
        ))
        db.send_create_signal(u'viewsource', ['ViewSource'])

        # Adding unique constraint on 'ViewSource', fields ['viewsource_id', 'partner_name']
        db.create_unique(u'viewsource_viewsource', ['viewsource_id', 'partner_name'])


    def backwards(self, orm):
        # Removing unique constraint on 'ViewSource', fields ['viewsource_id', 'partner_name']
        db.delete_unique(u'viewsource_viewsource', ['viewsource_id', 'partner_name'])

        # Deleting model 'ViewSource'
        db.delete_table(u'viewsource_viewsource')


    models = {
        u'viewsource.viewsource': {
            'Meta': {'unique_together': "(('viewsource_id', 'partner_name'),)", 'object_name': 'ViewSource'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'partner_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'partner_url': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'redirect_url': ('django.db.models.fields.URLField', [], {'max_length': '300', 'blank': 'True'}),
            'source_code': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'viewsource_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['viewsource']