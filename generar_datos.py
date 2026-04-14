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

from config import *   # todos los parámetros viven en config.py

# ================================================================
# SECCIÓN 1 — Inicialización
# ================================================================

rng = np.random.default_rng(SEED)
random.seed(SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Throughput relativo de hunters (vector numpy para np.choice)
_ht      = np.array([0.70, 0.85, 1.00, 1.25, 1.40, 0.90, 0.75, 0.80])
_hunter_w = _ht / _ht.sum()   # pesos normalizados (local, no sobreescribe config)

print('Configuración cargada.')
print('  Afiliados objetivo :', N_AFFILIATES)
print('  Leads Jira total   :', N_JIRA_TOTAL)
print('  Pool de productos  :', N_PRODUCT_POOL)
print('  SALES_MULTIPLIER   :', SALES_MULTIPLIER)
print('  Jira operativo     :', JIRA_START.date(), '->', TODAY.date())


# ================================================================
# SECCIÓN 2 — Funciones auxiliares
# ================================================================

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
    floor = FOLLOWER_FLOOR_BASE * rng.uniform(FOLLOWER_FLOOR_JITTER_LO, FOLLOWER_FLOOR_JITTER_HI)
    raw   = rng.lognormal(mean=10.5, sigma=1.2, size=n)
    return np.clip(raw, floor, 2_000_000).astype(int)

def rand_date(start, end):
    d = max(int((end - start).days), 1)
    return start + timedelta(days=int(rng.integers(0, d)))

def next_business_day(d):
    """Avanza al lunes si d cae en sábado o domingo."""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d

def prev_business_day(d):
    """Retrocede al viernes si d cae en sábado o domingo."""
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d

def make_product_id(country):
    return MELI_CODE[country] + str(int(rng.integers(10_000_000, 99_999_999)))

def make_product_title(cat2, cat3):
    adj = random.choice(['Premium','Original','Profesional','Ultra','Smart','Classic','Eco'])
    return f"{adj} {cat3} – {cat2}"

def make_seller_id():
    return int(rng.integers(10_000_000, 99_999_999))

def rand_price(country):
    """Precio lognormal con clamp duro. Mayoría baratos, cola larga hacia caros."""
    mu, sigma = PRICE_LOGNORMAL[country]
    lo, hi    = PRICE_CLAMP[country]
    return float(np.clip(np.round(rng.lognormal(mean=mu, sigma=sigma), 2), lo, hi))

print('Helpers listos.')


# ================================================================
# SECCIÓN 3 — Leads Jira (todos los influencers identificados)
# ================================================================

JIRA_PERIOD_DAYS  = max((TODAY - JIRA_START).days, 1)
JIRA_PERIOD_WEEKS = JIRA_PERIOD_DAYS / 7.0

# ── Throughput de hunters: convergen de 50 → 100 contactos/semana ────────────
# Capacidad total = promedio 75/sem × semanas del período × factor de peso relativo
_mean_w = float(np.mean(_ht))
HUNTER_CAPACITY = {
    name: int(HUNTER_WEEKLY_RATE_AVG * JIRA_PERIOD_WEEKS * (_ht[i] / _mean_w))
    for i, name in enumerate(HUNTER_NAMES)
}

# ── Fase 1: Generar todos los leads básicos ───────────────────────────────────
raw_leads = []
for i in range(N_JIRA_TOTAL):
    country             = str(rng.choice(COUNTRIES, p=COUNTRY_W))
    first, last, nombre = random_name(country)
    category            = random.choices(CATEGORIES, weights=CATEGORY_W)[0]

    has_ig = random.random() < 0.85
    has_tt = random.random() < 0.72
    if not has_ig and not has_tt:
        has_ig = True
    ig_handle = make_handle(first, last) if has_ig else None
    tt_handle = make_handle(first, last) if has_tt else None

    if float(rng.random()) < JIRA_FUNNEL['pool']:
        hunter_idx       = None
        fecha_asignacion = None
    else:
        hunter_idx       = int(rng.choice(len(HUNTER_NAMES), p=_hunter_w))
        # Distribución sesgada hacia fechas recientes para reflejar ramp-up del equipo
        u1, u2           = float(rng.random()), float(rng.random())
        t_frac           = max(u1, u2)   # densidad 2t: más leads en los últimos meses
        fecha_asignacion = JIRA_START + timedelta(days=int(t_frac * JIRA_PERIOD_DAYS))
        # Solo días hábiles: capear al último día hábil antes de TODAY, luego avanzar si weekend
        fecha_asignacion = min(fecha_asignacion, prev_business_day(TODAY - timedelta(days=1)))
        fecha_asignacion = next_business_day(fecha_asignacion)

    raw_leads.append({
        '_i':               i,
        '_country':         country,
        '_first':           first,
        '_last':            last,
        '_category':        category,
        '_hunter_idx':      hunter_idx,
        '_fecha_asig':      fecha_asignacion,
        '_state':           'pool' if hunter_idx is None else None,
        '_ultimo_contacto': None,
        'NOMBRE':           nombre,
        'INSTAGRAM':        ig_handle,
        'TIKTOK':           tt_handle,
    })

# ── Fase 2: Procesar leads por hunter en orden FIFO ──────────────────────────
for h_idx in range(len(HUNTER_NAMES)):
    hunter_name = HUNTER_NAMES[h_idx]
    capacity    = HUNTER_CAPACITY[hunter_name]

    # Solo los leads de este hunter
    h_leads = [l for l in raw_leads if l['_hunter_idx'] == h_idx]

    # FIFO: más antiguo primero
    h_leads.sort(key=lambda l: l['_fecha_asig'])

    for j, lead in enumerate(h_leads):
        fecha_asig = lead['_fecha_asig']
        t = min((fecha_asig - JIRA_START).days / JIRA_PERIOD_DAYS, 1.0)

        team_delay   = 3.0 - 2.0 * t
        team_cr      = 0.08 + 0.10 * t
        hunter_delay = max(team_delay + HUNTER_DELAY_DELTA[hunter_name], 0.3)
        hunter_cr    = float(np.clip(team_cr + HUNTER_CR_DELTA[hunter_name], 0.03, 0.40))

        if j < capacity:
            # Lead dentro de la capacidad del hunter: fue contactado
            delay_days      = int(np.clip(rng.normal(hunter_delay, 1.5), 0, 14))
            contact_date    = next_business_day(fecha_asig + timedelta(days=delay_days))
            ultimo_contacto = min(contact_date, prev_business_day(TODAY - timedelta(days=1)))
            lead['_ultimo_contacto'] = ultimo_contacto

            r = float(rng.random())
            if r < hunter_cr:
                lead['_state'] = 'afiliado'
            elif r < hunter_cr + 0.55:
                lead['_state'] = 'rechazado'
            else:
                lead['_state'] = 'contactado'
        else:
            # Lead en cola de espera (los más recientes, cap HUNTER_MAX_QUEUE)
            lead['_state'] = 'asignado'

# ── Fase 3: Construir df_jira_raw ─────────────────────────────────────────────
jira_rows = []
for lead in raw_leads:
    fec = lead['_fecha_asig']
    ult = lead['_ultimo_contacto']
    jira_rows.append({
        '_i':               lead['_i'],
        '_state':           lead['_state'],
        '_country':         lead['_country'],
        '_first':           lead['_first'],
        '_last':            lead['_last'],
        '_category':        lead['_category'],
        '_hunter_idx':      lead['_hunter_idx'],
        'NOMBRE':           lead['NOMBRE'],
        'INSTAGRAM':        lead['INSTAGRAM'],
        'TIKTOK':           lead['TIKTOK'],
        'FECHA_ASIGNACION': fec.strftime('%Y-%m-%d') if fec else None,
        'ULTIMO_CONTACTO':  ult.strftime('%Y-%m-%d') if ult else None,
    })

df_jira_raw = pd.DataFrame(jira_rows)

print('Leads Jira generados :', len(df_jira_raw))
print(df_jira_raw['_state'].value_counts().to_string())
print('\nCapacidad y cola por hunter:')
for h_idx in range(len(HUNTER_NAMES)):
    name     = HUNTER_NAMES[h_idx]
    cap      = HUNTER_CAPACITY[name]
    h_df     = df_jira_raw[df_jira_raw['_hunter_idx'] == h_idx]
    n_asig   = (h_df['_state'] == 'asignado').sum()
    n_proc   = len(h_df) - n_asig
    print(f'  {name:<22}  cap={cap:4d}  leads={len(h_df):5d}  proc={n_proc:5d}  asig={n_asig:3d}')


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
    _uc    = row['ULTIMO_CONTACTO']
    joined = datetime.strptime(_uc, '%Y-%m-%d') if _uc else rand_date(JIRA_START, TODAY - timedelta(days=3))
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
        'CATEGORY':      random.choices(CATEGORIES, weights=CATEGORY_W)[0],
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
df_affiliates['INSTAGRAM_FOLLOWER_COUNT'] = df_affiliates['_ig_followers'].astype('Int64')
df_affiliates['TIKTOK_HANDLE']            = df_affiliates['_tt_url'].apply(lambda u: _handle_from_url(u, 'https://tiktok.com/@'))
df_affiliates['TIKTOK_FOLLOWER_COUNT']    = df_affiliates['_tt_followers'].astype('Int64')
df_affiliates.drop(columns=['_ig_url', '_ig_followers', '_tt_url', '_tt_followers'], inplace=True, errors='ignore')

df_dim_affiliates = df_affiliates[[
    'AFFILIATE_ID', 'MELI_USERNAME', 'MELI_USER_ID', '_joined', 'COUNTRY', 'CATEGORY',
    'INSTAGRAM_HANDLE', 'INSTAGRAM_FOLLOWER_COUNT',
    'TIKTOK_HANDLE',    'TIKTOK_FOLLOWER_COUNT',
]].copy().rename(columns={'_joined': 'AFFILIATED_AT'})

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
        'JIRA_KEY':          jira_key,
        'MELI_USERNAME':     meli_username,
        'HUNTER':            hunter,
        'NOMBRE':            row['NOMBRE'],
        'FECHA_ASIGNACION':  row['FECHA_ASIGNACION'],
        'ULTIMO_CONTACTO':   row['ULTIMO_CONTACTO'],
        'INSTAGRAM':         row['INSTAGRAM'],
        'TIKTOK':            row['TIKTOK'],
        'ESTADO':     state,
        'ASIGNADO':   state in ('asignado', 'contactado', 'afiliado', 'rechazado'),
        'CONTACTADO': state in ('contactado', 'afiliado', 'rechazado'),
        'AFILIADO':   state == 'afiliado',
        'RECHAZADO':  state == 'rechazado',
    })

