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
| `URL` | STRING | Link de afiliado que originó la venta |
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