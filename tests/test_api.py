import requests
import time


BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    print(f"Health check: {data}")


def test_full_flow():
    """Test complete risk profiling flow"""
    
    # 1. Start session
    print("\n" + "="*50)
    print("1. Starting session...")
    print("="*50)
    response = requests.post(f"{BASE_URL}/api/session/start")
    data = response.json()
    client_id = data["client_id"]
    print(f"✓ Session started: {client_id}")
    print(f"\nAgent: {data['message']}\n")
    
    # 2. Simulate conversation
    questions = [
        "I'm 28 years old",
        "I'm planning to invest for 30 years",
        "I'm comfortable with high risk for higher returns",
        "My goal is wealth building",
        "I make about $120,000 per year",
        "I have around $50,000 in existing investments"
    ]
    
    for i, user_msg in enumerate(questions, 1):
        print("-" * 50)
        print(f"\n{i}. User: {user_msg}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat/{client_id}",
            json={"role": "user", "content": user_msg}
        )
        
        data = response.json()
        print(f"Agent: {data['message']}\n")
        
        if data.get("profile_complete"):
            print("="*50)
            print("✓ PROFILE COMPLETED!")
            print("="*50)
            print(f"Risk Score: {data['profile_data']['risk_score']}/100")
            print(f"Category: {data['profile_data']['risk_category']}")
            print(f"Allocation: {data['profile_data']['allocation']}")
            print(f"PDF Report: {BASE_URL}{data['pdf_url']}")
            print("="*50)
            break
        
        time.sleep(2)  # Be nice to the LLM


if __name__ == "__main__":
    print("\n🚀 Starting API Tests...")
    print("Make sure FastAPI server is running:")
    print("  uv run uvicorn wealth_risk_profiler.main:app --reload\n")
    
    try:
        test_health_check()
        test_full_flow()
        print("\n✅ All tests passed!")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API")
        print("Please start the server first:")
        print("  uv run uvicorn wealth_risk_profiler.main:app --reload")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")