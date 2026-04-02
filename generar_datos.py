# ================================================================
# Generación de Datos — Bootcamp BI Analyst
# Programa de Afiliados Mercado Libre
# ================================================================
#
# Tablas generadas:
#   DIM_AFFILIATES                            — dimensión de afiliados
#   FACTS_REGISTERED_SOCIAL_MEDIA             — redes sociales por afiliado
#   FACTS_JIRA_HUNTING_AFILIADOS              — tablero operativo de hunting
#   FACTS_MARKETPLACE_AFFILIATE_URLS          — links de afiliado
#   FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS  — clicks a links de afiliado
#   FACTS_AFFILIATES_MARKETPLACE_SALES        — ventas generadas
#   DIM_AFFILIATES_MARKETPLACE_PRODUCTS       — catálogo de productos
#   FACTS_USD_EXCHANGE_RATES                  — tipos de cambio semanales
# ================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ================================================================
# SECCIÓN 1 — Imports & Configuración
# ================================================================

SEED = 42
rng  = np.random.default_rng(SEED)
random.seed(SEED)

OUTPUT_DIR = 'output_data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

TODAY      = datetime(2026, 8, 1)
JIRA_START = TODAY - timedelta(days=90)

PROGRAM_LAUNCH = {
    'BRA': TODAY - timedelta(days=365 * 3),
    'MEX': TODAY - timedelta(days=365 * 3),
    'ARG': TODAY - timedelta(days=365),
    'CHI': TODAY - timedelta(days=365),
}

# ── ESCALA (ajustar libremente) ────────────────────────────────
N_AFFILIATES         = 5_000        # total de afiliados en el programa
N_JIRA_TOTAL         = 1_000      # total de leads en el tablero Jira
N_PRODUCT_POOL       = 10_000     # productos en el pool del marketplace
N_TARGET_ACCESS_LOGS = 75_000     # volumen total de access logs (ajustar libremente)
# ──────────────────────────────────────────────────────────────

COUNTRIES = ['BRA', 'MEX', 'ARG', 'CHI']
COUNTRY_W = [0.30,  0.30,  0.20,  0.20]

CATEGORIES = [
    'lifestyle', 'home_deco', 'fitness', 'travel',
    'education', 'tech', 'beauty', 'food', 'other',
]

PLATFORMS = ['instagram', 'tiktok', 'youtube', 'facebook', 'x', 'other']

MELI_CODE = {'ARG': 'MLA', 'BRA': 'MLB', 'MEX': 'MLM', 'CHI': 'MLC'}

CURRENCY_MAP = {'ARG': 'ARS', 'BRA': 'BRL', 'MEX': 'MXN', 'CHI': 'CLP'}

# Valores ancla de tipo de cambio (moneda local por 1 USD, aprox. 2026)
FX_ANCHOR = {'ARS': 1100.0, 'BRL': 5.8, 'MXN': 17.5, 'CLP': 960.0}

HUNTER_NAMES = [
    'Ana González', 'Carlos Mendez', 'Valentina Torres',
    'Bruno Alves',  'Sofía Ramírez',
]
_ht       = np.array([0.70, 0.85, 1.00, 1.25, 1.40])
HUNTER_W  = _ht / _ht.sum()
HUNTER_CR = [0.14, 0.17, 0.20, 0.23, 0.26]

JIRA_FUNNEL = {
    'pool':        0.60,
    'asignado':    0.10,
    'contactado':  0.10,
    'rechazado':   0.16,
    'afiliado':    0.04,
}

