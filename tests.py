import io
import re
import sqlite3
import time

import pytest
from PIL import Image
from werkzeug.security import generate_password_hash
from app import create_app


@pytest.fixture
def env(tmp_path):
    app = create_app({'TESTING': True, 'DATA_DIR': tmp_path})
    con = sqlite3.connect(tmp_path / 'marketplace.sqlite3')
    con.execute('INSERT INTO users(name,email,password,admin,created) VALUES (?,?,?,1,?)', ('Admin', 'admin@example.test', generate_password_hash('ClaveAdminSegura123'), int(time.time())))
    con.commit()
    yield app, tmp_path, con
    con.close()


def token(client, path='/login'):
    client.get(path)
    with client.session_transaction() as s:
        return s['csrf']


def post(client, path, data=None):
    payload = {'csrf': token(client)}
    payload.update(data or {})
    return client.post(path, data=payload, follow_redirects=False)


def register(client, email='persona@example.test'):
    return post(client, '/register', {'nombre': 'Persona Ejemplo', 'email': email, 'clave': 'ClaveDePrueba12345', 'adult': 'yes'})


def login_admin(client):
    return post(client, '/login', {'email': 'admin@example.test', 'clave': 'ClaveAdminSegura123'})


def picture():
    b = io.BytesIO()
    Image.new('RGB', (120, 120), '#1256af').save(b, 'PNG')
    b.seek(0)
    return b, 'prueba.png'


def submit(client):
    return post(client, '/verify', {'consent': 'yes', 'selfie': picture(), 'front': picture(), 'back': picture()})


def approve(admin, vid):
    return post(admin, f'/admin/review/{vid}', {'decision': 'approved', 'checked': 'yes'})


def test_registration_csrf_and_public_roles(env):
    app, root, con = env
    user = app.test_client()
    assert user.post('/register', data={'nombre':'x'}).status_code == 400
    assert register(user).status_code == 302
    assert con.execute('SELECT admin,verified FROM users WHERE email=?', ('persona@example.test',)).fetchone() == (0,0)
    assert user.get('/admin').status_code == 403
    assert user.get('/sell').status_code == 302
    assert 'Primero verific' in user.get('/account').get_data(as_text=True)


def test_identity_access_approval_and_encrypted_storage(env):
    app, root, con = env
    user, admin, anonymous = app.test_client(), app.test_client(), app.test_client()
    register(user)
    assert submit(user).status_code == 302
    vid = con.execute('SELECT id FROM verifications').fetchone()[0]
    files = list((root/'identity').iterdir())
    assert len(files) == 3
    assert all(p.read_bytes().startswith(b'gAAAA') for p in files)
    path = f'/admin/identity/{vid}/selfie'
    assert user.get(path).status_code == 403
    assert anonymous.get(path).status_code == 302
    login_admin(admin)
    assert admin.get('/admin').status_code == 200
    response = admin.get(path)
    assert response.status_code == 200
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.mimetype == 'image/jpeg'
    assert post(admin, f'/admin/review/{vid}', {'decision':'approved'}).status_code == 400
    assert approve(admin, vid).status_code == 302
    assert not list((root/'identity').iterdir())
    assert con.execute('SELECT verified FROM users WHERE email=?', ('persona@example.test',)).fetchone()[0] == 1
    assert admin.get(path).status_code == 404
    assert approve(admin, vid).status_code == 409
    assert user.get('/sell').status_code == 200


def test_rejection_retry_cancel_and_duplicate(env):
    app, root, con = env
    user, admin = app.test_client(), app.test_client()
    register(user)
    submit(user)
    submit(user)
    assert con.execute('SELECT count(*) FROM verifications').fetchone()[0] == 1
    assert len(list((root/'identity').iterdir())) == 3
    login_admin(admin)
    assert post(admin, '/admin/review/1', {'decision':'rejected','checked':'yes'}).status_code == 400
    assert post(admin, '/admin/review/1', {'decision':'rejected','checked':'yes','reason':'No es legible'}).status_code == 302
    assert not list((root/'identity').iterdir())
    assert 'No es legible' in user.get('/account').get_data(as_text=True)
    submit(user)
    assert post(user, '/verify/cancel').status_code == 302
    assert not list((root/'identity').iterdir())
    assert con.execute('SELECT verified FROM users WHERE email=?', ('persona@example.test',)).fetchone()[0] == 0


