# Cotizador de texturado

Página web para que el cliente calcule el precio de **colocación de texturado (mano de obra, base incluida)** y te mande el pedido por WhatsApp al **11 3765-4777**.

Es un solo archivo: `index.html`. No necesita servidor, base de datos ni instalar nada. Funciona en el celular y en la computadora.

## Qué hace

- El cliente carga los **m²** (o los calcula con largo × alto de cada pared).
- Elige la **altura de trabajo**:
  - Hasta 4 m: **$5.000/m²**
  - Hasta 5 m: **$6.000/m²**
  - Hasta 6 m: **$7.000/m²**
  - Más de 6 m: **a convenir**
- Elige la **textura**: media (precio base) o fina (**+$1.000/m²**).
- Marca si es **interior, exterior o ambos**.
- Elige la **zona de la obra** (CABA, Zona Norte, Sur, Oeste u otra) y puede escribir el barrio.
- Puede **subir fotos** de la pared.
- Ve el total al instante y toca **Enviar pedido por WhatsApp**: se abre el chat con tu número y el mensaje ya escrito, así:

```
Hola! Quiero cotizar colocación de texturado (mano de obra con base incluida).

Nombre: Marcela
Zona: Zona Sur - Lanús
Lugar: Exterior
Superficie: 35,5 m²
Altura: hasta 5 m
Textura: fina
Precio por m²: $7.000
Total estimado: $248.500
Fotos: 2 (te las mando por acá)
```

### Sobre las fotos

WhatsApp no permite que un link mande fotos junto con el mensaje. Por eso:

- En el **celular** (Android/iPhone) aparece el botón **Enviar las fotos**: abre el menú de compartir, el cliente elige WhatsApp y tu chat.
- Si el navegador no lo permite, la página le indica que adjunte las fotos con el clip en el chat que se abrió.

Las fotos no se suben a ningún servidor: quedan en el teléfono del cliente hasta que te las manda.

## Cambiar precios, zonas o número

Abrí `index.html` con cualquier editor de texto y buscá `CONFIGURACIÓN` (está al principio del `<script>`, casi al final del archivo):

```js
whatsapp: '5491137654777',          // 54 + 9 + 11 + número
whatsappVisible: '11 3765-4777',
alturas: [
  { id: '4',   label: 'Hasta 4 m',  max: 4, precio: 5000 },
  { id: '5',   label: 'Hasta 5 m',  max: 5, precio: 6000 },
  { id: '6',   label: 'Hasta 6 m',  max: 6, precio: 7000 },
  { id: 'mas', label: 'Más de 6 m', max: Infinity, precio: null } // a convenir
],
texturas: [
  { id: 'media', label: 'Textura media', extra: 0 },
  { id: 'fina',  label: 'Textura fina',  extra: 1000 }
],
zonas: ['CABA', 'Zona Norte', 'Zona Sur', 'Zona Oeste', 'Otra'],
```

Cambiá los números, guardá y volvé a subir el archivo. Todos los textos de precios de la página se actualizan solos.

## Publicarla en Internet

Sirve cualquier hosting que acepte archivos HTML (a diferencia de Plaza Cerca, no necesita Python):

- **Hostinger / cPanel**: subí `index.html` a `public_html` (o a una carpeta, por ejemplo `public_html/cotizar/`).
- **GitHub Pages**, **Netlify** o **Cloudflare Pages**: gratis, arrastrando la carpeta `cotizador-texturado`.

Después compartí el link en tu estado de WhatsApp, Instagram o Marketplace.

Para probarla en la computadora, abrí `index.html` con doble clic.
