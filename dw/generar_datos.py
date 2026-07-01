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

# Throughput relativo de hunters (definido en config; vector numpy para np.choice)
_ht      = HUNTER_THROUGHPUT
_hunter_w = _ht / _ht.sum()   # pesos normalizados

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
    """Avanza al siguiente día hábil (saltea fines de semana y feriados ARG)."""
    while d.weekday() >= 5 or d.date() in ARG_HOLIDAYS:
        d += timedelta(days=1)
    return d

def prev_business_day(d):
    """Retrocede al día hábil anterior (saltea fines de semana y feriados ARG)."""
    while d.weekday() >= 5 or d.date() in ARG_HOLIDAYS:
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

# ── CDF numérica para la distribución de fechas de asignación ────────────────
# La tasa de contactos/semana sigue una curva logarítmica:
#   r(t) = RATE_START + (RATE_MAX - RATE_START) * log(1+α·t/T_ramp) / log(1+α)  para t ≤ T_ramp
#   r(t) = RATE_MAX                                                                 para t > T_ramp
# Esto genera más leads al comienzo y se estabiliza en HUNTER_RAMP_WEEKS semanas.
_LOG_ALPHA  = 7.0       # curvatura del log (α). Mayor valor = ramp más empinada al inicio
_N_BINS     = 4_000     # resolución de la CDF numérica

_t_pts = np.linspace(0.0, JIRA_PERIOD_WEEKS, _N_BINS + 1)

def _hunter_rate(t_w):
    if t_w <= HUNTER_RAMP_WEEKS:
        return HUNTER_RATE_START + (HUNTER_RATE_MAX - HUNTER_RATE_START) * \
               np.log1p(_LOG_ALPHA * t_w / HUNTER_RAMP_WEEKS) / np.log1p(_LOG_ALPHA)
    return HUNTER_RATE_MAX

_r_pts = np.array([_hunter_rate(t) for t in _t_pts])

# Ruido semanal: cada semana del período recibe un multiplicador LogNormal(0, σ).
# Semilla separada para que el ruido sea reproducible pero independiente del resto.
_n_weeks_noise = int(np.ceil(JIRA_PERIOD_WEEKS)) + 1
_week_noise    = np.random.default_rng(SEED + 7).lognormal(
                     mean=0.0, sigma=HUNTER_WEEKLY_NOISE_SIGMA, size=_n_weeks_noise)
_r_pts_noisy   = _r_pts * np.array([
                     _week_noise[min(int(t), _n_weeks_noise - 1)] for t in _t_pts])

# CDF con ruido: redistribuye las fechas de asignación con variación semanal visible
_cdf_raw = np.concatenate([[0.0],
    np.cumsum((_r_pts_noisy[:-1] + _r_pts_noisy[1:]) * 0.5 * np.diff(_t_pts))])
_cdf_raw /= _cdf_raw[-1]

def _sample_t_frac():
    """Devuelve t ∈ [0, 1] muestreado de la distribución logarítmica de asignaciones."""
    u   = float(rng.random())
    idx = int(np.searchsorted(_cdf_raw, u, side='right')) - 1
    idx = max(0, min(idx, _N_BINS - 1))
    lo, hi = _cdf_raw[idx], _cdf_raw[idx + 1]
    denom  = hi - lo
    frac   = (u - lo) / denom if denom > 1e-12 else 0.5
    t_w    = _t_pts[idx] + frac * (_t_pts[idx + 1] - _t_pts[idx])
    return t_w / JIRA_PERIOD_WEEKS

# ── Cola pendiente por hunter al cierre del período ───────────────────────────
# Los hunters contactan sus leads en orden FIFO y solo dejan sin contactar los
# más recientes (los que todavía no llegaron a procesar). El tamaño de esa cola
# parte de HUNTER_MAX_QUEUE y escala inverso al throughput: el hunter de menor
# performance arrastra una cola más grande. Esto reparte los contactos por todo
# el período (evita el "corte" artificial de fechas) en vez de saturar la
# capacidad con los leads más viejos.
_mean_w = float(np.mean(_ht))
HUNTER_QUEUE = {
    name: int(round(HUNTER_MAX_QUEUE * _mean_w / _ht[i]))
    for i, name in enumerate(HUNTER_NAMES)
}

