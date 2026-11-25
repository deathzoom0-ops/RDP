import io
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
import bridge

class Response:
    ok = True
    def __init__(self, data=None, blob=b''):
        self.data = data
        self.raw = self
        self.blob = blob
    def read(self, *args, **kwargs): return self.blob
    def json(self): return self.data
    def raise_for_status(self): pass
    def __enter__(self): return self
    def __exit__(self, *exc): pass

key = 's' * 32
headers = {'Authorization': 'Bearer ' + key}
archive = io.BytesIO()
with zipfile.ZipFile(archive, 'w') as z:
    z.writestr('result.rbxmx', '<roblox/>')
client = bridge.app.test_client()
with TemporaryDirectory() as tmp, patch.dict('os.environ', {'STUDIO_BRIDGE_KEY':key, 'BRIDGE_DB':str(Path(tmp) / 'jobs.sqlite3')}), patch.object(bridge, 'api') as api:
    assert client.get('/healthz').json == {'status':'ok'}
    assert client.post('/jobs', json={'preset':'torre'}).status_code == 401
    assert client.post('/jobs', json={'preset':'powershell'}, headers=headers).status_code == 400
    api.return_value = Response()
    r = client.post('/jobs', json={'preset':'torre'}, headers=headers)
    assert r.status_code == 200
    ticket = r.json['ticket']
    run = {'display_title':'BloodyRay '+ticket,'head_branch':'main','id':3,'status':'completed','conclusion':'success'}
    api.side_effect = [Response({'workflow_runs':[run]}), Response({'artifacts':[{'name':'bloodyray-result','expired':False,'size_in_bytes':120,'id':9}]}), Response(blob=archive.getvalue())]
    assert client.get('/jobs/'+ticket, headers=headers).json == {'status':'ready','format':'rbxmx','content':'<roblox/>'}
    assert client.get('/jobs/'+ticket, headers=headers).json['status'] == 'ready'
    assert api.call_count == 4
    assert client.get('/jobs/'+'0'*32, headers=headers).status_code == 404
print('Bridge mock round trip: PASS')
