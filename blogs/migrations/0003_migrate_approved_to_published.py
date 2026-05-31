from django.db import migrations


def forwards(apps, schema_editor):
    Blog = apps.get_model('blogs', 'Blog')
    db_alias = schema_editor.connection.alias
    Blog.objects.using(db_alias).filter(status='approved').update(status='published')


def backwards(apps, schema_editor):
    Blog = apps.get_model('blogs', 'Blog')
    db_alias = schema_editor.connection.alias
    Blog.objects.using(db_alias).filter(status='published').update(status='approved')


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0002_blog_approved_by'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
