python cpolar-tunnel/scripts/cpolar_ssh_public_url.py
python cpolar-tunnel/scripts/dynamic_proxy_script.py (python cpolar-tunnel/scripts/cpolar_ssh_public_url.py | Select-String tcp).Line.Trim() 2001
python cpolar-tunnel/scripts/twin_dynamic_proxy_script.py (python cpolar-tunnel/scripts/cpolar_ssh_public_url.py | Select-String tcp).Line.Trim()
python cpolar-tunnel/scripts/port_forward_script.py (python cpolar-tunnel/scripts/cpolar_ssh_public_url.py | Select-String tcp).Line.Trim() 33895:172.63.132.33:3389
netstat -ano|findstr "20808 20809"