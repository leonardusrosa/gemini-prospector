#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Troca fácil de usuário e senha do dashboard de produção (Phoenix VPS + local).

Uso:
  python change_dashboard_password.py <nova_senha>
  python change_dashboard_password.py <novo_usuario> <nova_senha>
"""

import sys
import subprocess
import winreg
import urllib.request
import base64

def main():
    if len(sys.argv) == 2:
        user = 'admin'
        password = sys.argv[1].strip()
    elif len(sys.argv) == 3:
        user = sys.argv[1].strip()
        password = sys.argv[2].strip()
    else:
        print("Uso:")
        print("  python change_dashboard_password.py <nova_senha>")
        print("  python change_dashboard_password.py <novo_usuario> <nova_senha>")
        sys.exit(1)

    if len(password) < 6:
        print("Erro: A senha deve ter no mínimo 6 caracteres.")
        sys.exit(1)

    print(f"1. Atualizando credenciais no servidor Phoenix (usuário: {user})...")
    # Ler arquivo atual no Phoenix
    p_read = subprocess.run(['ssh', 'phoenix', 'sudo cat /etc/prospector-dashboard.env'],
                            capture_output=True, text=True, check=True)
    lines = p_read.stdout.splitlines()

    new_lines = []
    user_found = False
    pass_found = False
    for l in lines:
        if l.startswith('PROSPECTOR_AUTH_USER='):
            new_lines.append(f'PROSPECTOR_AUTH_USER={user}')
            user_found = True
        elif l.startswith('PROSPECTOR_AUTH_PASSWORD='):
            new_lines.append(f'PROSPECTOR_AUTH_PASSWORD={password}')
            pass_found = True
        else:
            new_lines.append(l)

    if not user_found:
        new_lines.append(f'PROSPECTOR_AUTH_USER={user}')
    if not pass_found:
        new_lines.append(f'PROSPECTOR_AUTH_PASSWORD={password}')

    env_content = '\n'.join(new_lines) + '\n'

    # Gravar e reiniciar serviço
    subprocess.run(['ssh', 'phoenix', 'cat > /tmp/dash.env'], input=env_content.encode('utf-8'), check=True)
    subprocess.run(['ssh', 'phoenix', 'sudo mv /tmp/dash.env /etc/prospector-dashboard.env && sudo chmod 600 /etc/prospector-dashboard.env'], check=True)
    subprocess.run(['ssh', 'phoenix', 'sudo systemctl restart prospector-dashboard.service'], check=True)
    print("   -> Servidor atualizado e serviço reiniciado.")

    print("2. Atualizando credenciais no ambiente Windows local...")
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, 'PROSPECTOR_AUTH_USER', 0, winreg.REG_SZ, user)
    winreg.SetValueEx(key, 'PROSPECTOR_AUTH_PASSWORD', 0, winreg.REG_SZ, password)
    winreg.CloseKey(key)
    print("   -> Registro do Windows atualizado.")

    print("3. Testando autenticação em produção...")
    auth = base64.b64encode(f"{user}:{password}".encode('utf-8')).decode('ascii')
    req = urllib.request.Request('https://prospector.autocora.com.br/api/leads', headers={'Authorization': f'Basic {auth}'})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 200:
                print("\nSUCESSO! Credenciais alteradas e verificadas ao vivo em https://prospector.autocora.com.br/")
                print(f"Novo usuário: {user}")
    except Exception as e:
        print(f"\nAviso: Erro ao validar nova credencial: {e}")

if __name__ == '__main__':
    main()
