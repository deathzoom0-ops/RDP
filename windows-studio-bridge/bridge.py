"""Bounded Github Actions bridge; serve behind HTTPS, one WSGI worker per instance."""
import hmac
import io
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
import time
import zipfile

import requests
from flask import Flask, abort, jsonify, request

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2048
REPO = os.getenv('GITHUB_REPO', 'deathzoom0-ops/RDP')
WORKFLOW = 'bloodyray-windows.yml'
API = f'https://api.github.com/repos/{REPO}/actions'
@contextmanager
def database():
    conn = sqlite3.connect(os.getenv('BRIDGE_DB', 'jobs.sqlite3'), timeout=10)
    try:
        with conn:
            conn.execute('CREATE TABLE IF NOT EXISTS jobs (ticket TEXT PRIMARY KEY, created REAL NOT NULL, preset TEXT NOT NULL, format TEXT, content TEXT)')
            yield conn
    finally:
        conn.close()


def api(method, path, **kwargs):
    return requests.request(method, API + path, headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}, timeout=12, **kwargs)


@app.before_request
def authorize():
    if request.path == "/healthz" and request.method == "GET":
        return
    key = os.environ.get('STUDIO_BRIDGE_KEY', '')
    if len(key) < 32 or not hmac.compare_digest(request.headers.get('Authorization', ''), 'Bearer ' + key):
        abort(401)


@app.get('/healthz')
def health():
    return jsonify(status='ok')


@app.post('/jobs')
def start():
    body = request.get_json(silent=True)
    preset = body.get('preset') if isinstance(body, dict) else None
    if preset not in ('torre', 'arco', 'blender-chanfro'):
        abort(400)
    ticket = secrets.token_hex(16)
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        now = time.time()
        db.execute('DELETE FROM jobs WHERE created < ?', (now - 900,))
        active = db.execute('SELECT COUNT(*) FROM jobs WHERE content IS NULL').fetchone()[0]
        if active >= 8:
            return jsonify(error='Fila temporariamente cheia.'), 429
        if db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] >= 32:
            return jsonify(error='Limite de pedidos por janela atingido.'), 429
        db.execute('INSERT INTO jobs(ticket, created, preset) VALUES(?, ?, ?)', (ticket, now, preset))
    try:
        res = api('POST', f'/workflows/{WORKFLOW}/dispatches', json={'ref': 'main', 'inputs': {'ticket': ticket, 'preset': preset}})
        if not res.ok:
            raise ValueError('dispatch refused')
    except (requests.RequestException, ValueError):
        with database() as db:
            db.execute("DELETE FROM jobs WHERE ticket=?", (ticket,))
        return jsonify(error='GitHub recusou ou não confirmou o disparo.'), 502
    return jsonify(ticket=ticket, status='queued')


@app.get('/jobs/<ticket>')
def status(ticket):
    if not re.fullmatch('[a-f0-9]{32}', ticket):
        abort(404)
    with database() as db:
        job = db.execute("SELECT created, preset, format, content FROM jobs WHERE ticket=?", (ticket,)).fetchone()
    if not job or time.time()-job[0] > 900:
        abort(404)
    if job[3] is not None:
        return jsonify(status="ready", format=job[2], content=job[3])
    try:
        res = api('GET', f'/workflows/{WORKFLOW}/runs', params={'event': 'workflow_dispatch', 'per_page': 50})
        res.raise_for_status()
        run = next((r for r in res.json()['workflow_runs'] if r['display_title'] == 'BloodyRay ' + ticket and r['head_branch'] == 'main'), None)
        if not run or run['status'] != 'completed':
            return jsonify(status='running' if run and run['status'] == 'in_progress' else 'queued')
        if run['conclusion'] != 'success':
            return jsonify(status='failed', error='O job Windows não terminou com sucesso.')
        res = api('GET', f"/runs/{int(run['id'])}/artifacts")
        res.raise_for_status()
        artifact = next(a for a in res.json()['artifacts'] if a['name'] == 'bloodyray-result' and not a['expired'])
        if artifact['size_in_bytes'] > 100_000:
            raise ValueError('artifact too large')
        with api('GET', f"/artifacts/{int(artifact['id'])}/zip", stream=True) as res:
            res.raise_for_status()
            data = res.raw.read(100_001, decode_content=True)
            if len(data) > 100_000:
                raise ValueError('archive too large')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            kind = 'obj' if job[1] == 'blender-chanfro' else 'rbxmx'
            entry = archive.getinfo('result.' + kind)
            if entry.file_size > 32000:
                raise ValueError('file too large')
            content = archive.read(entry).decode('utf-8-sig')
        with database() as db:
            db.execute("UPDATE jobs SET format=?, content=? WHERE ticket=?", (kind, content, ticket))
        return jsonify(status='ready', format=kind, content=content)
    except (requests.RequestException, KeyError, ValueError, StopIteration, zipfile.BadZipFile):
        return jsonify(error='Não foi possível consultar ou ler a entrega do GitHub.'), 502
