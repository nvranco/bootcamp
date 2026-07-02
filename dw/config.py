# ================================================================
# config.py — Parámetros de generación de datos
# Bootcamp BI Analyst — Programa de Afiliados Mercado Libre
#
# Editar este archivo para cambiar el comportamiento del generador
# sin tocar la lógica en generar_datos.py
# ================================================================

import numpy as np
from datetime import datetime, timedelta, date

# ── Semilla aleatoria ──────────────────────────────────────────
SEED = 42

# ── Fecha de corte ─────────────────────────────────────────────
TODAY      = datetime(2026, 6, 27)
JIRA_START = TODAY - timedelta(days=150)

PROGRAM_LAUNCH = {
    'BRA': TODAY - timedelta(days=365 * 3),
    'MEX': TODAY - timedelta(days=365 * 3),
    'ARG': TODAY - timedelta(days=365),
    'CHI': TODAY - timedelta(days=365),
}

# ── Escala ─────────────────────────────────────────────────────
N_AFFILIATES         = 50_000   # total de afiliados en el programa
N_JIRA_TOTAL         = 838      # total de leads en el tablero Jira (~950 filas con influencers)
N_PRODUCT_POOL       = 12_000   # productos en el pool del marketplace
N_TARGET_ACCESS_LOGS = 100_000  # volumen total de access logs (clics)

# ── Ventas ─────────────────────────────────────────────────────
# SALES_MULTIPLIER escala el volumen de ventas orgánicas.
#   1.0 = tasa base del 3 % (aprox. 3 000 ventas orgánicas)
#   3.0 = 9 % efectivo (aprox. 9 000 ventas orgánicas)
#   5.0 = 15 % efectivo (aprox. 15 000 ventas orgánicas)
# Las ventas garantizadas para afiliados Jira se escalan igual.
SALES_MULTIPLIER = 3.0

CONVERSION_RATE = 0.030   # tasa de conversión base clics → ventas

# Ventas garantizadas para afiliados Jira: distribución lognormal sin techo fijo.
# Mediana ≈ exp(JIRA_SALES_MU) ≈ 25 ventas; cola larga hacia 100+.
JIRA_SALES_MU    = 3.2    # ln(mediana) — mediana ≈ 25 ventas por afiliado
JIRA_SALES_SIGMA = 0.8    # σ — p5 ≈ 7, p95 ≈ 91, p99 ≈ 145 ventas
JIRA_SALES_FLOOR = 5      # piso absoluto (independiente de SALES_MULTIPLIER)

# Volumen de facturación de afiliados Jira: para llevar su facturación por encima
# de USD 2M se multiplica la CANTIDAD de ventas garantizadas por afiliado (el ticket
# no se toca). Ver Sección 9 en generar_datos.py.
JIRA_SALES_VOLUME_MULT = 3.1   # multiplicador global de ventas por afiliado Jira
# Ballenas Jira: unos pocos afiliados del hunting con ventas desproporcionadas.
JIRA_WHALE_COUNT       = 15    # cantidad de afiliados Jira "ballena"
JIRA_WHALE_SALES_MULT  = 10    # multiplicador de ventas de cada ballena (encima del global)

# ── Países ─────────────────────────────────────────────────────
COUNTRIES = ['BRA', 'MEX', 'ARG', 'CHI']
COUNTRY_W = [0.30,  0.30,  0.20,  0.20]

MELI_CODE    = {'ARG': 'MLA', 'BRA': 'MLB', 'MEX': 'MLM', 'CHI': 'MLC'}
CURRENCY_MAP = {'ARG': 'ARS', 'BRA': 'BRL', 'MEX': 'MXN', 'CHI': 'CLP'}
FX_ANCHOR    = {'ARS': 1100.0, 'BRL': 5.8, 'MXN': 17.5, 'CLP': 960.0}

# ── Categorías de afiliados ────────────────────────────────────
# Los pesos reflejan la distribución real del mercado de influencers:
# lifestyle y beauty dominan; education y other son nichos pequeños.
CATEGORIES = [
    'lifestyle', 'beauty', 'fitness', 'tech',
    'food', 'travel', 'home_deco', 'education', 'other',
]
CATEGORY_W = [
    0.22,        0.18,     0.15,      0.12,
    0.10,   0.08,     0.07,         0.05,        0.03,
]

