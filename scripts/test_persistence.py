import sys
import os
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))

from src.bot.state import PersistentState

def test_persistence():
    test_file = "data/processed/test_bot_state.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        
    print("🚀 Initializing test state...")
    state = PersistentState(test_file)
    
    # 1. Add data
    print("📥 Adding test preview...")
    test_uuid = "test-uuid-123"
    test_data = {"topic": "NASA finds water on Mars", "caption": "Breaking news!"}
    state.update_child("previews", test_uuid, test_data)
    
    # 2. Re-initialize
    print("🔄 Simulating bot restart (re-loading state from file)...")
    new_state = PersistentState(test_file)
    
    # 3. Verify
    loaded_data = new_state.get("previews", {}).get(test_uuid)
    if loaded_data == test_data:
        print("✅ Success! State survived restart.")
    else:
        print(f"❌ Failed! Expected {test_data}, got {loaded_data}")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    test_persistence()