PRODUCT_TAXONOMY = {
    'Electrónica': {
        'Celulares y Teléfonos': ['Smartphones', 'Accesorios', 'Repuestos'],
        'Computación':           ['Laptops', 'Tablets', 'Periféricos', 'Almacenamiento'],
        'TV y Audio':            ['Televisores', 'Auriculares', 'Parlantes', 'Equipos de sonido'],
        'Cámaras y Accesorios':  ['Cámaras digitales', 'Cámaras de acción', 'Lentes', 'Trípodes'],
    },
    'Ropa y Moda': {
        'Ropa Mujer':         ['Vestidos', 'Blusas', 'Pantalones', 'Ropa deportiva'],
        'Ropa Hombre':        ['Camisas', 'Pantalones', 'Ropa deportiva', 'Trajes'],
        'Calzado':            ['Zapatillas', 'Sandalias', 'Botas', 'Zapatos de vestir'],
        'Accesorios de Moda': ['Bolsos', 'Carteras', 'Cinturones', 'Joyería'],
    },
    'Hogar y Deco': {
        'Muebles':      ['Sillas', 'Mesas', 'Estanterías', 'Sofás'],
        'Cocina':       ['Electrodomésticos', 'Utensilios', 'Vajilla', 'Almacenamiento'],
        'Decoración':   ['Cuadros', 'Plantas artificiales', 'Iluminación', 'Textiles'],
        'Herramientas': ['Manuales', 'Eléctricas', 'Medición', 'Organización'],
    },
    'Deportes': {
        'Fitness':                ['Pesas y Mancuernas', 'Cardio', 'Yoga y Pilates', 'Suplementos'],
        'Deportes de equipo':     ['Fútbol', 'Básquet', 'Vóley', 'Rugby'],
        'Deportes al aire libre': ['Ciclismo', 'Running', 'Natación', 'Camping'],
        'Raquetas':               ['Tenis', 'Pádel', 'Tenis de mesa', 'Squash'],
    },
    'Belleza y Salud': {
        'Cuidado Personal': ['Skincare', 'Cabello', 'Higiene', 'Perfumes'],
        'Maquillaje':       ['Rostro', 'Ojos', 'Labios', 'Uñas'],
        'Salud':            ['Vitaminas', 'Equipos médicos', 'Ortopedia', 'Óptica'],
    },
    'Alimentos': {
        'Bebidas':   ['Jugos', 'Bebidas energéticas', 'Café y Té', 'Agua'],
        'Snacks':    ['Barras de cereal', 'Frutos secos', 'Chips', 'Chocolates'],
        'Orgánicos': ['Aceites', 'Harinas', 'Legumbres', 'Condimentos'],
    },
    'Juguetes y Bebés': {
        'Juguetes': ['Educativos', 'Acción y aventura', 'Muñecas', 'Juegos de mesa'],
        'Bebés':    ['Pañales', 'Ropa de bebé', 'Lactancia', 'Sillas y carriolas'],
    },
}

print('Configuración cargada.')
print('  Afiliados objetivo :', N_AFFILIATES)
print('  Leads Jira total   :', N_JIRA_TOTAL)
print('  Pool de productos  :', N_PRODUCT_POOL)
print('  Jira operativo     :', JIRA_START.date(), '->', TODAY.date())


# ================================================================
# SECCIÓN 2 — Funciones auxiliares
# ================================================================

FIRST_NAMES = {
    'ARG': ['Valentina','Sofía','Martina','Agustina','Lucía',
            'Santiago','Mateo','Nicolás','Facundo','Tomás','Emma','Julián','Lautaro'],
    'CHI': ['Camila','Javiera','Constanza','Valentina','Isidora',
            'Diego','Sebastián','Matías','Ignacio','Felipe','Catalina','Bastián'],
    'BRA': ['Ana','Julia','Larissa','Fernanda','Beatriz',
            'Lucas','Gabriel','Matheus','Guilherme','Rafael','Isabela','João','Pedro'],
    'MEX': ['Fernanda','Valentina','Mariana','Daniela','Karla',
            'Diego','Miguel','Jorge','Andrés','Javier','Paola','Rodrigo'],
}
LAST_NAMES = {
    'ARG': ['García','Rodríguez','González','Fernández','López',
            'Martínez','Pérez','Sánchez','Romero','Torres','Díaz'],
    'CHI': ['González','Muñoz','Rojas','Díaz','Pérez',
            'Soto','Contreras','Silva','Martínez','Flores','Álvarez'],
    'BRA': ['Silva','Santos','Oliveira','Souza','Rodrigues',
            'Ferreira','Alves','Pereira','Lima','Gomes','Ribeiro'],
    'MEX': ['García','Martínez','Hernández','López','González',
            'Pérez','Sánchez','Ramírez','Torres','Flores','Morales'],
}

_ACCENT = str.maketrans({
    'á':'a','é':'e','í':'i','ó':'o','ú':'u',
    'à':'a','è':'e','ì':'i','ò':'o','ù':'u',
    'ä':'a','ë':'e','ï':'i','ö':'o','ü':'u',
    'ñ':'n','ç':'c',
    'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U',
    'Ä':'A','Ë':'E','Ï':'I','Ö':'O','Ü':'U','Ñ':'N',
})

def clean(s):
    return s.translate(_ACCENT).lower().replace(' ', '').replace('.', '')

def random_name(country):
    first = random.choice(FIRST_NAMES[country])
    last  = random.choice(LAST_NAMES[country])
    return first, last, first + ' ' + last

def make_username(first, last, salt):
    suffix = int(rng.integers(10, 9_999))
    return clean(first) + clean(last) + str(suffix)

def make_handle(first, last):
    r = int(rng.integers(0, 4))
    if r == 0: return clean(first) + '.' + clean(last)
    if r == 1: return clean(first) + '_' + clean(last)
    if r == 2: return clean(first) + str(int(rng.integers(10, 999)))
    return 'the.' + clean(first)

def follower_count(n=1):
    """Lognormal: mediana ≈ 36K, 95pct ≈ 260K. Rango [8K, 2M]."""
    raw = rng.lognormal(mean=10.5, sigma=1.2, size=n)
    return np.clip(raw, 8_000, 2_000_000).astype(int)