# ── Pool de influencers argentinos (seed real + relleno procedural) ───────────
def _split_name(full):
    parts = full.split()
    return parts[0], (' '.join(parts[1:]) if len(parts) > 1 else parts[0])

influencer_pool = []
used_h = set()   # global: clean(handle) único → evita colisión de MELI_USERNAME luego
for cat in CATEGORIES:
    profiles = []
    for nombre_inf, handle_inf in INFLUENCERS_ARG_SEED.get(cat, []):
        f_inf, l_inf = _split_name(nombre_inf)
        profiles.append({'nombre': nombre_inf, 'ig_handle': handle_inf,
                         'first': f_inf, 'last': l_inf, 'category': cat})
        used_h.add(clean(handle_inf))
    while len(profiles) < N_INFLUENCERS_PER_CAT:
        f_inf, l_inf, nombre_inf = random_name('ARG')
        handle_inf = make_handle(f_inf, l_inf)
        if clean(handle_inf) in used_h:
            continue
        used_h.add(clean(handle_inf))
        profiles.append({'nombre': nombre_inf, 'ig_handle': handle_inf,
                         'first': f_inf, 'last': l_inf, 'category': cat})
    influencer_pool.extend(profiles)

# Motivos de rechazo y sus pesos (normalizados) para el sorteo vectorial.
_MOTIVO_KEYS = list(MOTIVO_RECHAZO_W.keys())
_MOTIVO_W    = np.array(list(MOTIVO_RECHAZO_W.values()), dtype=float)
_MOTIVO_W   /= _MOTIVO_W.sum()

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

    # ~20% de las veces el NOMBRE es el handle de IG (lead cargado por su @)
    if ig_handle and random.random() < NOMBRE_HANDLE_PROB:
        nombre = ig_handle

    if float(rng.random()) < JIRA_FUNNEL['pool']:
        hunter_idx       = None
        fecha_asignacion = None
    else:
        hunter_idx       = int(rng.choice(len(HUNTER_NAMES), p=_hunter_w))
        t_frac           = _sample_t_frac()   # ramp logarítmico definido en config
        fecha_asignacion = JIRA_START + timedelta(days=int(t_frac * JIRA_PERIOD_DAYS))
        # Solo días hábiles: capear al último día hábil antes de TODAY, luego avanzar si weekend
        fecha_asignacion = min(fecha_asignacion, prev_business_day(TODAY - timedelta(days=1)))
        fecha_asignacion = next_business_day(fecha_asignacion)

    prioridad = int(rng.choice(PRIORITY_LEVELS, p=PRIORITY_W_NORMAL))

    raw_leads.append({
        '_i':               i,
        '_country':         country,
        '_first':           first,
        '_last':            last,
        '_category':        category,
        '_hunter_idx':      hunter_idx,
        '_fecha_asig':      fecha_asignacion,
        '_state':           'pool' if hunter_idx is None else None,
        '_prioridad':       prioridad,
        '_fecha_contacto':  None,
        '_fecha_cierre':    None,
        '_motivo_rechazo':  None,
        '_is_influencer':   False,
        '_inf_handle':      None,
        'NOMBRE':           nombre,
        'INSTAGRAM':        ig_handle,
        'TIKTOK':           tt_handle,
    })

# ── Inyección de influencers (siempre asignados, nunca pool) ──────────────────
for k, prof in enumerate(influencer_pool):
    hunter_idx       = int(rng.choice(len(HUNTER_NAMES), p=_hunter_w))
    t_frac           = _sample_t_frac()
    fecha_asignacion = JIRA_START + timedelta(days=int(t_frac * JIRA_PERIOD_DAYS))
    fecha_asignacion = min(fecha_asignacion, prev_business_day(TODAY - timedelta(days=1)))
    fecha_asignacion = next_business_day(fecha_asignacion)

    tt_handle = prof['ig_handle'] if random.random() < 0.8 else make_handle(prof['first'], prof['last'])
    prioridad = int(rng.choice(PRIORITY_LEVELS, p=PRIORITY_W_INFLUENCER))

    raw_leads.append({
        '_i':               90_000 + k,
        '_country':         'ARG',
        '_first':           prof['first'],
        '_last':            prof['last'],
        '_category':        prof['category'],
        '_hunter_idx':      hunter_idx,
        '_fecha_asig':      fecha_asignacion,
        '_state':           None,
        '_prioridad':       prioridad,
        '_fecha_contacto':  None,
        '_fecha_cierre':    None,
        '_motivo_rechazo':  None,
        '_is_influencer':   True,
        '_inf_handle':      prof['ig_handle'],
        'NOMBRE':           prof['nombre'],
        'INSTAGRAM':        prof['ig_handle'],
        'TIKTOK':           tt_handle,
    })

