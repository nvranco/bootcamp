# Data Warehouse — Programa de Afiliados Mercado Libre

Hoja de consulta para los ejercicios del bootcamp.
Dataset sintético que simula el programa de afiliados de Mercado Libre en cuatro países.

---

## Contexto de negocio

Un **afiliado** es un creador de contenido que genera links únicos a productos del Marketplace.
Cada vez que un usuario hace clic en ese link y compra, el afiliado recibe una comisión.

El DW registra todo el ciclo:

```
Afiliado se registra → publica links → usuarios hacen clic → se generan ventas
```

---

## Universo de datos

| Dimensión | Valor |
|---|---|
| Fecha de corte | 2026-04-12 |
| Países | ARG · BRA · CHI · MEX |
| Monedas | ARS · BRL · CLP · MXN |
| Afiliados activos | ~36 000 |
| Links de afiliado | ~526 000 |
| Ventas registradas | ~17 500 |

---

## Diagrama de relaciones

```
DIM_AFFILIATES_MARKETPLACE_PRODUCTS
  │  MARKETPLACE_PRODUCT_ID
  │
  ├──────────────────────────────────────────────┐
  │                                              │
FACTS_MARKETPLACE_AFFILIATE_URLS          FACTS_AFFILIATES_MARKETPLACE_SALES
  │  URL (PK)           AFFILIATE_ID ──┐    URL · AFFILIATE_ID · MARKETPLACE_PRODUCT_ID
  │  MARKETPLACE_PRODUCT_ID            │    BUYER_MELI_USER_ID · PURCHASE_DATETIME
  │  CREATED_AT · CLOSED_AT            │    COUNTRY · CURRENCY · PRICE
  │                                    │
  │                              DIM_AFFILIATES
FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS   AFFILIATE_ID (PK)
  URL · MELI_USERNAME · ACCESS_DATETIME    MELI_USERNAME · MELI_USER_ID
                                           AFFILIATED_AT · COUNTRY · CATEGORY
                                           INSTAGRAM_HANDLE · INSTAGRAM_FOLLOWER_COUNT
                                           TIKTOK_HANDLE · TIKTOK_FOLLOWER_COUNT
                                                │
                                     FACTS_REGISTERED_SOCIAL_MEDIA
                                       SM_ID · AFFILIATE_ID
                                       SOCIAL_MEDIA · URL · FOLLOWERS
```

**Claves de join más usadas**

| Desde | Campo | Hacia |
|---|---|---|
| `FACTS_MARKETPLACE_AFFILIATE_URLS` | `AFFILIATE_ID` | `DIM_AFFILIATES` |
| `FACTS_MARKETPLACE_AFFILIATE_URLS` | `MARKETPLACE_PRODUCT_ID` | `DIM_AFFILIATES_MARKETPLACE_PRODUCTS` |
| `FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS` | `URL` | `FACTS_MARKETPLACE_AFFILIATE_URLS` |
| `FACTS_AFFILIATES_MARKETPLACE_SALES` | `URL` | `FACTS_MARKETPLACE_AFFILIATE_URLS` |
| `FACTS_AFFILIATES_MARKETPLACE_SALES` | `AFFILIATE_ID` | `DIM_AFFILIATES` |
| `FACTS_AFFILIATES_MARKETPLACE_SALES` | `MARKETPLACE_PRODUCT_ID` | `DIM_AFFILIATES_MARKETPLACE_PRODUCTS` |
| `FACTS_REGISTERED_SOCIAL_MEDIA` | `AFFILIATE_ID` | `DIM_AFFILIATES` |

---

## Tablas

### `DIM_AFFILIATES`
Dimensión maestra de afiliados. Una fila por afiliado.

