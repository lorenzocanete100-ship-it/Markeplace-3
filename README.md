# Plaza Cerca — primera versión para hosting propio

Aplicación web para celular y computadora. Código fuente completo, independiente de ChatGPT y sin servicios pagos obligatorios. El nombre es provisional y se puede cambiar.

## Incluye

- Registro e ingreso con correo y contraseña.
- Catálogo, búsqueda por título o localidad, categorías y paginación.
- Publicaciones con 1–4 fotos, descripción, precio en pesos, localidad y contacto por WhatsApp.
- Selfie, frente y dorso del documento para revisión manual.
- Panel privado para aprobar/rechazar solicitudes y retirar publicaciones.
- Solo las cuentas aprobadas pueden publicar; la aprobación muestra la insignia de identidad revisada.
- Marcar vendido, retirar publicación y eliminar la propia cuenta.
- Base de datos SQLite persistente y archivos en disco persistente.

## Estado de entrega

La aplicación está preparada para ejecutarse y fue probada localmente. **Todavía no está publicada en Internet ni conectada a un dominio.** No contiene usuarios, documentos, productos reales ni contraseñas iniciales. Es una app web: no es un APK ni una aplicación publicada en Play Store.

Esta primera versión no incluye pagos, envíos, chat interno, recuperación de contraseña por correo, confirmación del correo electrónico, edición de publicaciones ni verificación automática contra registros oficiales. El contacto comercial se hace por WhatsApp. La insignia significa revisión visual manual, no certificación de autenticidad.

## Probar en una computadora

Requiere Python 3.12 o superior. Descomprimí el ZIP y abrí una terminal dentro de la carpeta `plaza-cerca`.

```sh
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```sh
source .venv/bin/activate
```

```sh
python -m pip install -r requirements.txt
python -m flask --app app:create_app create-admin
python -m flask --app app:create_app run --host 127.0.0.1 --port 8000
```

Abrí `http://127.0.0.1:8000`. Ingresá con el administrador que acabás de crear. No existe una clave predeterminada. No expongas el servidor de desarrollo en Internet. Usá imágenes de prueba al probar la aplicación.

Para probar como comprador/vendedor, creá una cuenta normal en otra ventana o cerrá la sesión del administrador. El administrador no se considera automáticamente verificado para vender.

## Flujo de revisión

1. El usuario crea su cuenta, confirma ser mayor de 18 años y autoriza la revisión de imágenes.
2. Envía selfie, frente y dorso. Su estado queda Pendiente.
3. Entrás en `/admin`, comparás las imágenes con el nombre registrado y abrís cada foto para inspeccionarla. No descargues ni copies documentos fuera del sistema.
4. Confirmás la revisión y aprobás o rechazás. El rechazo requiere un motivo. La aplicación elimina las tres imágenes y conserva el resultado.
5. El usuario ve el resultado en Mi cuenta. Si fue aprobado, puede vender. Si fue rechazado, puede enviar una nueva solicitud.

Si una solicitud no se revisa durante 7 días, deja de ser accesible. Las fotos se eliminan al abrir la gestión de solicitudes o al ejecutar el mantenimiento programado. El usuario también puede retirar la solicitud antes de su revisión.

## Elegir hosting más adelante

Necesita un servidor que ejecute **Python/Gunicorn o Docker**, HTTPS y almacenamiento persistente. Un hosting que solo permita subir HTML o PHP no alcanza. No requiere un proveedor específico. SQLite está pensada aquí para una primera comunidad, en una única instancia con disco local persistente; no se debe usar la misma base sobre almacenamiento de red ni desplegar múltiples réplicas independientes.

El administrador del hosting deberá:

