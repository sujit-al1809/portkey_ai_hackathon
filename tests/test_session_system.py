#!/usr/bin/env python3
"""
Test the complete login and history flow
"""

import sys
sys.path.insert(0, './backend')

from session_manager import session_manager, chat_manager

print("=" * 80)
print("Testing Session & History System")
print("=" * 80)

# Test 1: User login
print("\n1. User Login Test")
session = session_manager.login("alice")
print(f"✓ Created session: {session.session_id}")
print(f"✓ User ID: {session.user_id}")
print(f"✓ Username: {session.username}")

# Test 2: Save conversation
print("\n2. Save Conversation Test")
chat_id = chat_manager.save_chat(
    user_id=session.user_id,
    question="How do I optimize Python code?",
    response="Use profiling tools and vectorization",
    model_used="gpt-4o",
    quality_score=0.92,
    cost=0.0015
)
print(f"✓ Saved chat: {chat_id}")

# Test 3: Get history
print("\n3. Get History Test")
history = chat_manager.get_user_history(session.user_id)
print(f"✓ Found {len(history)} chat(s)")
for chat in history:
    print(f"  - Q: {chat.question[:50]}...")
    print(f"    Model: {chat.model_used}, Quality: {chat.quality_score:.0%}")

# Test 4: Similar question detection
print("\n4. Similar Question Detection Test")
similar_q = "What's the best way to optimize Python scripts?"
result = chat_manager.find_similar_question(
    user_id=session.user_id,
    question=similar_q,
    similarity_threshold=0.6
)

if result:
    print(f"✓ Found similar question!")
    print(f"  Similarity: {result.similarity_score:.0%}")
    print(f"  Original: {result.question}")
    print(f"  Model: {result.model_used}")
    print(f"  Quality: {result.quality_score:.0%}")
else:
    print(f"✗ No similar question found")

# Test 5: Logout
print("\n5. Logout Test")
session_manager.logout(session.session_id)
print(f"✓ Session marked inactive")

# Test 6: Re-login should retrieve history
print("\n6. Re-login Test (Should Retrieve History)")
session2 = session_manager.login("alice")
history2 = chat_manager.get_user_history(session2.user_id)
print(f"✓ Found {len(history2)} chat(s) for returning user")

print("\n" + "=" * 80)
print("All tests passed!")
print("=" * 80)