def rand_date(start, end):
    d = max(int((end - start).days), 1)
    return start + timedelta(days=int(rng.integers(0, d)))

def make_product_id(country):
    return MELI_CODE[country] + str(int(rng.integers(10_000_000, 99_999_999)))

def make_product_title(cat2, cat3):
    adj = random.choice(['Premium','Original','Profesional','Ultra','Smart','Classic','Eco'])
    return f"{adj} {cat3} – {cat2}"

def make_seller_id():
    return int(rng.integers(10_000_000, 99_999_999))

print('Helpers listos.')


# ================================================================
# SECCIÓN 3 — Leads Jira (todos los influencers identificados)
# ================================================================

n = N_JIRA_TOTAL
shuf = np.arange(n)
rng.shuffle(shuf)

n_pool = int(n * JIRA_FUNNEL['pool'])
n_asig = int(n * JIRA_FUNNEL['asignado'])
n_cont = int(n * JIRA_FUNNEL['contactado'])
n_rech = int(n * JIRA_FUNNEL['rechazado'])
n_afil = n - n_pool - n_asig - n_cont - n_rech

states = np.empty(n, dtype=object)
c0 = n_pool
c1 = c0 + n_asig
c2 = c1 + n_cont
c3 = c2 + n_rech
states[shuf[:c0]]  = 'pool'
states[shuf[c0:c1]] = 'asignado'
states[shuf[c1:c2]] = 'contactado'
states[shuf[c2:c3]] = 'rechazado'
states[shuf[c3:]]   = 'afiliado'

jira_rows = []
for i in range(n):
    country             = str(rng.choice(COUNTRIES, p=COUNTRY_W))
    first, last, nombre = random_name(country)
    state               = str(states[i])
    category            = random.choice(CATEGORIES)

    has_ig = random.random() < 0.85
    has_tt = random.random() < 0.72
    if not has_ig and not has_tt:
        has_ig = True
    ig_handle = make_handle(first, last) if has_ig else None
    tt_handle = make_handle(first, last) if has_tt else None

    hunter_idx      = None
    ultimo_contacto = None

    if state in ('asignado', 'contactado', 'afiliado', 'rechazado'):
        hunter_idx = int(rng.choice(len(HUNTER_NAMES), p=HUNTER_W))
        if state == 'asignado':
            ultimo_contacto = rand_date(JIRA_START, TODAY - timedelta(days=5))
        elif state == 'contactado':
            ultimo_contacto = rand_date(JIRA_START + timedelta(days=7), TODAY - timedelta(days=2))
        else:
            ultimo_contacto = rand_date(JIRA_START + timedelta(days=14), TODAY - timedelta(days=1))

    jira_rows.append({
        '_i':              i,
        '_state':          state,
        '_country':        country,
        '_first':          first,
        '_last':           last,
        '_category':       category,
        '_hunter_idx':     hunter_idx,
        'NOMBRE':          nombre,
        'INSTAGRAM':       ig_handle,
        'TIKTOK':          tt_handle,
        'ULTIMO_CONTACTO': ultimo_contacto.strftime('%Y-%m-%d') if ultimo_contacto else None,
    })

df_jira_raw = pd.DataFrame(jira_rows)

print('Leads Jira generados:', len(df_jira_raw))
print(df_jira_raw['_state'].value_counts().to_string())


# ================================================================
# SECCIÓN 4 — DIM_AFFILIATES (base, sin handles de RRSS aún)
# ================================================================

aff_records  = []
aff_id_seq   = [1]
jira_aff_map = {}

jira_aff_df = df_jira_raw[df_jira_raw['_state'] == 'afiliado'].reset_index(drop=True)

for _, row in jira_aff_df.iterrows():
    country  = row['_country']
    first    = row['_first']
    last     = row['_last']
    raw_i    = int(row['_i'])
    username = make_username(first, last, raw_i)
    uid      = int(rng.integers(10_000_000, 99_999_999))
    joined   = rand_date(JIRA_START, TODAY - timedelta(days=3))
    aid      = aff_id_seq[0]
    aff_id_seq[0] += 1

    jira_aff_map[raw_i] = {'AFFILIATE_ID': aid, 'MELI_USERNAME': username}

    aff_records.append({
        'AFFILIATE_ID':  aid,
        'MELI_USERNAME': username,
        'MELI_USER_ID':  uid,
        'COUNTRY':       country,
        'CATEGORY':      row['_category'],
        '_joined':       joined,
        '_first':        first,
        '_last':         last,
        '_source':       'jira',
    })

print('Afiliados Jira-sourced :', len(aff_records))