# ── Fase 2: Procesar leads por hunter en orden FIFO ──────────────────────────
for h_idx in range(len(HUNTER_NAMES)):
    hunter_name = HUNTER_NAMES[h_idx]
    queue_size  = HUNTER_QUEUE[hunter_name]

    # Solo los leads de este hunter
    h_leads = [l for l in raw_leads if l['_hunter_idx'] == h_idx]

    # FIFO: más antiguo primero
    h_leads.sort(key=lambda l: l['_fecha_asig'])

    # Contacta todos menos los `queue_size` más recientes (cola pendiente al cierre)
    n_contact = max(len(h_leads) - queue_size, 0)

    for j, lead in enumerate(h_leads):
        fecha_asig = lead['_fecha_asig']
        t = min((fecha_asig - JIRA_START).days / JIRA_PERIOD_DAYS, 1.0)

        prio         = lead['_prioridad']
        team_delay   = 3.0 - 2.0 * t
        team_cr      = 0.08 + 0.10 * t
        hunter_delay = max(team_delay + HUNTER_DELAY_DELTA[hunter_name], 0.3)
        # La prioridad sube/baja la probabilidad de afiliar (moderado, relativo a P3).
        hunter_cr    = float(np.clip(team_cr + HUNTER_CR_DELTA[hunter_name]
                                     + PRIORITY_CR_DELTA[prio], 0.03, 0.40))

        # Los influencers siempre son contactados (no caen en la cola pendiente)
        if j < n_contact or lead['_is_influencer']:
            # FECHA_CONTACTO: pasaje asignado → contactado
            delay_days     = int(np.clip(rng.normal(hunter_delay, 1.5), 0, 14))
            contact_date   = next_business_day(fecha_asig + timedelta(days=delay_days))
            contact_date   = min(contact_date, prev_business_day(TODAY - timedelta(days=1)))
            lead['_fecha_contacto'] = contact_date

            if lead['_is_influencer']:
                # Alta conversión, nunca rechazado → llegan a fase final
                inf_prob = float(np.clip(INFLUENCER_AFILIADO_PROB + PRIORITY_CR_DELTA[prio], 0.5, 0.97))
                lead['_state'] = 'afiliado' if rng.random() < inf_prob else 'contactado'
            else:
                r = float(rng.random())
                if r < hunter_cr:
                    lead['_state'] = 'afiliado'
                elif r < hunter_cr + 0.55:
                    lead['_state'] = 'rechazado'
                    lead['_motivo_rechazo'] = str(rng.choice(_MOTIVO_KEYS, p=_MOTIVO_W))
                else:
                    lead['_state'] = 'contactado'

            # FECHA_CIERRE: pasaje contactado → afiliado/rechazado (solo si cerró)
            if lead['_state'] in ('afiliado', 'rechazado'):
                close_delay  = int(np.clip(rng.normal(CLOSE_DELAY_MEAN, CLOSE_DELAY_SD), 1, 30))
                cierre       = next_business_day(contact_date + timedelta(days=close_delay))
                cierre       = min(cierre, prev_business_day(TODAY - timedelta(days=1)))
                lead['_fecha_cierre'] = cierre
        else:
            # Lead en cola de espera (los más recientes, cap HUNTER_MAX_QUEUE)
            lead['_state'] = 'asignado'

# ── Fase 3: Construir df_jira_raw ─────────────────────────────────────────────
jira_rows = []
for lead in raw_leads:
    fec = lead['_fecha_asig']
    fco = lead['_fecha_contacto']
    fci = lead['_fecha_cierre']
    jira_rows.append({
        '_i':               lead['_i'],
        '_state':           lead['_state'],
        '_country':         lead['_country'],
        '_first':           lead['_first'],
        '_last':            lead['_last'],
        '_category':        lead['_category'],
        '_hunter_idx':      lead['_hunter_idx'],
        '_is_influencer':   lead['_is_influencer'],
        '_inf_handle':      lead['_inf_handle'],
        '_prioridad':       lead['_prioridad'],
        'NOMBRE':           lead['NOMBRE'],
        'INSTAGRAM':        lead['INSTAGRAM'],
        'TIKTOK':           lead['TIKTOK'],
        'PRIORIDAD':        lead['_prioridad'],
        'MOTIVO_RECHAZO':   lead['_motivo_rechazo'],
        'FECHA_ASIGNACION': fec.strftime('%Y-%m-%d') if fec else None,
        'FECHA_CONTACTO':   fco.strftime('%Y-%m-%d') if fco else None,
        'FECHA_CIERRE':     fci.strftime('%Y-%m-%d') if fci else None,
    })

