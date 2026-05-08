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

## Tablas

| Tabla | Descripción |
|---|---|
| [`DIM_AFFILIATES`](#dim_affiliates) | Dimensión maestra de afiliados — una fila por afiliado |
| [`DIM_AFFILIATES_MARKETPLACE_PRODUCTS`](#dim_affiliates_marketplace_products) | Catálogo de productos del Marketplace |
| [`FACTS_AFFILIATES_MARKETPLACE_SALES`](#facts_affiliates_marketplace_sales) | Transacciones completadas a través de links de afiliado |
| [`FACTS_AFFILIATES_MARKETPLACE_ACCESS_LOGS`](#facts_affiliates_marketplace_access_logs) | Log de clics en links de afiliado |
| [`FACTS_MARKETPLACE_AFFILIATE_URLS`](#facts_marketplace_affiliate_urls) | Links de afiliado generados |
| [`FACTS_REGISTERED_SOCIAL_MEDIA`](#facts_registered_social_media) | Redes sociales declaradas al registrarse |
| [`FACTS_JIRA_HUNTING_AFILIADOS`](#facts_jira_hunting_afiliados) | Pipeline de prospección de nuevos afiliados (Jira) |

---

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

**Valores posibles de `CATEGORY`:** `lifestyle` · `beauty` · `fitness` · `tech` · `food` · `travel` · `home_deco` · `education` · `other`

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

### `FACTS_JIRA_HUNTING_AFILIADOS`
Pipeline de prospección de nuevos afiliados. Una fila por prospecto gestionado en Jira.

| Columna | Tipo | Descripción |
|---|---|---|
| `JIRA_KEY` | STRING | Clave del ticket en Jira |
| `MELI_USERNAME` | STRING | Username en MELI del lead (NULL si no tiene cuenta) |
| `HUNTER` | STRING | Nombre del hunter asignado |
| `NOMBRE` | STRING | Nombre del prospecto |
| `FECHA_ASIGNACION` | DATE | Fecha en que se asignó el lead al hunter |
| `ULTIMO_CONTACTO` | DATE | Fecha del último contacto con el lead |
| `INSTAGRAM` | STRING | Handle de Instagram del lead |
| `TIKTOK` | STRING | Handle de TikTok del lead |
| `ESTADO` | STRING | Estado en el funnel (`pool` · `asignado` · `contactado` · `afiliado` · `rechazado`) |
| `ASIGNADO` | BOOLEAN | TRUE si el lead fue asignado a un hunter |
| `CONTACTADO` | BOOLEAN | TRUE si el hunter contactó al lead al menos una vez |
| `AFILIADO` | BOOLEAN | TRUE si el lead se convirtió en afiliado |
| `RECHAZADO` | BOOLEAN | TRUE si el lead fue rechazado |