n_organic = N_AFFILIATES - len(aff_records)
for i in range(n_organic):
    country        = str(rng.choice(COUNTRIES, p=COUNTRY_W))
    first, last, _ = random_name(country)
    username       = make_username(first, last, 100_000 + i)
    uid            = int(rng.integers(10_000_000, 99_999_999))
    joined         = rand_date(PROGRAM_LAUNCH[country], TODAY - timedelta(days=30))
    aid            = aff_id_seq[0]
    aff_id_seq[0] += 1

    aff_records.append({
        'AFFILIATE_ID':  aid,
        'MELI_USERNAME': username,
        'MELI_USER_ID':  uid,
        'COUNTRY':       country,
        'CATEGORY':      random.choice(CATEGORIES),
        '_joined':       joined,
        '_first':        first,
        '_last':         last,
        '_source':       'organic',
    })

df_affiliates = pd.DataFrame(aff_records)
df_affiliates = df_affiliates.drop_duplicates('MELI_USERNAME').reset_index(drop=True)
df_affiliates['AFFILIATE_ID'] = range(1, len(df_affiliates) + 1)

print('Total afiliados base   :', len(df_affiliates))


# ================================================================
# SECCIÓN 5 — FACTS_REGISTERED_SOCIAL_MEDIA
#             + backfill IG/TikTok en df_affiliates → DIM_AFFILIATES
# ================================================================

PLAT_PROB = {
    'instagram': 0.85,
    'tiktok':    0.72,
    'youtube':   0.32,
    'facebook':  0.28,
    'x':         0.22,
    'other':     0.08,
}
PLAT_URL_TPL = {
    'instagram': 'https://instagram.com/',
    'tiktok':    'https://tiktok.com/@',
    'youtube':   'https://youtube.com/@',
    'facebook':  'https://facebook.com/',
    'x':         'https://x.com/',
    'other':     'https://linktr.ee/',
}

sm_records = []
sm_id_seq  = [1]

for _, aff in df_affiliates.iterrows():
    first = aff['_first']
    last  = aff['_last']
    aid   = aff['AFFILIATE_ID']

    chosen = [p for p, prob in PLAT_PROB.items() if random.random() < prob]
    if not chosen:
        chosen = ['instagram']

    main_followers = int(follower_count(1)[0])

    for j, plat in enumerate(chosen):
        if j == 0:
            followers = main_followers
        else:
            ratio     = float(rng.uniform(0.08, 0.75))
            followers = max(1_000, int(main_followers * ratio))

        handle = make_handle(first, last)
        url    = PLAT_URL_TPL[plat] + handle

        sm_records.append({
            'SM_ID':        sm_id_seq[0],
            'AFFILIATE_ID': aid,
            'SOCIAL_MEDIA': plat,
            'URL':          url,
            'FOLLOWERS':    followers,
        })
        sm_id_seq[0] += 1

df_sm = pd.DataFrame(sm_records)

print('Registros social media :', len(df_sm))
print('Plataformas:')
print(df_sm['SOCIAL_MEDIA'].value_counts().to_string())
print('\nPromedio plataformas/afiliado :', round(len(df_sm) / len(df_affiliates), 1))

# ── Backfill IG / TikTok handles & follower counts → df_affiliates ────────────
ig_lookup = (
    df_sm[df_sm['SOCIAL_MEDIA'] == 'instagram']
    .drop_duplicates('AFFILIATE_ID')
    .set_index('AFFILIATE_ID')[['URL', 'FOLLOWERS']]
    .rename(columns={'URL': '_ig_url', 'FOLLOWERS': '_ig_followers'})
)
tt_lookup = (
    df_sm[df_sm['SOCIAL_MEDIA'] == 'tiktok']
    .drop_duplicates('AFFILIATE_ID')
    .set_index('AFFILIATE_ID')[['URL', 'FOLLOWERS']]
    .rename(columns={'URL': '_tt_url', 'FOLLOWERS': '_tt_followers'})
)

def _handle_from_url(url, prefix):
    return url.replace(prefix, '').split('?')[0] if isinstance(url, str) else None

df_affiliates = df_affiliates.join(ig_lookup, on='AFFILIATE_ID')
df_affiliates = df_affiliates.join(tt_lookup, on='AFFILIATE_ID')
df_affiliates['INSTAGRAM_HANDLE']         = df_affiliates['_ig_url'].apply(lambda u: _handle_from_url(u, 'https://instagram.com/'))
df_affiliates['INSTAGRAM_FOLLOWER_COUNT'] = df_affiliates['_ig_followers']
df_affiliates['TIKTOK_HANDLE']            = df_affiliates['_tt_url'].apply(lambda u: _handle_from_url(u, 'https://tiktok.com/@'))
df_affiliates['TIKTOK_FOLLOWER_COUNT']    = df_affiliates['_tt_followers']
df_affiliates.drop(columns=['_ig_url', '_ig_followers', '_tt_url', '_tt_followers'], inplace=True, errors='ignore')