def test_expiration_blocks_reads_and_purges(env):
    app, root, con = env
    user, admin = app.test_client(), app.test_client()
    register(user)
    submit(user)
    con.execute('UPDATE verifications SET created=?', (int(time.time())-8*86400,))
    con.commit()
    login_admin(admin)
    assert admin.get('/admin/identity/1/front').status_code == 404
    assert approve(admin, 1).status_code == 409
    assert admin.get('/admin').status_code == 200
    assert not list((root/'identity').iterdir())
    assert con.execute('SELECT status FROM verifications').fetchone()[0] == 'expired'


def test_invalid_upload_does_not_leave_files(env):
    app, root, con = env
    user = app.test_client()
    register(user)
    post(user, '/verify', {'consent':'yes','selfie':picture(),'front':(io.BytesIO(b'<svg onload="alert(1)"></svg>'),'evil.jpg'),'back':picture()})
    assert con.execute('SELECT count(*) FROM verifications').fetchone()[0] == 0
    assert not list((root/'identity').iterdir())
    post(user, '/verify', {'selfie':picture(),'front':picture(),'back':picture()})
    assert not list((root/'identity').iterdir())


def publish(user, title='Taladro de prueba'):
    return post(user, '/sell', {'titulo':title,'descripcion':'Producto de prueba con todos sus accesorios.', 'precio':'12500.50','categoria':'Herramientas','zona':'González Catán','whatsapp':'5491112345678','public_contact':'yes','fotos':picture()})


def test_listing_complete_flow_and_owner_authorization(env):
    app, root, con = env
    user, admin, stranger = app.test_client(), app.test_client(), app.test_client()
    register(user)
    submit(user)
    login_admin(admin)
    approve(admin, 1)
    response = publish(user)
    assert response.status_code == 302
    detail = stranger.get(response.headers['Location']).get_data(as_text=True)
    assert 'wa.me/5491112345678' in detail
    assert '$ 12.500,50' in detail
    assert 'Taladro de prueba' in stranger.get('/?category=Herramientas').get_data(as_text=True)
    assert stranger.get('/photo/1').status_code == 200
    register(stranger, 'otro@example.test')
    assert post(stranger, '/listing/1/state', {'state':'sold'}).status_code == 403
    assert post(user, '/listing/1/state', {'state':'sold'}).status_code == 302
    assert stranger.get('/listing/1').status_code == 404
    assert stranger.get('/photo/1').status_code == 404
    assert 'Taladro de prueba' not in stranger.get('/').get_data(as_text=True)
    assert user.get('/listing/1').status_code == 200


def test_xss_escaped_and_account_delete(env):
    app, root, con = env
    user, admin = app.test_client(), app.test_client()
    register(user)
    submit(user)
    login_admin(admin)
    approve(admin, 1)
    publish(user, '<script>alert(1)</script>')
    html = user.get('/listing/1').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in html
    assert '&lt;script&gt;' in html
    assert post(user, '/account/delete', {'clave':'incorrecta'}).status_code == 400
    assert post(user, '/account/delete', {'clave':'ClaveDePrueba12345'}).status_code == 302
    assert con.execute('SELECT count(*) FROM listings').fetchone()[0] == 0
    assert not list((root/'public').iterdir())
    assert con.execute('SELECT count(*) FROM users WHERE admin=0').fetchone()[0] == 0


def test_failed_login_limited(env):
    app, root, con = env
    user = app.test_client()
    for _ in range(10):
        assert post(user, '/login', {'email':'x@example.test','clave':'incorrecta'}).status_code == 200
    assert post(user, '/login', {'email':'x@example.test','clave':'incorrecta'}).status_code == 429


def test_pages_and_admin_cli(env):
    app, root, con = env
    user = app.test_client()
    for path in ['/', '/privacy', '/register', '/login', '/static/style.css', '/static/favicon.svg']:
        assert user.get(path).status_code == 200
    assert user.get('/does-not-exist').status_code == 404
    result = app.test_cli_runner().invoke(args=['create-admin','--email','new@example.test','--name','Nuevo','--password','UnaClaveSegura12345'])
    assert result.exit_code == 0
    assert con.execute('SELECT admin,verified FROM users WHERE email="new@example.test"').fetchone() == (1,0)