| Columna | Tipo | Descripción |
|---|---|---|
| `AFFILIATE_ID` | INTEGER | Clave primaria |
| `MELI_USERNAME` | STRING | Username en Mercado Libre |
| `MELI_USER_ID` | INTEGER | ID numérico de usuario en MELI |
| `AFFILIATED_AT` | DATE | Fecha en que se incorporó al programa |
| `COUNTRY` | STRING | País (`ARG` · `BRA` · `CHI` · `MEX`) |
| `CATEGORY` | STRING | Nicho de contenido del afiliado |
| `INSTAGRAM_HANDLE` | STRING | Handle de Instagram (sin `@`), puede ser NULL |
| `INSTAGRAM_FOLLOWER_COUNT` | FLOAT | Seguidores en Instagram |
| `TIKTOK_HANDLE` | STRING | Handle de TikTok (sin `@`), puede ser NULL |
| `TIKTOK_FOLLOWER_COUNT` | FLOAT | Seguidores en TikTok |

**Valores posibles de `CATEGORY`:** `lifestyle` · `home_deco` · `fitness` · `travel` · `education` · `tech` · `beauty` · `food` · `other`

---

### `FACTS_REGISTERED_SOCIAL_MEDIA`
Todas las redes sociales declaradas por cada afiliado al registrarse. Un afiliado puede tener varias filas (una por plataforma).

| Columna | Tipo | Descripción |
|---|---|---|
| `SM_ID` | INTEGER | Clave primaria |
| `AFFILIATE_ID` | INTEGER | FK → `DIM_AFFILIATES` |
| `SOCIAL_MEDIA` | STRING | Plataforma |
| `URL` | STRING | URL del perfil |
| `FOLLOWERS` | INTEGER | Seguidores al momento del registro |

**Valores posibles de `SOCIAL_MEDIA`:** `instagram` · `tiktok` · `youtube` · `facebook` · `x` · `other`

> **Nota:** `DIM_AFFILIATES` solo guarda Instagram y TikTok (las principales).
> `FACTS_REGISTERED_SOCIAL_MEDIA` es la fuente completa de todas las plataformas.

---

### `FACTS_MARKETPLACE_AFFILIATE_URLS`
Cada link de afiliado generado. Un afiliado puede tener muchos links (uno por producto que promociona).

| Columna | Tipo | Descripción |
|---|---|---|
| `URL` | STRING | Clave primaria — link único de afiliado |
| `AFFILIATE_ID` | INTEGER | FK → `DIM_AFFILIATES` |
| `MARKETPLACE_PRODUCT_ID` | STRING | FK → `DIM_AFFILIATES_MARKETPLACE_PRODUCTS` |
| `CREATED_AT` | DATE | Fecha de creación del link |
| `CLOSED_AT` | DATE | Fecha en que se desactivó el link (NULL si sigue activo) |

> Un link con `CLOSED_AT IS NULL` está **activo**. Con fecha, está **cerrado**.

---

### `FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS`
Registro de cada clic recibido por un link de afiliado.

| Columna | Tipo | Descripción |
|---|---|---|
| `URL` | STRING | FK → `FACTS_MARKETPLACE_AFFILIATE_URLS` |
| `MELI_USERNAME` | STRING | Usuario de MELI que hizo el clic |
| `ACCESS_DATETIME` | DATETIME | Fecha y hora exacta del clic |

> Para saber de qué afiliado es el link: `JOIN FACTS_MARKETPLACE_AFFILIATE_URLS USING (URL)`.

---

### `FACTS_AFFILIATES_MARKETPLACE_SALES`
Compras completadas a través de un link de afiliado. Una fila por transacción.

| Columna | Tipo | Descripción |
|---|---|---|
| `URL` | STRING | FK → `FACTS_MARKETPLACE_AFFILIATE_URLS` |
| `AFFILIATE_ID` | INTEGER | FK → `DIM_AFFILIATES` |
| `BUYER_MELI_USER_ID` | INTEGER | ID del comprador en MELI |
| `MARKETPLACE_PRODUCT_ID` | STRING | FK → `DIM_AFFILIATES_MARKETPLACE_PRODUCTS` |
| `PURCHASE_DATETIME` | DATETIME | Fecha y hora de la compra |
| `COUNTRY` | STRING | País donde se realizó la compra |
| `CURRENCY` | STRING | Moneda local (`ARS` · `BRL` · `CLP` · `MXN`) |
| `PRICE` | FLOAT | Precio en moneda local |

