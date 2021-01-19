# Generated by Django 2.1.15 on 2021-01-19 19:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('units', '0018_auto_20210119_1227'),
        ('faults', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='faulttype',
            options={'ordering': ('code',)},
        ),
        migrations.AddField(
            model_name='fault',
            name='treatment_technique',
            field=models.ForeignKey(blank=True, help_text='Select the treatment technique being used when this fault occurred (optional)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='faults', to='units.TreatmentTechnique', verbose_name='treatment technique'),
        ),
        migrations.AlterField(
            model_name='fault',
            name='modality',
            field=models.ForeignKey(blank=True, help_text='Select the modality being used when this fault occurred (optional)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='faults', to='units.Modality', verbose_name='modality'),
        ),
    ]
