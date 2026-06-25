# ================================================================
# Carga de CSVs a BigQuery
# Trunca y recarga cada tabla con los datos generados
# ================================================================

from google.cloud import bigquery
import os

# ── Configuración ─────────────────────────────────────────────
PROJECT_ID = 'afiliados-490100'
DATASET    = 'DW'
INPUT_DIR  = 'dw/output_data'
# ──────────────────────────────────────────────────────────────

client = bigquery.Client(project=PROJECT_ID)

# Esquemas explícitos por tabla (evita ambigüedades en booleanos y fechas)
SCHEMAS = {
    'DIM_AFFILIATES': [
        bigquery.SchemaField('AFFILIATE_ID',             'INTEGER', description='Clave primaria'),
        bigquery.SchemaField('MELI_USERNAME',            'STRING',  description='Username en Mercado Libre'),
        bigquery.SchemaField('MELI_USER_ID',             'INTEGER', description='ID numérico de usuario en MELI'),
        bigquery.SchemaField('AFFILIATED_AT',            'DATE',    description='Fecha en que se incorporó al programa'),
        bigquery.SchemaField('COUNTRY',                  'STRING',  description='País (ARG · BRA · CHI · MEX)'),
        bigquery.SchemaField('CATEGORY',                 'STRING',  description='Nicho de contenido del afiliado'),
        bigquery.SchemaField('INSTAGRAM_HANDLE',         'STRING',  description='Handle de Instagram (sin @), puede ser NULL'),
        bigquery.SchemaField('INSTAGRAM_FOLLOWER_COUNT', 'INTEGER', description='Seguidores en Instagram'),
        bigquery.SchemaField('TIKTOK_HANDLE',            'STRING',  description='Handle de TikTok (sin @), puede ser NULL'),
        bigquery.SchemaField('TIKTOK_FOLLOWER_COUNT',    'INTEGER', description='Seguidores en TikTok'),
    ],
    'FACTS_REGISTERED_SOCIAL_MEDIA': [
        bigquery.SchemaField('SM_ID',        'INTEGER', description='Clave primaria'),
        bigquery.SchemaField('AFFILIATE_ID', 'INTEGER', description='FK → DIM_AFFILIATES'),
        bigquery.SchemaField('SOCIAL_MEDIA', 'STRING',  description='Plataforma (instagram · tiktok · youtube · facebook · x · other)'),
        bigquery.SchemaField('URL',          'STRING',  description='URL del perfil'),
        bigquery.SchemaField('FOLLOWERS',    'INTEGER', description='Seguidores al momento del registro'),
    ],
    'FACTS_JIRA_HUNTING_AFILIADOS': [
        bigquery.SchemaField('JIRA_KEY',         'STRING',  description='Clave del ticket en Jira'),
        bigquery.SchemaField('MELI_USERNAME',    'STRING',  description='Username en MELI del lead (NULL si no tiene cuenta)'),
        bigquery.SchemaField('HUNTER',           'STRING',  description='Nombre del hunter asignado (displayName en Jira)'),
        bigquery.SchemaField('HUNTER_JIRA_ID',   'STRING',  description='accountId del hunter en Jira (NULL si lead en pool)'),
        bigquery.SchemaField('NOMBRE',           'STRING',  description='Nombre del prospecto'),
        bigquery.SchemaField('FECHA_ASIGNACION', 'DATE',    description='Fecha en que se asignó el lead al hunter'),
        bigquery.SchemaField('ULTIMO_CONTACTO',  'DATE',    description='Fecha del último contacto con el lead'),
        bigquery.SchemaField('INSTAGRAM',        'STRING',  description='Handle de Instagram del lead'),
        bigquery.SchemaField('TIKTOK',           'STRING',  description='Handle de TikTok del lead'),
        bigquery.SchemaField('ESTADO',           'STRING',  description='Estado en el funnel (pool · asignado · contactado · afiliado · rechazado)'),
        bigquery.SchemaField('ASIGNADO',         'BOOLEAN', description='TRUE si el lead fue asignado a un hunter'),
        bigquery.SchemaField('CONTACTADO',       'BOOLEAN', description='TRUE si el hunter contactó al lead al menos una vez'),
        bigquery.SchemaField('AFILIADO',         'BOOLEAN', description='TRUE si el lead se convirtió en afiliado'),
        bigquery.SchemaField('RECHAZADO',        'BOOLEAN', description='TRUE si el lead fue rechazado'),
    ],
    'FACTS_MARKETPLACE_AFFILIATE_URLS': [
        bigquery.SchemaField('URL',                    'STRING',  description='Clave primaria — link único de afiliado'),
        bigquery.SchemaField('AFFILIATE_ID',           'INTEGER', description='FK → DIM_AFFILIATES'),
        bigquery.SchemaField('MARKETPLACE_PRODUCT_ID', 'STRING',  description='FK → DIM_AFFILIATES_MARKETPLACE_PRODUCTS'),
        bigquery.SchemaField('CREATED_AT',             'DATE',    description='Fecha de creación del link'),
        bigquery.SchemaField('CLOSED_AT',              'DATE',    description='Fecha en que se desactivó el link (NULL si sigue activo)'),
    ],
    'FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS': [
        bigquery.SchemaField('URL',             'STRING',   description='FK → FACTS_MARKETPLACE_AFFILIATE_URLS'),
        bigquery.SchemaField('MELI_USERNAME',   'STRING',   description='Usuario de MELI que hizo el clic'),
        bigquery.SchemaField('ACCESS_DATETIME', 'DATETIME', description='Fecha y hora exacta del clic'),
    ],
    'FACTS_AFFILIATES_MARKETPLACE_SALES': [
        bigquery.SchemaField('URL',                    'STRING',   description='FK → FACTS_MARKETPLACE_AFFILIATE_URLS'),
        bigquery.SchemaField('AFFILIATE_ID',           'INTEGER',  description='FK → DIM_AFFILIATES'),
        bigquery.SchemaField('BUYER_MELI_USER_ID',     'INTEGER',  description='ID del comprador en MELI'),
        bigquery.SchemaField('MARKETPLACE_PRODUCT_ID', 'STRING',   description='FK → DIM_AFFILIATES_MARKETPLACE_PRODUCTS'),
        bigquery.SchemaField('PURCHASE_DATETIME',      'DATETIME', description='Fecha y hora de la compra'),
        bigquery.SchemaField('COUNTRY',                'STRING',   description='País donde se realizó la compra'),
        bigquery.SchemaField('CURRENCY',               'STRING',   description='Moneda local (ARS · BRL · CLP · MXN)'),
        bigquery.SchemaField('PRICE',                  'FLOAT',    description='Precio en moneda local'),
    ],
    'DIM_AFFILIATES_MARKETPLACE_PRODUCTS': [
        bigquery.SchemaField('MARKETPLACE_PRODUCT_ID', 'STRING',  description='Clave primaria (ej. MLA-1234567)'),
        bigquery.SchemaField('SELLER_MELI_USER_ID',    'INTEGER', description='ID del vendedor en MELI'),
        bigquery.SchemaField('TITLE',                  'STRING',  description='Título del producto'),
        bigquery.SchemaField('CATEGORY_AGG_1',         'STRING',  description='Categoría nivel 1 (ej. Electrónica)'),
        bigquery.SchemaField('CATEGORY_AGG_2',         'STRING',  description='Categoría nivel 2 (ej. Celulares y Teléfonos)'),
        bigquery.SchemaField('CATEGORY_AGG_3',         'STRING',  description='Categoría nivel 3 (ej. Smartphones)'),
        bigquery.SchemaField('CONDITION',              'STRING',  description='Estado del producto (new · used)'),
        bigquery.SchemaField('VISIBLE',                'BOOLEAN', description='Si el producto está publicado actualmente'),
        bigquery.SchemaField('AVAILABLE_UNITS',        'INTEGER', description='Stock disponible'),
        bigquery.SchemaField('PUBLICATION_DATETIME',   'DATE',    description='Fecha de publicación original'),
        bigquery.SchemaField('CALIFICATION',           'FLOAT',   description='Calificación promedio (1.0 – 5.0)'),
        bigquery.SchemaField('OPINIONS',               'INTEGER', description='Cantidad de opiniones recibidas'),
    ],
}

def cargar_tabla(table_name):
    csv_path  = os.path.join(INPUT_DIR, table_name + '.csv')
    table_ref = f'{PROJECT_ID}.{DATASET}.{table_name}'

    job_config = bigquery.LoadJobConfig(
        schema            = SCHEMAS[table_name],
        skip_leading_rows = 1,
        source_format     = bigquery.SourceFormat.CSV,
        write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE,
        null_marker       = '',
    )

    with open(csv_path, 'rb') as f:
        job = client.load_table_from_file(f, table_ref, job_config=job_config)

    job.result()  # espera a que termine

    tabla = client.get_table(table_ref)
    print(f'  OK  {table_name:<50} {tabla.num_rows:>9,} filas')


print(f'Proyecto : {PROJECT_ID}')
print(f'Dataset  : {DATASET}')
print('-' * 72)

errores = []
for table_name in SCHEMAS:
    try:
        cargar_tabla(table_name)
    except Exception as e:
        print(f'  ERROR  {table_name}: {e}')
        errores.append(table_name)

print('-' * 72)
if errores:
    print(f'Tablas con error: {errores}')
else:
    print('Todas las tablas cargadas correctamente.')