> Los precios están en **moneda local**, no en USD. Para comparar entre países hay que convertir.

---

### `DIM_AFFILIATES_MARKETPLACE_PRODUCTS`
Catálogo de productos del Marketplace referenciados por los links de afiliado.

| Columna | Tipo | Descripción |
|---|---|---|
| `MARKETPLACE_PRODUCT_ID` | STRING | Clave primaria (ej. `MLA-1234567`) |
| `SELLER_MELI_USER_ID` | INTEGER | ID del vendedor en MELI |
| `TITLE` | STRING | Título del producto |
| `CATEGORY_AGG_1` | STRING | Categoría nivel 1 (ej. `Electrónica`) |
| `CATEGORY_AGG_2` | STRING | Categoría nivel 2 (ej. `Celulares y Teléfonos`) |
| `CATEGORY_AGG_3` | STRING | Categoría nivel 3 (ej. `Smartphones`) |
| `CONDITION` | STRING | Estado del producto (`new` · `used`) |
| `VISIBLE` | BOOLEAN | Si el producto está publicado actualmente |
| `AVAILABLE_UNITS` | INTEGER | Stock disponible |
| `PUBLICATION_DATETIME` | DATE | Fecha de publicación original |
| `CALIFICATION` | FLOAT | Calificación promedio (1.0 – 5.0) |
| `OPINIONS` | INTEGER | Cantidad de opiniones recibidas |

**Categorías nivel 1:** `Electrónica` · `Ropa y Moda` · `Hogar y Deco` · `Deportes` · `Belleza y Salud` · `Alimentos` · `Juguetes y Bebés`

---

## Consultas de referencia

```sql
-- Ventas totales por afiliado (en moneda local)
SELECT
    a.AFFILIATE_ID,
    a.MELI_USERNAME,
    a.COUNTRY,
    COUNT(*)        AS ventas,
    SUM(s.PRICE)    AS ingresos
FROM DW.FACTS_AFFILIATES_MARKETPLACE_SALES s
JOIN DW.DIM_AFFILIATES a USING (AFFILIATE_ID)
GROUP BY 1, 2, 3
ORDER BY ventas DESC;


-- Tasa de conversión por link (clics → compras)
SELECT
    u.URL,
    u.AFFILIATE_ID,
    COUNT(DISTINCT a.ACCESS_DATETIME)   AS clics,
    COUNT(DISTINCT s.PURCHASE_DATETIME) AS ventas,
    SAFE_DIVIDE(
        COUNT(DISTINCT s.PURCHASE_DATETIME),
        COUNT(DISTINCT a.ACCESS_DATETIME)
    ) AS conversion_rate
FROM DW.FACTS_MARKETPLACE_AFFILIATE_URLS u
LEFT JOIN DW.FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS a USING (URL)
LEFT JOIN DW.FACTS_AFFILIATES_MARKETPLACE_SALES       s USING (URL)
GROUP BY 1, 2;


-- Top productos por cantidad de links de afiliado activos
SELECT
    p.TITLE,
    p.CATEGORY_AGG_1,
    COUNT(*) AS links_activos
FROM DW.FACTS_MARKETPLACE_AFFILIATE_URLS u
JOIN DW.DIM_AFFILIATES_MARKETPLACE_PRODUCTS p USING (MARKETPLACE_PRODUCT_ID)
WHERE u.CLOSED_AT IS NULL
GROUP BY 1, 2
ORDER BY links_activos DESC
LIMIT 20;


-- Afiliados con redes sociales registradas (todas las plataformas)
SELECT
    a.MELI_USERNAME,
    a.COUNTRY,
    sm.SOCIAL_MEDIA,
    sm.FOLLOWERS
FROM DW.DIM_AFFILIATES a
JOIN DW.FACTS_REGISTERED_SOCIAL_MEDIA sm USING (AFFILIATE_ID)
ORDER BY sm.FOLLOWERS DESC;
```
