# ================================================================
# Carga de CSVs a BigQuery
# Trunca y recarga cada tabla con los datos generados
# ================================================================

from google.cloud import bigquery
import os

# ── Configuración ─────────────────────────────────────────────
PROJECT_ID = 'afiliados-490100'
DATASET    = 'DW'
INPUT_DIR  = 'output_data'
# ──────────────────────────────────────────────────────────────

client = bigquery.Client(project=PROJECT_ID)

# Esquemas explícitos por tabla (evita ambigüedades en booleanos y fechas)
SCHEMAS = {
    'DIM_AFFILIATES': [
        bigquery.SchemaField('AFFILIATE_ID',              'INTEGER'),
        bigquery.SchemaField('MELI_USERNAME',             'STRING'),
        bigquery.SchemaField('MELI_USER_ID',              'INTEGER'),
        bigquery.SchemaField('COUNTRY',                   'STRING'),
        bigquery.SchemaField('CATEGORY',                  'STRING'),
        bigquery.SchemaField('INSTAGRAM_HANDLE',          'STRING'),
        bigquery.SchemaField('INSTAGRAM_FOLLOWER_COUNT',  'FLOAT'),
        bigquery.SchemaField('TIKTOK_HANDLE',             'STRING'),
        bigquery.SchemaField('TIKTOK_FOLLOWER_COUNT',     'FLOAT'),
    ],
    'FACTS_REGISTERED_SOCIAL_MEDIA': [
        bigquery.SchemaField('SM_ID',        'INTEGER'),
        bigquery.SchemaField('AFFILIATE_ID', 'INTEGER'),
        bigquery.SchemaField('SOCIAL_MEDIA', 'STRING'),
        bigquery.SchemaField('URL',          'STRING'),
        bigquery.SchemaField('FOLLOWERS',    'INTEGER'),
    ],
    'FACTS_JIRA_HUNTING_AFILIADOS': [
        bigquery.SchemaField('JIRA_KEY',        'STRING'),
        bigquery.SchemaField('MELI_USERNAME',   'STRING'),
        bigquery.SchemaField('HUNTER',          'STRING'),
        bigquery.SchemaField('NOMBRE',          'STRING'),
        bigquery.SchemaField('ULTIMO_CONTACTO', 'DATE'),
        bigquery.SchemaField('INSTAGRAM',       'STRING'),
        bigquery.SchemaField('TIKTOK',          'STRING'),
        bigquery.SchemaField('asignado',        'BOOLEAN'),
        bigquery.SchemaField('contactado',      'BOOLEAN'),
        bigquery.SchemaField('afiliado',        'BOOLEAN'),
        bigquery.SchemaField('rechazado',       'BOOLEAN'),
    ],
    'FACTS_MARKETPLACE_AFFILIATE_URLS': [
        bigquery.SchemaField('URL',                    'STRING'),
        bigquery.SchemaField('AFFILIATE_ID',           'INTEGER'),
        bigquery.SchemaField('MARKETPLACE_PRODUCT_ID', 'STRING'),
        bigquery.SchemaField('CREATED_AT',             'DATE'),
        bigquery.SchemaField('CLOSED_AT',              'DATE'),
    ],
    'FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS': [
        bigquery.SchemaField('URL',             'STRING'),
        bigquery.SchemaField('MELI_USERNAME',   'STRING'),
        bigquery.SchemaField('ACCESS_DATETIME', 'DATETIME'),
    ],
    'FACTS_AFFILIATES_MARKETPLACE_SALES': [
        bigquery.SchemaField('URL',                    'STRING'),
        bigquery.SchemaField('AFFILIATE_ID',           'INTEGER'),
        bigquery.SchemaField('BUYER_MELI_USER_ID',     'INTEGER'),
        bigquery.SchemaField('MARKETPLACE_PRODUCT_ID', 'STRING'),
        bigquery.SchemaField('PURCHASE_DATETIME',      'DATETIME'),
        bigquery.SchemaField('COUNTRY',                'STRING'),
        bigquery.SchemaField('CURRENCY',               'STRING'),
        bigquery.SchemaField('PRICE',                  'FLOAT'),
    ],
    'DIM_AFFILIATES_MARKETPLACE_PRODUCTS': [
        bigquery.SchemaField('MARKETPLACE_PRODUCT_ID', 'STRING'),
        bigquery.SchemaField('SELLER_MELI_USER_ID',    'INTEGER'),
        bigquery.SchemaField('TITLE',                  'STRING'),
        bigquery.SchemaField('CATEGORY_AGG_1',         'STRING'),
        bigquery.SchemaField('CATEGORY_AGG_2',         'STRING'),
        bigquery.SchemaField('CATEGORY_AGG_3',         'STRING'),
        bigquery.SchemaField('CONDITION',              'STRING'),
        bigquery.SchemaField('VISIBLE',                'BOOLEAN'),
        bigquery.SchemaField('AVAILABLE_UNITS',        'INTEGER'),
        bigquery.SchemaField('PUBLICATION_DATETIME',   'DATE'),
        bigquery.SchemaField('CALIFICATION',           'FLOAT'),
        bigquery.SchemaField('OPINIONS',               'INTEGER'),
    ]
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
