import requests

BASE_URL = "http://localhost:8000/api/v1"

print("\n--- 1. OBTENIENDO JWT PARA movil1 ---")
resp = requests.post(f"{BASE_URL}/auth/login/", json={
    "username": "movil1",
    "password": "movil123"
})
if resp.status_code != 200:
    print(f"Error Login ({resp.status_code}): {resp.text}")
    exit(1)

tokens = resp.json()
access_token = tokens['access']
print(f"✅ Login OK! Access Token: {access_token[:20]}...")

headers = {"Authorization": f"Bearer {access_token}"}

print("\n--- 3. CONSULTANDO MIS MAQUINAS (/mis-maquinas/) ---")
resp_maq = requests.get(f"{BASE_URL}/mis-maquinas/", headers=headers)
print(f"Status: {resp_maq.status_code}")
maquinas = resp_maq.json()
print(f"Data: {maquinas}")
maquina_id = maquinas[0]['id'] if maquinas else None

if maquina_id:
    print("\n--- 4. ENVIANDO CHECKLIST DIARIO VALIDO ---")
    data_checklist = {
        "maquina": maquina_id,
        "niveles_ok": True,
        "luces_ok": True,
        "estructura_ok": True, # DEBE SER TRUE PARA DEJAR ABRIR OT
        "comentarios": "Revisión OK. Listo para salir."
    }
    resp_chk = requests.post(f"{BASE_URL}/checklists/", headers=headers, json=data_checklist)
    print(f"Status: {resp_chk.status_code}")
    print(f"Data: {resp_chk.json()}")
    
    print("\n--- 5. CREANDO ORDEN DE TRABAJO ---")
    data_ot = {
        "maquina": maquina_id,
        "medida_salida": 5000,
        "nro_guia_despacho": "GUIA-101"
    }
    resp_ot = requests.post(f"{BASE_URL}/ordenes/", headers=headers, json=data_ot)
    print(f"Status: {resp_ot.status_code}")
    try:
        ot_data = resp_ot.json()
        print(f"Data: {ot_data}")
    except:
        ot_data = {}
        print(f"Body: {resp_ot.text}")
    
    print("\n--- 6. CERRANDO LA ORDEN DE TRABAJO ---")
    if 'id' in ot_data:
        ot_id = ot_data['id']
        data_cierre = {
            "medida_entrada": 5012
        }
        resp_cierre = requests.patch(f"{BASE_URL}/ordenes/{ot_id}/cerrar/", headers=headers, json=data_cierre)
        print(f"Status: {resp_cierre.status_code}")
        try:
            print(f"Data: {resp_cierre.json()}")
        except:
            print(f"Body: {resp_cierre.text}")

print("\n--- PRUEBAS COMPLETADAS ---")
