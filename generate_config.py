"""Genera claves nuevas sin mostrarlas por pantalla ni reemplazar archivos."""
import os
import secrets
from cryptography.fernet import Fernet

fd = os.open('.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write('APP_ENV=production\n')
    f.write('SECRET_KEY=' + secrets.token_hex(32) + '\n')
    f.write('DOCUMENT_KEY=' + Fernet.generate_key().decode() + '\n')
print('Se creó .env. Guardalo en un lugar privado; no lo subas a GitHub.')