1. Configurar dominio y HTTPS mediante un proxy inverso.
2. Generar `.env` privado con `python generate_config.py` y cargar esas variables en el servicio. **El archivo no se carga automáticamente al ejecutar Flask**; Docker `--env-file` sí lo carga. Nunca subirlo a GitHub.
3. Configurar `APP_ENV=production`, `SECRET_KEY` y `DOCUMENT_KEY`. La app rechaza iniciar en producción sin claves. Las cookies requieren HTTPS en ese modo.
4. Montar un volumen persistente para `DATA_DIR`. Sus claves de cifrado deben conservarse por separado y no rotarse sin un plan de migración.
5. Crear tu administrador desde la consola del servidor. El registro público no puede asignar administradores.
6. Programar `flask --app app:create_app purge-documents` cada hora con las mismas variables del servicio.
7. Identificar al responsable del servicio e incorporar un canal de contacto y las condiciones de privacidad definitivas antes de admitir documentos reales. El texto incluido explica el funcionamiento; no certifica cumplimiento legal.
8. Configurar respaldo de base y fotos públicas. **Excluir `identity/` de respaldos y snapshots**, para que no sobrevivan copias de documentos eliminados. Si el proveedor hace snapshots de todo el disco, separar `identity/` en un montaje que no se respalde. Fijar un plazo de retención de respaldos de cuentas y publicaciones y explicarlo en la política final.

### Ejemplo con Docker

```sh
python generate_config.py
docker build -t plaza-cerca .
docker run -d --name plaza-cerca --restart unless-stopped --env-file .env -p 127.0.0.1:8000:8000 -v plaza-cerca-data:/app/data plaza-cerca
docker exec -it plaza-cerca flask --app app:create_app create-admin
```

El puerto queda accesible solo desde el servidor. Configurá el proxy HTTPS para enviar tráfico a `127.0.0.1:8000`. No uses cookies de producción sobre HTTP. Ejemplo de configuración para Caddy (instalado en el servidor):

```caddy
tu-dominio.example {
    request_body {
        max_size 26MB
    }
    reverse_proxy 127.0.0.1:8000
}
```

Ejemplo de tarea horaria en el servidor:

```cron
0 * * * * docker exec plaza-cerca flask --app app:create_app purge-documents
```

Los límites por IP no confían en cabeceras reenviadas. Detrás de un proxy pueden agrupar visitantes; existe además un límite por correo o usuario. El operador deberá ajustar la configuración a su proxy de confianza si crece el tráfico, sin confiar indiscriminadamente en `X-Forwarded-For`.

## Datos y controles implementados

- Documentos cifrados con Fernet y fuera de la carpeta pública. Se descifran únicamente en rutas que validan el rol administrador en el servidor; las respuestas no se almacenan en caché.
- Contraseñas con hash scrypt de Werkzeug. Cookies HttpOnly/SameSite, CSRF, límites de intentos persistentes, consultas parametrizadas y escape de HTML.
- Fotos redecodificadas, metadatos EXIF eliminados y nombres aleatorios. Límites de tipo, tamaño, cantidad y resolución.
- Sin contraseñas predeterminadas, rol administrador por consola, registro de accesos a documentos y decisiones.
- Eliminación de cuenta con contraseña; documentos borrados al decidir, retirar o vencer.

Esto no sustituye una revisión de seguridad de producción. Antes de abrir el sitio con documentos reales, verificá HTTPS, permisos de disco, administración de claves, respaldos y la tarea de eliminación en el hosting elegido.

## Comprobaciones

```sh
python -m pip install pytest
python -m pytest -q tests.py
```

Resultado de esta entrega: 9 pruebas aprobadas. La comprobación visual en navegador no pudo completarse en el entorno de creación; revisar las pantallas en celular y computadora al instalar.

Las pruebas usan una base temporal y fotos sintéticas: registro, sesiones, CSRF, control de acceso a documentos, rechazo/aprobación, publicación, contacto, retiro, eliminación de cuenta y vencimiento.

## Archivos principales

- `app.py`: lógica, base de datos, controles de acceso y consola.
- `templates/`: pantallas en español.
- `static/`: diseño y favicon.
- `wsgi.py`, `Dockerfile`, `requirements.txt`: ejecución en servidor.
- `generate_config.py`: generación de claves privadas.
- `tests.py`: pruebas automatizadas.

Se entrega todo el código de la aplicación. Las bibliotecas de terceros conservan sus propias licencias. Para cambiar el nombre, buscá `Plaza Cerca` y `plazacerca` en las plantillas.
