import urllib.request, base64, json
req = urllib.request.Request('http://localhost:8000/api/scan')
creds = base64.b64encode(b'hemang:411057').decode()
req.add_header('Authorization', 'Basic ' + creds)
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    if 'stocks' in data and len(data['stocks']) > 0:
        s = data['stocks'][0]
        print('divergence' in s)
        print(s.get('divergence_count'))
    else:
        print('no')
except Exception as e:
    print(e)