df_dim_affiliates = df_affiliates[[
    'AFFILIATE_ID', 'MELI_USERNAME', 'MELI_USER_ID', 'COUNTRY', 'CATEGORY',
    'INSTAGRAM_HANDLE', 'INSTAGRAM_FOLLOWER_COUNT',
    'TIKTOK_HANDLE',    'TIKTOK_FOLLOWER_COUNT',
]].copy()

print('\nDIM_AFFILIATES — handles backfilled:')
print('  Con Instagram :', df_dim_affiliates['INSTAGRAM_HANDLE'].notna().sum())
print('  Con TikTok    :', df_dim_affiliates['TIKTOK_HANDLE'].notna().sum())


# ================================================================
# SECCIÓN 6 — FACTS_JIRA_HUNTING_AFILIADOS
# ================================================================

uname_to_aid = df_affiliates.set_index('MELI_USERNAME')['AFFILIATE_ID'].to_dict()
for raw_i, info in jira_aff_map.items():
    uname = info['MELI_USERNAME']
    if uname in uname_to_aid:
        jira_aff_map[raw_i]['AFFILIATE_ID'] = uname_to_aid[uname]

jira_out = []
for _, row in df_jira_raw.iterrows():
    state  = str(row['_state'])
    raw_i  = int(row['_i'])

    h_idx  = row['_hunter_idx']
    hunter = HUNTER_NAMES[int(h_idx)] if pd.notna(h_idx) else None

    meli_username = None
    if state == 'afiliado' and raw_i in jira_aff_map:
        meli_username = jira_aff_map[raw_i]['MELI_USERNAME']

    jira_key = 'HUNT-' + str(raw_i + 1).zfill(4)

    jira_out.append({
        'JIRA_KEY':        jira_key,
        'MELI_USERNAME':   meli_username,
        'HUNTER':          hunter,
        'NOMBRE':          row['NOMBRE'],
        'ULTIMO_CONTACTO': row['ULTIMO_CONTACTO'],
        'INSTAGRAM':       row['INSTAGRAM'],
        'TIKTOK':          row['TIKTOK'],
        'asignado':   state in ('asignado', 'contactado', 'afiliado', 'rechazado'),
        'contactado': state in ('contactado', 'afiliado', 'rechazado'),
        'afiliado':   state == 'afiliado',
        'rechazado':  state == 'rechazado',
    })

df_facts_jira = pd.DataFrame(jira_out)

print('Registros Jira :', len(df_facts_jira))
print('\nDistribución por estado:')
print('  asignado  :', df_facts_jira['asignado'].sum())
print('  contactado:', df_facts_jira['contactado'].sum())
print('  afiliado  :', df_facts_jira['afiliado'].sum())
print('  rechazado :', df_facts_jira['rechazado'].sum())
print('  pool      :', (~df_facts_jira['asignado']).sum())
print('\nDistribución por hunter (leads asignados):')
print(df_facts_jira[df_facts_jira['HUNTER'].notna()]['HUNTER'].value_counts().to_string())


# ================================================================
# SECCIÓN 7 — DIM_AFFILIATES_MARKETPLACE_PRODUCTS
#             + FACTS_MARKETPLACE_AFFILIATE_URLS
# ================================================================

# ── Fase 1: Pool de productos ──────────────────────────────────────────────────
cat1_list    = list(PRODUCT_TAXONOMY.keys())
cat1_weights = np.array([len(v) for v in PRODUCT_TAXONOMY.values()], dtype=float)
cat1_weights /= cat1_weights.sum()

product_records = []
used_pids       = set()

for _ in range(N_PRODUCT_POOL):
    p_country = str(rng.choice(COUNTRIES, p=COUNTRY_W))
    cat1      = random.choices(cat1_list, weights=cat1_weights)[0]
    cat2      = random.choice(list(PRODUCT_TAXONOMY[cat1].keys()))
    cat3      = random.choice(PRODUCT_TAXONOMY[cat1][cat2])

    pid = None
    for _attempt in range(10):
        candidate = make_product_id(p_country)
        if candidate not in used_pids:
            pid = candidate
            used_pids.add(pid)
            break
    if pid is None:
        pid = make_product_id(p_country)

    pub_date = rand_date(min(PROGRAM_LAUNCH.values()), TODAY - timedelta(days=1))

    product_records.append({
        'MARKETPLACE_PRODUCT_ID': pid,
        'SELLER_MELI_USER_ID':    make_seller_id(),
        'TITLE':                  make_product_title(cat2, cat3),
        'CATEGORY_AGG_1':         cat1,
        'CATEGORY_AGG_2':         cat2,
        'CATEGORY_AGG_3':         cat3,
        'CONDITION':       random.choices(['new', 'used', 'refurbished'], weights=[0.70, 0.22, 0.08])[0],
        'VISIBLE':         random.random() > 0.05,
        'AVAILABLE_UNITS': int(rng.integers(1, 500)),
        'PUBLICATION_DATETIME': pub_date.strftime('%Y-%m-%d'),
        'CALIFICATION':    round(float(rng.uniform(3.0, 5.0)), 1),
        'OPINIONS':        int(rng.lognormal(mean=3.0, sigma=1.2)),
    })