df_jira_raw = pd.DataFrame(jira_rows)

print('Leads Jira generados :', len(df_jira_raw))
print(df_jira_raw['_state'].value_counts().to_string())
_inf_df = df_jira_raw[df_jira_raw['_is_influencer']]
print(f'\nInfluencers inyectados : {len(_inf_df)}  '
      f'(afiliados: {(_inf_df["_state"] == "afiliado").sum()}, '
      f'contactados: {(_inf_df["_state"] == "contactado").sum()})')
print('\nCola y procesados por hunter:')
for h_idx in range(len(HUNTER_NAMES)):
    name     = HUNTER_NAMES[h_idx]
    queue    = HUNTER_QUEUE[name]
    h_df     = df_jira_raw[df_jira_raw['_hunter_idx'] == h_idx]
    n_asig   = (h_df['_state'] == 'asignado').sum()
    n_proc   = len(h_df) - n_asig
    print(f'  {name:<22}  cola={queue:4d}  leads={len(h_df):5d}  proc={n_proc:5d}  asig={n_asig:3d}')


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
    is_inf   = bool(row['_is_influencer'])
    inf_handle = row['_inf_handle'] if is_inf else None
    # Influencer → username derivado de su handle real (reconocible)
    username = clean(inf_handle) if is_inf else make_username(first, last, raw_i)
    uid      = int(rng.integers(10_000_000, 99_999_999))
    # Fecha de afiliación = FECHA_CIERRE (cierre como afiliado); fallback aleatorio.
    _fci   = row['FECHA_CIERRE']
    joined = datetime.strptime(_fci, '%Y-%m-%d') if _fci else rand_date(JIRA_START, TODAY - timedelta(days=3))
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
        '_is_influencer': is_inf,
        '_inf_handle':   inf_handle,
        '_prioridad':    int(row['_prioridad']),
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
        '_is_influencer': False,
        '_inf_handle':   None,
        '_prioridad':    3,   # orgánicos: prioridad neutra (no vienen de Jira)
    })

df_affiliates = pd.DataFrame(aff_records)
df_affiliates = df_affiliates.drop_duplicates('MELI_USERNAME').reset_index(drop=True)
df_affiliates['AFFILIATE_ID'] = range(1, len(df_affiliates) + 1)

# IDs de afiliados influencer (para boostear followers/URLs/clicks/ventas)
influencer_aff_ids = set(df_affiliates[df_affiliates['_is_influencer']]['AFFILIATE_ID'])
# Mapa AFFILIATE_ID → PRIORIDAD (para escalar followers y ventas por prioridad)
prio_map = df_affiliates.set_index('AFFILIATE_ID')['_prioridad'].to_dict()

print('Total afiliados base   :', len(df_affiliates))
print('Afiliados influencer   :', len(influencer_aff_ids))


# ================================================================
# SECCIÓN 5 — FACTS_REGISTERED_SOCIAL_MEDIA
#             + backfill IG/TikTok en df_affiliates → DIM_AFFILIATES
# ================================================================

sm_records = []
sm_id_seq  = [1]

for _, aff in df_affiliates.iterrows():
    first  = aff['_first']
    last   = aff['_last']
    aid    = aff['AFFILIATE_ID']
    is_inf = aff['_is_influencer']

    chosen = [p for p, prob in PLAT_PROB.items() if random.random() < prob]
    if not chosen:
        chosen = ['instagram']
    if is_inf and 'instagram' not in chosen:
        chosen = ['instagram'] + chosen   # el influencer siempre tiene IG

    # Followers escalados por prioridad (fama): más prioridad → más followers.
    prio = int(aff['_prioridad'])
    if is_inf:
        # Influencer: 300K–2M, con un nudge extra para la elite (P5).
        main_followers = int(rng.uniform(INFLUENCER_FOLLOWER_LO, INFLUENCER_FOLLOWER_HI)
                             * PRIORITY_INFLU_FAME.get(prio, 1.0))
    else:
        main_followers = int(follower_count(1)[0] * PRIORITY_FAME_MULT[prio])

    for j, plat in enumerate(chosen):
        if j == 0:
            followers = main_followers
        else:
            ratio     = float(rng.uniform(0.08, 0.75))
            followers = max(1_000, int(main_followers * ratio))

        # IG del influencer usa su handle real; el resto se generan
        if plat == 'instagram' and is_inf:
            handle = aff['_inf_handle']
        else:
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