# ── Plataformas de redes sociales ──────────────────────────────
PLATFORMS = ['instagram', 'tiktok', 'youtube', 'facebook', 'x', 'other']

PLAT_PROB = {
    'instagram': 0.99,
    'tiktok':    0.95,
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

# ── Productos — taxonomía y pesos de categoría nivel 1 ────────
# Los pesos reflejan la participación real de cada categoría
# en un marketplace LATAM: Electrónica y Ropa dominan;
# Alimentos y Juguetes tienen menor peso relativo.
PRODUCT_CAT1_W = {
    'Electrónica':      0.25,
    'Ropa y Moda':      0.22,
    'Hogar y Deco':     0.15,
    'Deportes':         0.13,
    'Belleza y Salud':  0.12,
    'Alimentos':        0.08,
    'Juguetes y Bebés': 0.05,
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

# ── Precios — distribución lognormal por país ──────────────────
# La mayoría de los productos son económicos; hay una cola larga
# hacia productos caros (distribución real de e-commerce).
#
#   mu, sigma: parámetros del log del precio en moneda local
#   mediana = exp(mu)
#
# Clamp duro para eliminar outliers extremos.
PRICE_LOGNORMAL = {
    #        mu     sigma     mediana aprox.
    'ARG': ( 9.3,   1.3),  # ~11 000 ARS
    'BRA': ( 4.9,   1.2),  # ~134 BRL
    'MEX': ( 6.6,   1.2),  # ~735 MXN
    'CHI': ( 8.6,   1.3),  # ~5 400 CLP
}
PRICE_CLAMP = {
    'ARG': (    500,   500_000),
    'BRA': (     10,     8_000),
    'MEX': (     50,    30_000),
    'CHI': (    300,   400_000),
}

# ── Followers — distribución lognormal ────────────────────────
# Piso de followers: 8 000 × Uniform(FOLLOWER_FLOOR_JITTER_LO, FOLLOWER_FLOOR_JITTER_HI)
# El jitter evita un corte artificial en exactamente 8 000.
FOLLOWER_FLOOR_BASE     = 8_000
FOLLOWER_FLOOR_JITTER_LO = 0.985
FOLLOWER_FLOOR_JITTER_HI = 1.123

# ── Ballenas (afiliados con impacto desproporcionado) ──────────
N_WHALES               = 123
WHALE_CLICK_MULTIPLIER = 60

# ── Hunters ────────────────────────────────────────────────────
# Los nombres son los displayName reales del tablero Jira (proyecto AFHU).
# Orden canónico: alto → medio → medio-bajo (Fede / Fran / Nico).
HUNTER_NAMES = [
    'Federico Quinteros',   # Fede
    'Francisco Rodriguez',  # Fran
    'Nicolás Vrancovich',   # Nico
]

# accountId de Atlassian de cada hunter (para cruzar con la API de Jira)
HUNTER_JIRA_ID = {
    'Federico Quinteros':  '5f26e76870fb250022df96f8',
    'Francisco Rodriguez': '712020:5ec99a7e-5928-4361-9ccd-9d6549e14b12',
    'Nicolás Vrancovich':  '70121:06a5f854-7183-43e5-a317-3b5a446f03ca',
}

# Throughput relativo de cada hunter (afecta cuántos leads procesa = "contactos").
# Sin guion bajo → importable con `from config import *` (lo usa generar_datos.py).
# Fran contacta mucho, Fede media-alta, Nico media-bajo.
HUNTER_THROUGHPUT = np.array([1.10, 1.40, 0.75])   # Fede / Fran / Nico
HUNTER_W          = (HUNTER_THROUGHPUT / HUNTER_THROUGHPUT.sum()).tolist()

# ── Ruido semanal en productividad de hunters ─────────────────
# Cada semana recibe un multiplicador LogNormal(0, σ) independiente.
# σ=0.22 → la mayoría de las semanas está entre ±25 % del promedio;
# ocasionalmente alguna semana cae a ~0.6× o sube a ~1.5×.
HUNTER_WEEKLY_NOISE_SIGMA = 0.22

# ── Feriados nacionales de Argentina (sin actividad de hunting) ──
# Usado en next_business_day / prev_business_day para correr fechas.
ARG_HOLIDAYS = {
    date(2025, 12,  8),  # Inmaculada Concepción
    date(2025, 12, 25),  # Navidad
    date(2026,  1,  1),  # Año Nuevo
    date(2026,  1,  2),  # Feriado puente (frecuente en ARG)
    date(2026,  2, 16),  # Carnaval — lunes
    date(2026,  2, 17),  # Carnaval — martes
    date(2026,  3, 24),  # Día de la Memoria
    date(2026,  4,  2),  # Día del Veterano (Malvinas)
    date(2026,  4, 17),  # Viernes Santo
    date(2026,  5,  1),  # Día del Trabajador
    date(2026,  5, 25),  # Revolución de Mayo
    date(2026,  6, 15),  # Paso a la Inmortalidad del Gral. Güemes (trasladado al lunes)
    date(2026,  6, 20),  # Día de la Bandera
}

# ── Eventos de ventas estacionales ────────────────────────────
# extra_sales: número de ventas adicionales a inyectar en el período.
# cat1_filter: lista de CATEGORY_AGG_1 afectadas, o None para todas.
SALES_EVENTS = [
    {
        'name':        'Black Friday 2025',
        'start':       date(2025, 11, 27),
        'end':         date(2025, 11, 29),
        'extra_sales': 1_800,
        'cat1_filter': None,
    },
    {
        'name':        'CyberMonday ARG 2025',
        'start':       date(2025, 12,  1),
        'end':         date(2025, 12,  3),
        'extra_sales':   900,
        'cat1_filter': ['Electrónica', 'Ropa y Moda'],
    },
    {
        'name':        'Navidad 2025',
        'start':       date(2025, 12, 20),
        'end':         date(2025, 12, 25),
        'extra_sales': 1_000,
        'cat1_filter': ['Juguetes y Bebés', 'Electrónica', 'Ropa y Moda'],
    },
    {
        'name':        'San Valentín 2026',
        'start':       date(2026,  2, 13),
        'end':         date(2026,  2, 14),
        'extra_sales':   600,
        'cat1_filter': ['Belleza y Salud', 'Ropa y Moda'],
    },
    {
        'name':        'Día de la Mujer 2026',
        'start':       date(2026,  3,  8),
        'end':         date(2026,  3,  8),
        'extra_sales':   400,
        'cat1_filter': ['Belleza y Salud', 'Ropa y Moda'],
    },
]

# Ramp-up de contactos por semana (hunter promedio).
# Progresión logarítmica: sube rápido en las primeras HUNTER_RAMP_WEEKS semanas
# y se estabiliza en HUNTER_RATE_MAX a partir de ahí.
HUNTER_RATE_START  =   4.5   # contactos/semana al inicio del período
HUNTER_RATE_MAX    =  11.0   # contactos/semana al estabilizarse
HUNTER_RAMP_WEEKS  =   12.0   # semanas para alcanzar la tasa máxima
HUNTER_MAX_QUEUE   =    12   # máx leads en 'asignado' por hunter al cierre

# Offset de tiempo de respuesta vs. la media del equipo (días; negativo = más rápido)
# Alineado con el volumen de contactos: más actividad → responde más rápido.
HUNTER_DELAY_DELTA = {
    'Federico Quinteros': -0.3,   # Fede media-alta actividad
    'Francisco Rodriguez':-1.0,   # Fran muy activo, contesta rápido
    'Nicolás Vrancovich': +1.2,   # Nico menos activo, más lento
}

# Offset de tasa de conversión vs. la media del equipo (positivo = mejor)
# Fran convierte poco (volumen pero baja calidad), Fede medio, Nico alto.
HUNTER_CR_DELTA = {
    'Federico Quinteros':  0.00,  # Fede conversión media
    'Francisco Rodriguez':-0.06,  # Fran conversión baja
    'Nicolás Vrancovich': +0.05,  # Nico conversión medio-alta
}

# ── Funnel Jira ────────────────────────────────────────────────
JIRA_FUNNEL = {
    'pool':       0.33,   # fracción de leads que quedan sin asignar durante la simulación
    'asignado':   0.10,
    'contactado': 0.10,
    'rechazado':  0.16,
    'afiliado':   0.04,
}

# Poda del Pool al cierre: tras correr la simulación se descartan los leads sobrantes
# en estado 'pool' hasta dejar ~POOL_KEEP. Los leads en pool no tienen datos aguas
# abajo (ni afiliados ni ventas), así que la poda solo achica el tablero final sin
# afectar el resto de las tablas ni la facturación.
POOL_KEEP = 50

# ── Componente random en NOMBRE (FACTS_JIRA_HUNTING_AFILIADOS) ──
# Probabilidad de que el NOMBRE del lead sea su handle de Instagram en vez del
# nombre real (simula al hunter cargando el lead por su @). Solo leads normales;
# los influencers conservan su nombre real para que sean reconocibles.
NOMBRE_HANDLE_PROB = 0.20

# ── Prioridad de leads Jira (1-5; se usan 2-5, pico en 3) ──────
# La PRIORIDAD modela la importancia del lead. La mayoría cae en 3 (medium);
# 2 y 4 son los hombros y 5 la colita (estilo gamma). La prioridad modifica el
# comportamiento: más prioridad → más conversión, más followers y más ventas.
PRIORITY_LEVELS       = [2, 3, 4, 5]
PRIORITY_W_NORMAL     = [0.21, 0.57, 0.18, 0.04]   # leads normales: pico en 3, casi nada en 5
PRIORITY_W_INFLUENCER = [0.00, 0.00, 0.30, 0.70]   # influencers: mayoría 5, algunos 4

# Efecto de la prioridad (moderado). Todo relativo a P3 (neutro).
PRIORITY_CR_DELTA   = {2: -0.06, 3: 0.00, 4: 0.06, 5: 0.12}   # pp sumados a la prob. de afiliar
PRIORITY_SALES_MULT = {2: 0.6,  3: 1.0, 4: 1.6, 5: 2.5}       # multiplicador de ventas garantizadas
PRIORITY_FAME_MULT  = {2: 0.7,  3: 1.0, 4: 1.8, 5: 3.0}       # multiplicador de followers (leads normales)
PRIORITY_INFLU_FAME = {4: 1.0,  5: 1.3}                       # nudge extra de followers para influencer elite

# Demora entre FECHA_CONTACTO y FECHA_CIERRE (días; solo afiliado/rechazado).
CLOSE_DELAY_MEAN = 5.0
CLOSE_DELAY_SD   = 4.0

# ── Motivo de rechazo (solo leads 'rechazado', no equiprobable) ─
# Probabilidades realistas: la falta de respuesta y el desinterés dominan.
MOTIVO_RECHAZO_W = {
    'No respondió después de 7 días':      0.40,
    'No le interesa el programa':          0.30,
    'No está habilitado para facturar':    0.18,
    'Perfil no cumple requisitos mínimos': 0.12,
}

# ── Influencers argentinos inyectados al pool de Jira ──────────
# Se inyectan N_INFLUENCERS_PER_CAT por rubro (todos COUNTRY='ARG'), con alta
# probabilidad de afiliarse y métricas por encima de la media (followers, URLs,
# clicks, ventas). No llevan flag en los datos: destacan solo por sus métricas.
N_INFLUENCERS_PER_CAT    = 12       # influencers por rubro (9 rubros ≈ 108)
INFLUENCER_AFILIADO_PROB = 0.80     # prob. de cerrar como 'afiliado' (resto 'contactado')
INFLUENCER_FOLLOWER_LO   = 300_000  # piso de followers de influencer
INFLUENCER_FOLLOWER_HI   = 2_000_000
INFLUENCER_URL_MULT      = 2        # multiplicador de URLs generadas
INFLUENCER_CLICK_MULT    = 5        # multiplicador de clicks (estilo ballena suave)
INFLUENCER_SALES_MULT    = 2        # multiplicador de ventas garantizadas

# Seed de influencers argentinos reales por rubro: (nombre, handle_instagram).
# El generador rellena cada rubro hasta N_INFLUENCERS_PER_CAT con perfiles ARG
# generados a partir de los pools de nombres.
INFLUENCERS_ARG_SEED = {
    'lifestyle': [
        ('Alejo Igoa', 'alejoigoa'), ('Belén Lupinacci', 'belulupinacci'),
        ('Flor Jazmín Peña', 'florjazminp'), ('Nati Jota', 'natijota'),
        ('Belu Lucius', 'belulucius'), ('Connie Isla', 'conniisla'),
        ('Stephanie Demner', 'stephaniedemner'), ('Zaira Nara', 'zairanara'),
        ('Juana Repetto', 'juanarepettook'), ('Cande Molfese', 'candelariamolfese'),
        ('Ivana Nadal', 'ivunadal'), ('Sofía Gonet', 'lareinadelflow'),
    ],
    'beauty': [
        ('Cande Copello', 'candecopello'), ('Luz Rearte', 'luzrearte'),
        ('Sofi Morandi', 'sofiamorandi'), ('Pin Up Snijders', 'pinupsnijders'),
        ('Maru Marengo', 'marumarengo'), ('Agus Padilla', 'aguspadillaa'),
    ],
    'fitness': [
        ('Mai Pistiner', 'maipistiner'), ('Magui Bravi', 'maguibravi'),
        ('Sofía Pachano', 'sofiapachano'), ('Caro Calvagni', 'carocalvagni'),
        ('Noe Antonelli', 'noeantonelli'),
    ],
    'tech': [
        ('Pelado Nerd', 'peladonerd'), ('Lucas Mostazo', 'lucasmostazo'),
        ('Tecmonster', 'tecmonster'), ('Nardweb', 'nardweb'),
        ('Franco Cavallone', 'francocavallone'),
    ],
    'food': [
        ('Paulina Cocina', 'paulinacocina'), ('Narda Lepes', 'nardalepes'),
        ('Maru Botana', 'marubotana'), ('Felicitas Pizarro', 'felicitaspizarro'),
        ('Juan Ferrara', 'juanferrara'), ('Coco Carreño', 'cococarreno'),
    ],
    'travel': [
        ('Cecilia Volando', 'cecivolando'), ('Martina Tupi', 'tupiviajera'),
        ('Plan B Viajero', 'planbviajero'), ('Algarrobo Travel', 'algarrobotravel'),
    ],
    'home_deco': [
        ('Deco con Alma', 'decoconalma'), ('Mica Deco', 'micadeco'),
        ('Estudio Caramba', 'estudiocaramba'),
    ],
    'education': [
        ('Mate con Vos', 'matevos'), ('Profe Hernán', 'profehernan'),
        ('Inglés con Pablo', 'inglesconpablo'),
    ],
    'other': [
        ('Coscu', 'coscu'), ('Spreen', 'spreen'), ('Davoo Xeneize', 'davooxeneize'),
        ('Momo', 'momoochii'), ('Goncho Banzas', 'goncho'),
        ('Migue Granados', 'miguegranados'), ('Lizardo Ponce', 'lizardoponce'),
        ('Grego Rosello', 'gregorosello'), ('Martín Cirio', 'lafaraona'),
        ('Frankkaster', 'frankkaster'),
    ],
}

# ── Nombres por país ───────────────────────────────────────────
FIRST_NAMES = {
    'ARG': [
        'Valentina','Sofía','Martina','Agustina','Lucía','Emma','Florencia',
        'Antonella','Camila','Renata','Victoria','Zoe','Giuliana','Bianca',
        'Isabella','Abril','Milagros','Catalina','Morena','Pilar',
        'Santiago','Mateo','Nicolás','Facundo','Tomás','Julián','Lautaro',
        'Benjamín','Franco','Thiago','Máximo','Bruno','Leandro','Ezequiel',
        'Ignacio','Agustín','Ramiro','Iván','Federico','Sebastián',
    ],
    'CHI': [
        'Camila','Javiera','Constanza','Valentina','Isidora','Catalina',
        'Fernanda','Florencia','Rocío','Macarena','Antonia','Daniela',
        'Bárbara','Francisca','Carla','Paula','Sofía','Renata',
        'Diego','Sebastián','Matías','Ignacio','Felipe','Bastián',
        'Gonzalo','Nicolás','Andrés','Tomás','Cristóbal','Rodrigo',
        'Pablo','Joaquín','Vicente','Benjamín','Maximiliano','Patricio',
    ],
    'BRA': [
        'Ana','Julia','Larissa','Fernanda','Beatriz','Isabela','Amanda',
        'Gabriela','Leticia','Rafaela','Camila','Carolina','Juliana',
        'Mariana','Natalia','Lívia','Bianca','Vanessa','Priscila','Renata',
        'Lucas','Gabriel','Matheus','Guilherme','Rafael','João','Pedro',
        'Bruno','Leonardo','Thiago','Vinícius','Felipe','Henrique',
        'Eduardo','Ricardo','André','Daniel','Leandro','Rodrigo','Diego',
    ],
    'MEX': [
        'Fernanda','Valentina','Mariana','Daniela','Karla','Paola','Sofía',
        'Isabella','Ximena','Regina','Camila','Andrea','Alejandra',
        'Valeria','Natalia','Montserrat','Itzel','Brenda','Estefanía','Cecilia',
        'Diego','Miguel','Jorge','Andrés','Javier','Rodrigo','Alejandro',
        'Carlos','Eduardo','José','Emilio','Iván','Luis','Héctor',
        'Arturo','Óscar','Mauricio','Gerardo','Francisco','Manuel',
    ],
}

LAST_NAMES = {
    'ARG': [
        # Españoles/nativos
        'García','Rodríguez','González','Fernández','López','Martínez',
        'Pérez','Sánchez','Romero','Torres','Díaz','Herrera','Castro',
        'Morales','Reyes','Gutiérrez','Vargas','Ramos','Ríos','Medina',
        # Italianos (muy comunes en Argentina)
        'Rossi','Ferrari','Romano','Colombo','Bianchi','Ricci','Di Marco',
        'Esposito','Bruno','Mancini','Pellegrini','Gatti','Bassi','Conti',
        'Russo','De Luca','Lombardi','Gallo','Costa','Greco',
        # Alemanes / centroeuropeos
        'Müller','Weber','Hoffmann','Kramer','Fischer','Schulz',
        # Otros europeos
        'Dupont','Laurent','Moreau','Ivanov','Novak',
    ],
    'CHI': [
        # Españoles/nativos
        'González','Muñoz','Rojas','Díaz','Pérez','Soto','Contreras',
        'Silva','Martínez','Flores','Álvarez','Castro','Reyes','Fuentes',
        'Herrera','Morales','Espinoza','Vega','Cortés','Jiménez',
        'Núñez','Pizarro','Valenzuela','Tapia','Acevedo','Miranda',
        'Sepúlveda','Ríos','Araya','Ibáñez',
        # Alemanes (fuerte inmigración al sur de Chile)
        'Müller','Fischer','Hoffmann','Schneider','Becker','Braun',
        'Koch','Wagner','Richter','Klein',
        # Otros europeos / árabes
        'Dupont','Farah','Hatem','Nasser',
    ],
    'BRA': [
        # Portugueses/nativos
        'Silva','Santos','Oliveira','Souza','Rodrigues','Ferreira',
        'Alves','Pereira','Lima','Gomes','Ribeiro','Carvalho','Araújo',
        'Nascimento','Costa','Barbosa','Pinto','Cardoso','Mendes','Moreira',
        'Cavalcanti','Ramos','Correia','Teixeira','Nunes','Machado',
        # Italianos (muy comunes en São Paulo / Sul)
        'Rossi','Ferrari','Bianchi','Romano','Conti','Greco',
        'Lombardi','Russo','De Luca','Ricci',
        # Alemanes (muy comunes en RS, SC, PR)
        'Müller','Fischer','Schneider','Hoffmann','Becker','Braun',
        'Koch','Wagner','Richter','Klein',
        # Japoneses (mayor comunidad fuera de Japón está en São Paulo)
        'Nakamura','Yamamoto','Suzuki','Tanaka','Watanabe',
        # Árabes (Líbano / Siria)
        'Nasser','Farah','Haddad',
    ],
    'MEX': [
        # Españoles/nativos
        'García','Martínez','Hernández','López','González','Pérez',
        'Sánchez','Ramírez','Torres','Flores','Morales','Reyes','Cruz',
        'Vargas','Castillo','Romero','Gutiérrez','Díaz','Jiménez','Ortega',
        'Medina','Chávez','Mendoza','Ramos','Herrera','Ruiz','Vázquez',
        'Navarro','Salinas','Delgado',
        # Árabes (comunidad libanesa/siria muy presente en México)
        'Nasser','Farah','Haddad','Hatem','Kuri','Harb',
        # Europeos varios
        'Weber','Hoffmann','Dupont','Moreau',
        # Asiáticos (comunidad china en Baja California, Sonora, etc.)
        'Wong','Chan','Lee',
    ],
}

# ── Directorio de salida ───────────────────────────────────────
OUTPUT_DIR = 'dw/output_data'
