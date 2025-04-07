import os
import socket
import requests

ZONE_NAME = os.environ["ZONE_NAME"]
RECORD_NAME = os.environ["RECORD_NAME"]
IP_PIHOLE = os.environ["IP_PIHOLE"]
IP_BACKUP = os.environ["IP_BACKUP"]
API_TOKEN = os.environ["CF_API_TOKEN"]

def pihole_respondendo():
    try:
        socket.setdefaulttimeout(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((IP_PIHOLE, 53))
        s.close()
        return True
    except:
        return False

def get_zone_id():
    r = requests.get("https://api.cloudflare.com/client/v4/zones", headers={
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }, params={"name": ZONE_NAME})

    response = r.json()
    if not response.get("success"):
        print("Erro ao obter zone_id:", response)
        return None

    return response["result"][0]["id"]

def get_record_id(zone_id):
    r = requests.get(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records", headers={
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }, params={"type": "A", "name": RECORD_NAME})

    response = r.json()
    if not response.get("success"):
        print("Erro ao obter registro DNS:", response)
        return None

    return response["result"][0]

def atualizar_dns(zone_id, record, novo_ip):
    r = requests.put(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "type": "A",
            "name": RECORD_NAME,
            "content": novo_ip,
            "ttl": 60,
            "proxied": record["proxied"]
        }
    )
    print("DNS atualizado:", r.json())

if __name__ == "__main__":
    zone_id = get_zone_id()
    if not zone_id:
        exit(1)

    record = get_record_id(zone_id)
    if not record:
        exit(1)

    ip_atual = record["content"]

    if pihole_respondendo():
        print("Pi-hole está online ✅")
        if ip_atual != IP_PIHOLE:
            print("Revertendo para IP do Pi-hole...")
            atualizar_dns(zone_id, record, IP_PIHOLE)
    else:
        print("Pi-hole fora do ar ❌")
        if ip_atual != IP_BACKUP:
            print("Redirecionando para IP de fallback...")
            atualizar_dns(zone_id, record, IP_BACKUP)
