# Generated by Django 5.0 on 2023-12-20 20:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sea_combat', '0006_remove_gamestate_curturn_gamestate_isplayeroneturn'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamestate',
            name='lastTurnNum',
            field=models.IntegerField(default=0),
        ),
    ]