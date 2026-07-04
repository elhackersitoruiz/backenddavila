from django.db import migrations, models
import django.db.models.deletion


def migrar_marca_categoria(apps, schema_editor):
    Producto = apps.get_model('tienda', 'Producto')
    Marca = apps.get_model('tienda', 'Marca')
    Categoria = apps.get_model('tienda', 'Categoria')

    for producto in Producto.objects.all():
        nombre_marca = producto.marca_texto.strip()
        marca_obj, _ = Marca.objects.get_or_create(
            nombre__iexact=nombre_marca,
            defaults={'nombre': nombre_marca}
        )
        producto.marca_fk_id = marca_obj.id

        nombre_categoria = producto.categoria_texto.strip()
        categoria_obj, _ = Categoria.objects.get_or_create(
            nombre__iexact=nombre_categoria,
            defaults={'nombre': nombre_categoria}
        )
        producto.categoria_fk_id = categoria_obj.id

        producto.save(update_fields=['marca_fk', 'categoria_fk'])


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0007_remove_producto_proveedor_alter_producto_imagen_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='producto',
            old_name='marca',
            new_name='marca_texto',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='categoria',
            new_name='categoria_texto',
        ),
        migrations.AddField(
            model_name='producto',
            name='marca_fk',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='productos_temp',
                to='tienda.marca',
            ),
        ),
        migrations.AddField(
            model_name='producto',
            name='categoria_fk',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='productos_temp',
                to='tienda.categoria',
            ),
        ),
        migrations.RunPython(migrar_marca_categoria, revertir),
        migrations.RemoveField(
            model_name='producto',
            name='marca_texto',
        ),
        migrations.RemoveField(
            model_name='producto',
            name='categoria_texto',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='marca_fk',
            new_name='marca',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='categoria_fk',
            new_name='categoria',
        ),
        migrations.AlterField(
            model_name='producto',
            name='marca',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='productos',
                to='tienda.marca',
            ),
        ),
        migrations.AlterField(
            model_name='producto',
            name='categoria',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='productos',
                to='tienda.categoria',
            ),
        ),
    ]