df_products      = pd.DataFrame(product_records)
product_pid_pool = df_products['MARKETPLACE_PRODUCT_ID'].tolist()

print(f'Pool de productos generado : {len(df_products):,} productos únicos')

# ── Fase 2: URLs de afiliado muestreando del pool ──────────────────────────────
url_records = []

for _, aff in df_affiliates.iterrows():
    aid      = aff['AFFILIATE_ID']
    username = aff['MELI_USERNAME']
    joined   = aff['_joined']
    days_aff = max((TODAY - joined).days, 1)

    mu_urls = np.log(max(days_aff / 25.0, 2.0))
    n_urls  = int(np.clip(rng.lognormal(mean=mu_urls, sigma=0.55), 2, 30))

    sampled_pids = random.choices(product_pid_pool, k=n_urls)

    for pid in sampled_pids:
        url = 'https://meli.me/' + pid[:3].lower() + '/' + pid.lower() + '?aff=' + username
        created_at = rand_date(joined, TODAY - timedelta(days=1))
        is_closed  = random.random() < 0.28
        closed_at  = rand_date(created_at + timedelta(days=1), TODAY) if is_closed else None
        end_dt     = closed_at if closed_at else TODAY

        url_records.append({
            'URL':                    url,
            'AFFILIATE_ID':           aid,
            'MARKETPLACE_PRODUCT_ID': pid,
            'CREATED_AT':             created_at.strftime('%Y-%m-%d'),
            'CLOSED_AT':              closed_at.strftime('%Y-%m-%d') if closed_at else None,
            '_created_dt':            created_at,
            '_end_dt':                end_dt,
        })

df_urls = pd.DataFrame(url_records).drop_duplicates('URL').reset_index(drop=True)

referenced_pids = set(df_urls['MARKETPLACE_PRODUCT_ID'].unique())
df_dim_products = df_products[
    df_products['MARKETPLACE_PRODUCT_ID'].isin(referenced_pids)
].reset_index(drop=True)

print(f'URLs de afiliado           : {len(df_urls):,}')
print(f'  Prom. por afiliado       : {round(len(df_urls) / len(df_affiliates), 1)}')
closed_n = df_urls['CLOSED_AT'].notna().sum()
print(f'  Cerradas                 : {closed_n} ({round(100*closed_n/len(df_urls))}%)')
print(f'  Productos únicos ref.    : {len(df_dim_products):,}  (de pool de {len(df_products):,})')


# ================================================================
# SECCIÓN 8 — FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS (vectorizado)
# ================================================================

aff_max_followers = df_sm.groupby('AFFILIATE_ID')['FOLLOWERS'].max().to_dict()

df_urls['_created_dt'] = pd.to_datetime(df_urls['_created_dt'])
df_urls['_end_dt']     = pd.to_datetime(df_urls['_end_dt'])
df_urls['_active_days'] = (
    (df_urls['_end_dt'] - df_urls['_created_dt']).dt.days.clip(lower=1)
)

df_urls['_max_followers'] = df_urls['AFFILIATE_ID'].map(aff_max_followers).fillna(20_000)

active_months = df_urls['_active_days'] / 30.0
mean_clicks   = (df_urls['_max_followers'] * 0.001 / 8.0) * active_months
log_mean      = np.log(np.maximum(mean_clicks.values, 1.5))
n_clicks_raw = rng.lognormal(mean=log_mean, sigma=0.9)
# Escalar proporcionalmente al target: preserva la distribución relativa
# (afiliados con más seguidores siguen teniendo más clicks) pero controla el volumen total
total_raw = n_clicks_raw.sum()
n_clicks_scaled = n_clicks_raw * (N_TARGET_ACCESS_LOGS / total_raw)
df_urls['_n_clicks'] = np.maximum(np.floor(n_clicks_scaled).astype(int), 0)

total_clicks = int(df_urls['_n_clicks'].sum())
print('Total clicks a generar :', f'{total_clicks:,}', f'(target: {N_TARGET_ACCESS_LOGS:,})')

active_mask = df_urls['_n_clicks'] > 0
df_u_active = df_urls[active_mask].copy()
rep_idx     = np.repeat(df_u_active.index.values, df_u_active['_n_clicks'].values)
df_acc_base = df_u_active.loc[rep_idx, ['URL', '_created_dt', '_end_dt']].reset_index(drop=True)

active_secs    = (
    (df_acc_base['_end_dt'] - df_acc_base['_created_dt']).dt.total_seconds().values
)
random_offsets = (rng.random(len(df_acc_base)) * active_secs).astype('int64')
df_acc_base['ACCESS_DATETIME'] = (
    df_acc_base['_created_dt'] + pd.to_timedelta(random_offsets, unit='s')
)

