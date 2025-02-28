# Generated by Django 3.1.2 on 2020-10-15 18:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Server',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=200)),
                ('weight', models.DecimalField(decimal_places=2, max_digits=3)),
            ],
        ),
        migrations.CreateModel(
            name='SentMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=200)),
                ('status', models.CharField(max_length=200)),
                ('attempt', models.IntegerField(default=0)),
                ('capture_time', models.DateTimeField(verbose_name='time captured')),
                ('latency', models.DecimalField(decimal_places=10, max_digits=19)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wrapper.server')),
            ],
        ),
    ]
