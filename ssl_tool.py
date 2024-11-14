#!/usr/bin/env python3

import argparse
import subprocess
import sys
import requests
import json
import pandas as pd
from tabulate import tabulate

def print_banner():
    print("""
       
                          ,--,                                                                 ,----,                ,----,                             ,--,           
                       ,---.'|               ,----..                               ,--.      ,/   .`|              ,/   .`|  ,----..       ,----..   ,---.'|           
  .--.--.    .--.--.   |   | :              /   /   \   .--.--.      ,---,       ,--.'|    ,`   .'  :            ,`   .'  : /   /   \     /   /   \  |   | :           
 /  /    '. /  /    '. :   : |             /   .     : /  /    '. ,`--.' |   ,--,:  : |  ;    ;     /          ;    ;     //   .     :   /   .     : :   : |           
|  :  /`. /|  :  /`. / |   ' :            .   /   ;.  \  :  /`. / |   :  :,`--.'`|  ' :.'___,/    ,'         .'___,/    ,'.   /   ;.  \ .   /   ;.  \|   ' :           
;  |  |--` ;  |  |--`  ;   ; '           .   ;   /  ` ;  |  |--`  :   |  '|   :  :  | ||    :     |          |    :     |.   ;   /  ` ;.   ;   /  ` ;;   ; '           
|  :  ;_   |  :  ;_    '   | |__         ;   |  ; \ ; |  :  ;_    |   :  |:   |   \ | :;    |.';  ;          ;    |.';  ;;   |  ; \ ; |;   |  ; \ ; |'   | |__         
 \  \    `. \  \    `. |   | :.'|        |   :  | ; | '\  \    `. '   '  ;|   : '  '; |`----'  |  |          `----'  |  ||   :  | ; | '|   :  | ; | '|   | :.'|        
  `----.   \ `----.   \'   :    ;        .   |  ' ' ' : `----.   \|   |  |'   ' ;.    ;    '   :  ;              '   :  ;.   |  ' ' ' :.   |  ' ' ' :'   :    ;        
  __ \  \  | __ \  \  ||   |  ./         '   ;  \; /  | __ \  \  |'   :  ;|   | | \   |    |   |  '              |   |  ''   ;  \; /  |'   ;  \; /  ||   |  ./         
 /  /`--'  //  /`--'  /;   : ;            \   \  ',  / /  /`--'  /|   |  ''   : |  ; .'    '   :  |              '   :  | \   \  ',  /  \   \  ',  / ;   : ;           
'--'.     /'--'.     / |   ,/              ;   :    / '--'.     / '   :  ||   | '`--'      ;   |.'               ;   |.'   ;   :    /    ;   :    /  |   ,/            
  `--'---'   `--'---'  '---'                \   \ .'    `--'---'  ;   |.' '   : |          '---'                 '---'      \   \ .'      \   \ .'   '---'             
                                             `---`                '---'   ;   |.'                                            `---`         `---`                       
         ,----,                 ,----,   ,----..                          '---'                                                                                        
       .'   .`|   ,---,       .'   .`|  /   /   \                                                                                                                      
    .'   .'   ;,`--.' |    .'   .'   ; /   .     :          ,--,                                                                                                       
  ,---, '    .'|   :  :  ,---, '    .'.   /   ;.  \       ,'_ /|                                                                                                       
  |   :     ./ :   |  '  |   :     ./.   ;   /  ` ;  .--. |  | :                                                                                                       
  ;   | .'  /  |   :  |  ;   | .'  / ;   |  ; \ ; |,'_ /| :  . |                                                                                                       
  `---' /  ;   '   '  ;  `---' /  ;  |   :  | ; | '|  ' | |  . .                                                                                                       
    /  ;  /    |   |  |    /  ;  /   .   |  ' ' ' :|  | ' |  | |                                                                                                       
   ;  /  /--,  '   :  ;   ;  /  /--, '   ;  \; /  |:  | | :  ' ;                                                                                                       
  /  /  / .`|  |   |  '  /  /  / .`|  \   \  ',  / |  ; ' |  | '                                                                                                       
./__;       :  '   :  |./__;       :   ;   :    /  :  | : ;  ; |                                                                                                       
|   :     .'   ;   |.' |   :     .'     \   \ .'   '  :  `--'   \                                                                                                      
;   |  .'      '---'   ;   |  .'         `---`     :  ,      .-./                                                                                                      
`---'                  `---'                        `--`----'                                                                                                          
                                                                                                                                                                       
""")

def check_jq():
    try:
        subprocess.run(["jq", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("jq not found, installing...")
        if subprocess.run(["command", "-v", "apt-get"], stdout=subprocess.PIPE).returncode == 0:
            subprocess.run(["sudo", "apt-get", "install", "-y", "jq"])
        elif subprocess.run(["command", "-v", "yum"], stdout=subprocess.PIPE).returncode == 0:
            subprocess.run(["sudo", "yum", "install", "-y", "jq"])
        elif subprocess.run(["command", "-v", "dnf"], stdout=subprocess.PIPE).returncode == 0:
            subprocess.run(["sudo", "dnf", "install", "-y", "jq"])
        elif subprocess.run(["command", "-v", "brew"], stdout=subprocess.PIPE).returncode == 0:
            subprocess.run(["brew", "install", "jq"])
        else:
            print("Error: jq is not found and cannot be installed on this system. Please manually install jq and rerun the script.")
            sys.exit(1)

def fetch_certificates(url, duplicates):
    print(f"Checking {url} at crt.sh\n")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0'
    }
    response = requests.get(f"https://crt.sh/?q={url}&output=json&exclude=expired", headers=headers)
    if response.status_code == 200:
        certificates = response.json()
        return certificates
    else:
        print("Error fetching data from crt.sh")
        sys.exit(1)

def fetch_status_code(domain):
    try:
        response = requests.head(f"https://{domain}", timeout=5)
        return response.status_code
    except requests.RequestException:
        return None

def display_certificates(certificates, duplicates):
    data = []
    for cert in certificates:
        domain = cert["common_name"]
        status_code = fetch_status_code(domain)
        data.append((domain, cert["issuer_ca_id"], cert["not_before"], cert["not_after"], status_code))
    df = pd.DataFrame(data, columns=["common_name", "issuer_ca_id", "not_before", "not_after", "status_code"])
    if not duplicates:
        df = df.drop_duplicates(subset="common_name")
    print(tabulate(df, headers="keys", tablefmt="grid"))

def main():
    parser = argparse.ArgumentParser(description="Check SSL certificates from crt.sh")
    parser.add_argument("-u", "--url", help="URL to check at crt.sh", required=True)
    parser.add_argument("-d", "--duplicates", help="Show duplicated records (true/false)", default="false", choices=["true", "false"])
    
    args = parser.parse_args()
    url = args.url
    duplicates = args.duplicates.lower() == "true"
    
    print_banner()
    check_jq()
    certificates = fetch_certificates(url, duplicates)
    display_certificates(certificates, duplicates)

if __name__ == "__main__":
    main()