_is_inf_col = df_dim_affiliates['AFFILIATE_ID'].isin(influencer_aff_ids)
_inf_fw     = df_dim_affiliates.loc[_is_inf_col, 'INSTAGRAM_FOLLOWER_COUNT'].dropna()
_rest_fw    = df_dim_affiliates.loc[~_is_inf_col, 'INSTAGRAM_FOLLOWER_COUNT'].dropna()
if len(_inf_fw) and len(_rest_fw):
    print(f'  Followers IG promedio  : influencer {_inf_fw.mean():,.0f}  vs  resto {_rest_fw.mean():,.0f}')


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
        'HUNTER_JIRA_ID':    HUNTER_JIRA_ID.get(hunter),
        'NOMBRE':            row['NOMBRE'],
        'PRIORIDAD':         int(row['_prioridad']),
        'FECHA_ASIGNACION':  row['FECHA_ASIGNACION'],
        'FECHA_CONTACTO':    row['FECHA_CONTACTO'],
        'FECHA_CIERRE':      row['FECHA_CIERRE'],
        'INSTAGRAM':         row['INSTAGRAM'],
        'TIKTOK':            row['TIKTOK'],
        'ESTADO':     state,
        'ASIGNADO':   state in ('asignado', 'contactado', 'afiliado', 'rechazado'),
        'CONTACTADO': state in ('contactado', 'afiliado', 'rechazado'),
        'AFILIADO':   state == 'afiliado',
        'RECHAZADO':  state == 'rechazado',
        'MOTIVO_RECHAZO':    row['MOTIVO_RECHAZO'],
    })

df_facts_jira = pd.DataFrame(jira_out)

# ── Leads de test — para ejercicio de filtrado SQL del bootcamp ──────────────
# Detección: LOWER(NOMBRE) LIKE '%test%'
_ID_FEDE = HUNTER_JIRA_ID['Federico Quinteros']
_ID_FRAN = HUNTER_JIRA_ID['Francisco Rodriguez']
_ID_NICO = HUNTER_JIRA_ID['Nicolás Vrancovich']

# Fechas ancladas a la ventana operativa (no hardcodeadas) para que los test
# caigan siempre dentro del período denso y no creen semanas aisladas con
# conversión 100 % al inicio, aun si cambia TODAY.
def _td(days):
    return (JIRA_START + timedelta(days=days)).strftime('%Y-%m-%d')

