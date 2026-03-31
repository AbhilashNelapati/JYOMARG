from services.chat_service import handle_ask_abhi

print("--- Testing Phase 1 Hybrid AI Router ---")
print("Attempting to route the chat question logically...\n")

try:
    result = handle_ask_abhi("How do I learn Python fast?")
    print("SUCCESS! JSON Output Received:\n")
    print(result)
except Exception as e:
    print(f"FAILED: {e}")