n_buyers   = max(total_clicks // 5, 10_000)
buyer_ids  = rng.integers(1_000_000, 9_999_999, size=n_buyers)
buyer_pool = np.array(['buyer_' + str(x) for x in buyer_ids])
b_idx      = rng.integers(0, n_buyers, size=len(df_acc_base))
df_acc_base['MELI_USERNAME'] = buyer_pool[b_idx]

df_access_logs = df_acc_base[['URL', 'MELI_USERNAME', 'ACCESS_DATETIME']].copy()
df_access_logs['ACCESS_DATETIME'] = (
    df_access_logs['ACCESS_DATETIME'].dt.strftime('%Y-%m-%d %H:%M:%S')
)

print('Registros access_logs  :', f'{len(df_access_logs):,}')


# ================================================================
# SECCIÓN 9 — FACTS_AFFILIATES_MARKETPLACE_SALES (vectorizado)
# ================================================================

CONVERSION_RATE = 0.030

PRICE_RANGES = {
    'ARG': (3_000,   300_000),
    'BRA': (   30,     3_000),
    'MEX': (  150,    15_000),
    'CHI': (2_000,   200_000),
}

url_to_country = (
    df_urls[['URL', 'AFFILIATE_ID']]
    .merge(df_affiliates[['AFFILIATE_ID', 'COUNTRY']], on='AFFILIATE_ID')
    .set_index('URL')['COUNTRY']
    .to_dict()
)

url_to_pid = df_urls.set_index('URL')['MARKETPLACE_PRODUCT_ID'].to_dict()
url_to_aid = df_urls.set_index('URL')['AFFILIATE_ID'].to_dict()

sale_mask     = rng.random(len(df_access_logs)) < CONVERSION_RATE
df_sales_base = df_access_logs[sale_mask].copy().reset_index(drop=True)

df_sales_base['ACCESS_DATETIME']  = pd.to_datetime(df_sales_base['ACCESS_DATETIME'])
min_offset = rng.integers(1, 45, size=len(df_sales_base))
df_sales_base['PURCHASE_DATETIME'] = (
    df_sales_base['ACCESS_DATETIME'] + pd.to_timedelta(min_offset, unit='m')
).clip(upper=pd.Timestamp(TODAY))

df_sales_base['COUNTRY'] = df_sales_base['URL'].map(url_to_country).fillna('BRA')
prices = np.zeros(len(df_sales_base))
for country, (lo, hi) in PRICE_RANGES.items():
    mask = (df_sales_base['COUNTRY'] == country).values
    if mask.sum() > 0:
        prices[mask] = np.round(rng.uniform(lo, hi, size=int(mask.sum())), 2)
df_sales_base['PRICE'] = prices

df_sales_base['AFFILIATE_ID']           = df_sales_base['URL'].map(url_to_aid)
df_sales_base['MARKETPLACE_PRODUCT_ID'] = df_sales_base['URL'].map(url_to_pid)
df_sales_base['CURRENCY']               = df_sales_base['COUNTRY'].map(CURRENCY_MAP)

n_buyers_pool  = max(len(df_sales_base) // 4, 5_000)
buyer_uid_pool = rng.integers(10_000_000, 99_999_999, size=n_buyers_pool)
b_idx          = rng.integers(0, n_buyers_pool, size=len(df_sales_base))
df_sales_base['BUYER_MELI_USER_ID'] = buyer_uid_pool[b_idx]

df_facts_sales = df_sales_base[[
    'URL', 'AFFILIATE_ID', 'BUYER_MELI_USER_ID', 'MARKETPLACE_PRODUCT_ID',
    'PURCHASE_DATETIME', 'COUNTRY', 'CURRENCY', 'PRICE'
]].copy()
df_facts_sales['PURCHASE_DATETIME'] = df_facts_sales['PURCHASE_DATETIME'].dt.strftime('%Y-%m-%d %H:%M:%S')

real_cr = round(100 * len(df_facts_sales) / len(df_access_logs), 1)
print('Registros ventas       :', f'{len(df_facts_sales):,}')
print('Conv. rate efectivo    :', str(real_cr) + '%')
print('\nPrecio promedio por país:')
print(df_sales_base.groupby('COUNTRY')['PRICE'].agg(['mean','min','max']).round(0).to_string())


# ================================================================
# SECCIÓN 10 — FACTS_USD_EXCHANGE_RATES
# ================================================================

FX_START = min(PROGRAM_LAUNCH.values())
FX_END   = TODAY

fx_dates = []
d = FX_START
while d <= FX_END:
    fx_dates.append(d)
    d += timedelta(days=7)
n_weeks = len(fx_dates)

print(f'Generando {n_weeks} semanas de tasas ({FX_START.date()} -> {FX_END.date()})')

FX_PARAMS = {
    'ARS': {'drift': +0.012,  'vol': 0.035},
    'BRL': {'drift': +0.0015, 'vol': 0.012},
    'MXN': {'drift': +0.0010, 'vol': 0.010},
    'CLP': {'drift': +0.0008, 'vol': 0.009},
}

fx_records = []
for currency, params in FX_PARAMS.items():
    shocks      = rng.normal(loc=params['drift'], scale=params['vol'], size=n_weeks)
    log_returns = np.cumsum(shocks)
    log_series  = np.log(FX_ANCHOR[currency]) + log_returns - log_returns[-1]
    rate_series = np.exp(log_series)
    for i, dt in enumerate(fx_dates):
        fx_records.append({
            'CURRENCY':      currency,
            'RATE_DATETIME': dt.strftime('%Y-%m-%d'),
            'VALUE':         round(float(rate_series[i]), 4),
        })

df_exchange_rates = pd.DataFrame(fx_records)

print('Registros tipo de cambio :', len(df_exchange_rates))
print('\nÚltimo valor por moneda:')
print(df_exchange_rates.groupby('CURRENCY').last()[['RATE_DATETIME', 'VALUE']].to_string())
print('\nRango histórico:')
print(df_exchange_rates.groupby('CURRENCY')['VALUE'].agg(['min', 'max']).round(2).to_string())


# ================================================================
# SECCIÓN 11 — Exportar CSVs
# ================================================================

EXPORT_COLS = {
    'DIM_AFFILIATES': [
        'AFFILIATE_ID', 'MELI_USERNAME', 'MELI_USER_ID', 'COUNTRY', 'CATEGORY',
        'INSTAGRAM_HANDLE', 'INSTAGRAM_FOLLOWER_COUNT',
        'TIKTOK_HANDLE', 'TIKTOK_FOLLOWER_COUNT',
    ],
    'FACTS_REGISTERED_SOCIAL_MEDIA': [
        'SM_ID', 'AFFILIATE_ID', 'SOCIAL_MEDIA', 'URL', 'FOLLOWERS',
    ],
    'FACTS_JIRA_HUNTING_AFILIADOS': [
        'JIRA_KEY', 'MELI_USERNAME', 'HUNTER', 'NOMBRE',
        'ULTIMO_CONTACTO', 'INSTAGRAM', 'TIKTOK',
        'asignado', 'contactado', 'afiliado', 'rechazado',
    ],
    'FACTS_MARKETPLACE_AFFILIATE_URLS': [
        'URL', 'AFFILIATE_ID', 'MARKETPLACE_PRODUCT_ID', 'CREATED_AT', 'CLOSED_AT',
    ],
    'FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS': [
        'URL', 'MELI_USERNAME', 'ACCESS_DATETIME',
    ],
    'FACTS_AFFILIATES_MARKETPLACE_SALES': [
        'URL', 'AFFILIATE_ID', 'BUYER_MELI_USER_ID', 'MARKETPLACE_PRODUCT_ID',
        'PURCHASE_DATETIME', 'COUNTRY', 'CURRENCY', 'PRICE',
    ],
    'DIM_AFFILIATES_MARKETPLACE_PRODUCTS': [
        'MARKETPLACE_PRODUCT_ID', 'SELLER_MELI_USER_ID',
        'TITLE', 'CATEGORY_AGG_1', 'CATEGORY_AGG_2', 'CATEGORY_AGG_3',
        'CONDITION', 'VISIBLE', 'AVAILABLE_UNITS',
        'PUBLICATION_DATETIME', 'CALIFICATION', 'OPINIONS',
    ],
    'FACTS_USD_EXCHANGE_RATES': [
        'CURRENCY', 'RATE_DATETIME', 'VALUE',
    ],
}

DATAFRAMES = {
    'DIM_AFFILIATES':                            df_dim_affiliates,
    'FACTS_REGISTERED_SOCIAL_MEDIA':             df_sm,
    'FACTS_JIRA_HUNTING_AFILIADOS':              df_facts_jira,
    'FACTS_MARKETPLACE_AFFILIATE_URLS':          df_urls,
    'FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS':  df_access_logs,
    'FACTS_AFFILIATES_MARKETPLACE_SALES':        df_facts_sales,
    'DIM_AFFILIATES_MARKETPLACE_PRODUCTS':       df_dim_products,
    'FACTS_USD_EXCHANGE_RATES':                  df_exchange_rates,
}

print('Exportando CSVs a:', OUTPUT_DIR)
print('-' * 72)
total_rows = 0
for name, df in DATAFRAMES.items():
    cols = EXPORT_COLS[name]
    out  = df[cols].copy()
    path = OUTPUT_DIR + '/' + name + '.csv'
    out.to_csv(path, index=False)
    rows = len(out)
    total_rows += rows
    print(f'  {name:<50} {rows:>9,} filas  ->  {path}')

print('-' * 72)
print('Total filas generadas  :', f'{total_rows:,}')
print('\nTodo listo.')