_test_rows = [
    {'JIRA_KEY':'HUNT-99980','MELI_USERNAME':None,               'HUNTER':'Federico Quinteros','HUNTER_JIRA_ID':_ID_FEDE,'NOMBRE':'Test',        'PRIORIDAD':3,'FECHA_ASIGNACION':_td(60),'FECHA_CONTACTO':None,    'FECHA_CIERRE':None,    'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'asignado',  'ASIGNADO':True, 'CONTACTADO':False,'AFILIADO':False,'RECHAZADO':False,'MOTIVO_RECHAZO':None},
    {'JIRA_KEY':'HUNT-99981','MELI_USERNAME':None,               'HUNTER':'Francisco Rodriguez','HUNTER_JIRA_ID':_ID_FRAN,'NOMBRE':'Test Lead',   'PRIORIDAD':2,'FECHA_ASIGNACION':_td(45),'FECHA_CONTACTO':_td(47),'FECHA_CIERRE':None,    'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'contactado','ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':False,'RECHAZADO':False,'MOTIVO_RECHAZO':None},
    {'JIRA_KEY':'HUNT-99982','MELI_USERNAME':'test_afiliado_001','HUNTER':'Nicolás Vrancovich','HUNTER_JIRA_ID':_ID_NICO,'NOMBRE':'test_usuario','PRIORIDAD':5,'FECHA_ASIGNACION':_td(50),'FECHA_CONTACTO':_td(52),'FECHA_CIERRE':_td(56),'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'afiliado',  'ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':True, 'RECHAZADO':False,'MOTIVO_RECHAZO':None},
    {'JIRA_KEY':'HUNT-99983','MELI_USERNAME':None,               'HUNTER':'Federico Quinteros','HUNTER_JIRA_ID':_ID_FEDE,'NOMBRE':'TEST DUMMY',  'PRIORIDAD':3,'FECHA_ASIGNACION':_td(70),'FECHA_CONTACTO':_td(72),'FECHA_CIERRE':_td(75),'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'rechazado', 'ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':False,'RECHAZADO':True, 'MOTIVO_RECHAZO':'No respondió después de 7 días'},
    {'JIRA_KEY':'HUNT-99984','MELI_USERNAME':None,               'HUNTER':None,                'HUNTER_JIRA_ID':None,    'NOMBRE':'Prueba Test', 'PRIORIDAD':3,'FECHA_ASIGNACION':None,    'FECHA_CONTACTO':None,    'FECHA_CIERRE':None,    'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'pool',      'ASIGNADO':False,'CONTACTADO':False,'AFILIADO':False,'RECHAZADO':False,'MOTIVO_RECHAZO':None},
    {'JIRA_KEY':'HUNT-99985','MELI_USERNAME':'test_afiliado_002','HUNTER':'Francisco Rodriguez','HUNTER_JIRA_ID':_ID_FRAN,'NOMBRE':'Test Nico',   'PRIORIDAD':4,'FECHA_ASIGNACION':_td(55),'FECHA_CONTACTO':_td(57),'FECHA_CIERRE':_td(60),'INSTAGRAM':None,'TIKTOK':None,'ESTADO':'afiliado',  'ASIGNADO':True, 'CONTACTADO':True, 'AFILIADO':True, 'RECHAZADO':False,'MOTIVO_RECHAZO':None},
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

print('\nDistribución de PRIORIDAD (todos los leads):')
_pri = df_facts_jira['PRIORIDAD'].value_counts(normalize=True).sort_index()
for lvl, frac in _pri.items():
    print(f'  P{lvl}: {frac*100:5.1f}%')
_inf_pri = df_jira_raw[df_jira_raw['_is_influencer']]['_prioridad'].value_counts().sort_index()
print('  Influencers por prioridad:', _inf_pri.to_dict())

print('\nMotivos de rechazo:')
print(df_facts_jira[df_facts_jira['RECHAZADO']]['MOTIVO_RECHAZO'].value_counts(normalize=True).round(3).to_string())


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

    # Influencer: más URLs (mayor actividad de promoción)
    if aff['_is_influencer']:
        n_urls = int(np.clip(n_urls * INFLUENCER_URL_MULT, 2, 60))

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

# Influencers: amplificación más suave que las ballenas, para que destaquen
influencer_url_mask = df_urls['AFFILIATE_ID'].isin(influencer_aff_ids).values
df_urls.loc[influencer_url_mask, '_n_clicks'] = (
    df_urls.loc[influencer_url_mask, '_n_clicks'] * INFLUENCER_CLICK_MULT
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
# Distribución lognormal sin techo fijo: mediana ≈ exp(JIRA_SALES_MU) ≈ 25 ventas.

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
    n_sales        = max(JIRA_SALES_FLOOR, int(rng.lognormal(mean=JIRA_SALES_MU, sigma=JIRA_SALES_SIGMA)))
    if aff_id in influencer_aff_ids:
        n_sales = int(n_sales * INFLUENCER_SALES_MULT)   # influencer vende más
    # Prioridad escala las ventas (plata): P5 vende más, P2 menos.
    n_sales = max(JIRA_SALES_FLOOR, int(n_sales * PRIORITY_SALES_MULT[prio_map.get(aff_id, 3)]))

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

    # Gradiente por prioridad (afiliados Jira): confirma que más prioridad = más plata/fama
    _g = df_jira_guaranteed.copy()
    _g['PRIORIDAD']  = _g['AFFILIATE_ID'].map(prio_map)
    _fw = df_dim_affiliates.set_index('AFFILIATE_ID')['INSTAGRAM_FOLLOWER_COUNT'].to_dict()
    _g['FOLLOWERS']  = _g['AFFILIATE_ID'].map(_fw)
    print('  Gradiente por prioridad (afiliados Jira):')
    for lvl, grp in _g.groupby('PRIORIDAD'):
        ventas_x_aff = len(grp) / grp['AFFILIATE_ID'].nunique()
        fw_prom      = grp.drop_duplicates('AFFILIATE_ID')['FOLLOWERS'].mean()
        print(f'    P{int(lvl)}: {ventas_x_aff:5.1f} ventas/afiliado  ·  followers IG prom {fw_prom:,.0f}')

# ── Ventas estacionales (eventos) ────────────────────────────────────────────
# Se inyectan ventas extra en el período de cada evento para que el gráfico
# de ventas diarias muestre picos visibles. Las ventas respetan el filtro de
# categoría de producto cuando se especifica cat1_filter.
pid_to_cat1 = df_dim_products.set_index('MARKETPLACE_PRODUCT_ID')['CATEGORY_AGG_1'].to_dict()

print('\nEventos estacionales:')
for ev in SALES_EVENTS:
    ev_start = pd.Timestamp(ev['start'])
    ev_end   = pd.Timestamp(ev['end']) + pd.Timedelta(hours=23, minutes=59, seconds=59)

    ev_urls = df_urls[
        (df_urls['_created_dt'] <= ev_end) &
        (df_urls['_end_dt']     >= ev_start)
    ].copy()

    if ev.get('cat1_filter'):
        ev_urls['_cat1'] = ev_urls['MARKETPLACE_PRODUCT_ID'].map(pid_to_cat1)
        ev_urls = ev_urls[ev_urls['_cat1'].isin(ev['cat1_filter'])]
        ev_urls.drop(columns=['_cat1'], inplace=True)

    n_extra = ev['extra_sales']
    if len(ev_urls) == 0 or n_extra == 0:
        print(f'  {ev["name"]}: sin URLs activas, saltado')
        continue

    idx        = rng.integers(0, len(ev_urls), size=n_extra)
    ev_sampled = ev_urls.iloc[idx].reset_index(drop=True)

    dur_s   = max(int((ev_end - ev_start).total_seconds()), 1)
    offsets = rng.integers(0, dur_s + 1, size=n_extra)
    ev_sampled['PURCHASE_DATETIME'] = ev_start + pd.to_timedelta(offsets, unit='s')
    ev_sampled['COUNTRY']  = ev_sampled['URL'].map(url_to_country).fillna('BRA')
    ev_sampled['CURRENCY'] = ev_sampled['COUNTRY'].map(CURRENCY_MAP)

    ev_prices = np.zeros(n_extra)
    for country, (mu_p, sigma_p) in PRICE_LOGNORMAL.items():
        lo, hi = PRICE_CLAMP[country]
        m      = (ev_sampled['COUNTRY'] == country).values
        if m.sum() > 0:
            raw          = rng.lognormal(mean=mu_p, sigma=sigma_p, size=int(m.sum()))
            ev_prices[m] = np.clip(np.round(raw, 2), lo, hi)
    ev_sampled['PRICE']              = ev_prices
    ev_sampled['AFFILIATE_ID']       = ev_sampled['URL'].map(url_to_aid)
    ev_sampled['BUYER_MELI_USER_ID'] = rng.integers(10_000_000, 99_999_999, size=n_extra)

    ev_df = ev_sampled[[
        'URL', 'AFFILIATE_ID', 'BUYER_MELI_USER_ID', 'MARKETPLACE_PRODUCT_ID',
        'PURCHASE_DATETIME', 'COUNTRY', 'CURRENCY', 'PRICE',
    ]].copy()
    ev_df['PURCHASE_DATETIME'] = ev_df['PURCHASE_DATETIME'].dt.strftime('%Y-%m-%d %H:%M:%S')

    df_facts_sales = pd.concat([df_facts_sales, ev_df], ignore_index=True)
    print(f'  {ev["name"]:<28} +{n_extra:,} ventas')

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
        'JIRA_KEY', 'MELI_USERNAME', 'HUNTER', 'HUNTER_JIRA_ID', 'NOMBRE',
        'PRIORIDAD', 'FECHA_ASIGNACION', 'FECHA_CONTACTO', 'FECHA_CIERRE',
        'INSTAGRAM', 'TIKTOK',
        'ESTADO', 'ASIGNADO', 'CONTACTADO', 'AFILIADO', 'RECHAZADO',
        'MOTIVO_RECHAZO',
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
