import urllib.request
import json

try:
    print('Intentando iniciar sesión...')
    data = json.dumps({'username': 'admin', 'password': 'admin123'}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8000/api/v1/auth/login/', data=data, headers={'Content-Type': 'application/json'})
    res = urllib.request.urlopen(req)
    response_data = json.loads(res.read())
    
    token = response_data.get('access')
    print('LOGIN EXITOSO. Token Obtenido:', token[:30] + '...')
    
    print('\nConsultando Maquinarias autorizadas...')
    req_maq = urllib.request.Request('http://localhost:8000/api/v1/maquinarias/', headers={'Authorization': 'Bearer ' + token})
    res_maq = urllib.request.urlopen(req_maq)
    
    print('MAQUINARIAS DE LA EMPRESA:')
    print(json.dumps(json.loads(res_maq.read()), indent=2))

except Exception as e:
    print('Error:', e)
