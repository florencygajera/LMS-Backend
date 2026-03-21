import requests
import json
import time

BASE_URL = 'http://localhost:8001'

def main():
    print("==================================================")
    print("🔒 1. Generating Secure Connection to Agniveer API...")
    login_data = {'username': 'admin', 'password': 'admin123'}
    try:
        auth_resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=login_data)
        auth_resp.raise_for_status()
        token = auth_resp.json()['access_token']
    except Exception as e:
        print(f"❌ Login Handshake Failed: {e}")
        return
        
    print("\n✅ Secure JWT Access Token Acquired.")
    print("==================================================")
    print("🤖 Live Chat Activated. Type 'exit' to quit.\n")

    while True:
        user_input = input("\n📝 Ask AgniAssist: ")
        if user_input.strip().lower() in ['exit', 'quit']:
            print("Session closed.")
            break
            
        if not user_input.strip():
            continue

        payload = {
            "query": user_input,
            "user_id": 1
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        
        start_time = time.time()
        print("⏳ AI Engine Generating...")
        
        try:
            req = requests.post(f"{BASE_URL}/agniassist/ask", json=payload, headers=headers)
            req.raise_for_status()
            
            data = req.json()
            execution_time = round(time.time() - start_time, 2)
            
            print(f"\n🚀 Output ({execution_time}s):")
            print("--------------------------------------------------")
            print(data['answer'])
            print("--------------------------------------------------")
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Local AI Generation Pipeline Error: {e}")
            if hasattr(req, 'text'):
                print(f"DUMP: {req.text}")
            
if __name__ == "__main__":
    main()