df_facts_jira = pd.DataFrame(jira_out)

# ── Leads de test — para ejercicio de filtrado SQL del bootcamp ──────────────
# Detección: LOWER(NOMBRE) LIKE '%test%'
_test_rows = [
    {'JIRA_KEY':'HUNT-99980','MELI_USERNAME':None,               'HUNTER':'Ana González',    'NOMBRE':'Test',        'FECHA_ASIGNACION':'2026-01-20','ULTIMO_CONTACTO':None,        'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'asignado',  'ASIGNADO':True, 'CONTACTADO':False,'AFILIADO':False,'RECHAZADO':False},
    {'JIRA_KEY':'HUNT-99981','MELI_USERNAME':None,               'HUNTER':'Carlos Mendez',   'NOMBRE':'Test Lead',   'FECHA_ASIGNACION':'2026-02-10','ULTIMO_CONTACTO':'2026-02-12','INSTAGRAM':None,'TIKTOK':None,'ESTADO':'contactado','ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':False,'RECHAZADO':False},
    {'JIRA_KEY':'HUNT-99982','MELI_USERNAME':'test_afiliado_001','HUNTER':'Sofía Ramírez',   'NOMBRE':'test_usuario','FECHA_ASIGNACION':'2026-01-15','ULTIMO_CONTACTO':'2026-01-17','INSTAGRAM':None,'TIKTOK':None,'ESTADO':'afiliado',  'ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':True, 'RECHAZADO':False},
    {'JIRA_KEY':'HUNT-99983','MELI_USERNAME':None,               'HUNTER':'Bruno Alves',     'NOMBRE':'TEST DUMMY',  'FECHA_ASIGNACION':'2026-03-05','ULTIMO_CONTACTO':'2026-03-07','INSTAGRAM':None,'TIKTOK':None,'ESTADO':'rechazado', 'ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':False,'RECHAZADO':True},
    {'JIRA_KEY':'HUNT-99984','MELI_USERNAME':None,               'HUNTER':None,              'NOMBRE':'Prueba Test', 'FECHA_ASIGNACION':None,       'ULTIMO_CONTACTO':None,        'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'pool',      'ASIGNADO':False,'CONTACTADO':False,'AFILIADO':False,'RECHAZADO':False},
    {'JIRA_KEY':'HUNT-99985','MELI_USERNAME':'test_afiliado_002','HUNTER':'Valentina Torres','NOMBRE':'Test Nico',   'FECHA_ASIGNACION':'2026-02-24','ULTIMO_CONTACTO':'2026-02-25','INSTAGRAM':None,'TIKTOK':None,'ESTADO':'afiliado',  'ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':True, 'RECHAZADO':False},
]
df_facts_jira = pd.concat([df_facts_jira, pd.DataFrame(_test_rows)], ignore_index=True)
print(f'  >> {len(_test_rows)} leads de test inyectados (HUNT-99980 a HUNT-99985)')

print('Registros Jira :', len(df_facts_jira))
print('\nDistribución por estado:')
print('  ASIGNADO  :', df_facts_jira['ASIGNADO'].sum())
print('  CONTACTADO:', df_facts_jira['CONTACTADO'].sum())
print('  AFILIADO  :', df_facts_jira['AFILIADO'].sum())
print('  RECHAZADO :', df_facts_jira['RECHAZADO'].sum())
print('  pool      :', (~df_facts_jira['ASIGNADO']).sum())
print('\nDistribución por hunter (leads asignados):')
print(df_facts_jira[df_facts_jira['HUNTER'].notna()]['HUNTER'].value_counts().to_string())


# ================================================================
# SECCIÓN 7 — DIM_AFFILIATES_MARKETPLACE_PRODUCTS
#             + FACTS_MARKETPLACE_AFFILIATE_URLS
# ================================================================

# ── Fase 1: Pool de productos ──────────────────────────────────────────────────
cat1_list    = list(PRODUCT_CAT1_W.keys())
cat1_weights = list(PRODUCT_CAT1_W.values())

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

# ── Garantizar URLs en primera semana para afiliados Jira ─────────────────────
N_JIRA_FIRST_WEEK_URLS = 5
for _, aff in df_affiliates[df_affiliates['_source'] == 'jira'].iterrows():
    aid            = aff['AFFILIATE_ID']
    username       = aff['MELI_USERNAME']
    joined         = aff['_joined']
    first_week_end = min(joined + timedelta(days=7), TODAY - timedelta(days=1))
    if first_week_end <= joined:
        continue
    for _ in range(N_JIRA_FIRST_WEEK_URLS):
        pid        = random.choice(product_pid_pool)
        url        = 'https://meli.me/' + pid[:3].lower() + '/' + pid.lower() + '?aff=' + username
        created_at = rand_date(joined, first_week_end)
        url_records.append({
            'URL':                    url,
            'AFFILIATE_ID':           aid,
            'MARKETPLACE_PRODUCT_ID': pid,
            'CREATED_AT':             created_at.strftime('%Y-%m-%d'),
            'CLOSED_AT':              None,
            '_created_dt':            created_at,
            '_end_dt':                TODAY,
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

# ── Ballenas: 2 afiliados con impacto desproporcionado en clicks y ventas ────────
N_WHALES               = 2
WHALE_CLICK_MULTIPLIER = 60

top_by_followers = pd.Series(aff_max_followers).nlargest(20).index.tolist()
whale_ids        = set(random.sample(top_by_followers, N_WHALES))
print(f'Ballenas designadas    : AFFILIATE_ID {sorted(whale_ids)}')

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
# Amplificar clicks de las ballenas DESPUÉS del escalado para no colapsar el presupuesto base
whale_url_mask = df_urls['AFFILIATE_ID'].isin(whale_ids).values
df_urls.loc[whale_url_mask, '_n_clicks'] = (
    df_urls.loc[whale_url_mask, '_n_clicks'] * WHALE_CLICK_MULTIPLIER
).astype(int)

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

effective_cr = CONVERSION_RATE * SALES_MULTIPLIER   # tasa efectiva de conversión

url_to_country = (
    df_urls[['URL', 'AFFILIATE_ID']]
    .merge(df_affiliates[['AFFILIATE_ID', 'COUNTRY']], on='AFFILIATE_ID')
    .set_index('URL')['COUNTRY']
    .to_dict()
)

url_to_pid = df_urls.set_index('URL')['MARKETPLACE_PRODUCT_ID'].to_dict()
url_to_aid = df_urls.set_index('URL')['AFFILIATE_ID'].to_dict()

sale_mask     = rng.random(len(df_access_logs)) < effective_cr
df_sales_base = df_access_logs[sale_mask].copy().reset_index(drop=True)

df_sales_base['ACCESS_DATETIME']  = pd.to_datetime(df_sales_base['ACCESS_DATETIME'])
min_offset = rng.integers(1, 45, size=len(df_sales_base))
df_sales_base['PURCHASE_DATETIME'] = (
    df_sales_base['ACCESS_DATETIME'] + pd.to_timedelta(min_offset, unit='m')
).clip(upper=pd.Timestamp(TODAY))

df_sales_base['COUNTRY'] = df_sales_base['URL'].map(url_to_country).fillna('BRA')
prices = np.zeros(len(df_sales_base))
for country, (mu, sigma) in PRICE_LOGNORMAL.items():
    lo, hi = PRICE_CLAMP[country]
    mask   = (df_sales_base['COUNTRY'] == country).values
    if mask.sum() > 0:
        raw           = rng.lognormal(mean=mu, sigma=sigma, size=int(mask.sum()))
        prices[mask]  = np.clip(np.round(raw, 2), lo, hi)
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
print('Ventas orgánicas       :', f'{len(df_facts_sales):,}', f'(conv. rate {real_cr}%)')

# ── Ventas garantizadas para afiliados Jira en su primera semana ──────────────
_jira_min = max(1, int(JIRA_SALES_MIN * SALES_MULTIPLIER))
_jira_max = max(_jira_min + 1, int(JIRA_SALES_MAX * SALES_MULTIPLIER))

jira_aff_ids   = set(df_affiliates[df_affiliates['_source'] == 'jira']['AFFILIATE_ID'])
aff_joined_map = df_affiliates.set_index('AFFILIATE_ID')['_joined'].to_dict()

df_urls['_created_dt_dt'] = pd.to_datetime(df_urls['_created_dt'])
df_urls['_aff_joined']    = pd.to_datetime(df_urls['AFFILIATE_ID'].map(aff_joined_map))

jira_first_week_urls = df_urls[
    df_urls['AFFILIATE_ID'].isin(jira_aff_ids) &
    (df_urls['_created_dt_dt'] <= df_urls['_aff_joined'] + timedelta(days=7))
].copy()

df_urls.drop(columns=['_created_dt_dt', '_aff_joined'], inplace=True, errors='ignore')

jira_sales_records = []
for aff_id, group in jira_first_week_urls.groupby('AFFILIATE_ID'):
    joined         = aff_joined_map[aff_id]
    first_week_end = min(joined + timedelta(days=7), TODAY)
    n_sales        = int(rng.integers(_jira_min, _jira_max + 1))

    for _ in range(n_sales):
        url_row  = group.sample(1).iloc[0]
        url      = url_row['URL']
        pid      = url_row['MARKETPLACE_PRODUCT_ID']
        country  = url_to_country.get(url, 'BRA')
        currency = CURRENCY_MAP[country]
        price    = rand_price(country)

        days_range  = max((first_week_end - joined).days, 1)
        purchase_dt = joined + timedelta(
            days    = int(rng.integers(0, days_range)),
            hours   = int(rng.integers(8, 22)),
            minutes = int(rng.integers(0, 60)),
        )
        purchase_dt = min(purchase_dt, TODAY)

        jira_sales_records.append({
            'URL':                    url,
            'AFFILIATE_ID':           aff_id,
            'BUYER_MELI_USER_ID':     int(rng.integers(10_000_000, 99_999_999)),
            'MARKETPLACE_PRODUCT_ID': pid,
            'PURCHASE_DATETIME':      purchase_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'COUNTRY':                country,
            'CURRENCY':               currency,
            'PRICE':                  price,
        })

if jira_sales_records:
    df_jira_guaranteed = pd.DataFrame(jira_sales_records)
    df_facts_sales     = pd.concat([df_facts_sales, df_jira_guaranteed], ignore_index=True)
    print(f'Ventas garantizadas Jira   : {len(df_jira_guaranteed):,}  ({len(jira_aff_ids)} afiliados)')

print('Total ventas           :', f'{len(df_facts_sales):,}')
print('\nPrecio promedio por país:')
print(df_sales_base.groupby('COUNTRY')['PRICE'].agg(['mean','min','max']).round(0).to_string())


# ================================================================
# SECCIÓN 10 — Exportar CSVs
# ================================================================

EXPORT_COLS = {
    'DIM_AFFILIATES': [
        'AFFILIATE_ID', 'MELI_USERNAME', 'MELI_USER_ID', 'AFFILIATED_AT', 'COUNTRY', 'CATEGORY',
        'INSTAGRAM_HANDLE', 'INSTAGRAM_FOLLOWER_COUNT',
        'TIKTOK_HANDLE', 'TIKTOK_FOLLOWER_COUNT',
    ],
    'FACTS_REGISTERED_SOCIAL_MEDIA': [
        'SM_ID', 'AFFILIATE_ID', 'SOCIAL_MEDIA', 'URL', 'FOLLOWERS',
    ],
    'FACTS_JIRA_HUNTING_AFILIADOS': [
        'JIRA_KEY', 'MELI_USERNAME', 'HUNTER', 'NOMBRE',
        'FECHA_ASIGNACION', 'ULTIMO_CONTACTO', 'INSTAGRAM', 'TIKTOK',
        'ESTADO', 'ASIGNADO', 'CONTACTADO', 'AFILIADO', 'RECHAZADO',
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
}

DATAFRAMES = {
    'DIM_AFFILIATES':                            df_dim_affiliates,
    'FACTS_REGISTERED_SOCIAL_MEDIA':             df_sm,
    'FACTS_JIRA_HUNTING_AFILIADOS':              df_facts_jira,
    'FACTS_MARKETPLACE_AFFILIATE_URLS':          df_urls,
    'FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS':  df_access_logs,
    'FACTS_AFFILIATES_MARKETPLACE_SALES':        df_facts_sales,
    'DIM_AFFILIATES_MARKETPLACE_PRODUCTS':       df_dim_products,
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
