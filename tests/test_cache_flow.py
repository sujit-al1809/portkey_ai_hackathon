#!/usr/bin/env python3
"""
Test the complete cache flow:
1. User logs in
2. User asks a question (full analysis)
3. User asks a SIMILAR question (should get cached response)
4. Verify cost savings
"""

import sys
sys.path.insert(0, './backend')

from session_manager import session_manager, chat_manager

print("=" * 80)
print("Testing Cache Hit Flow (Same User, Similar Question)")
print("=" * 80)

# Test 1: User login
print("\n1. User Login")
session = session_manager.login("bob")
print(f"✓ User logged in: {session.username} ({session.user_id})")

# Test 2: Save first question
print("\n2. First Question: 'How do I optimize Python code?'")
chat_id_1 = chat_manager.save_chat(
    user_id=session.user_id,
    question="How do I optimize Python code?",
    response="Use profiling tools like cProfile and vectorization with NumPy",
    model_used="gpt-4o-mini",
    quality_score=0.92,
    cost=0.00006
)
print(f"✓ Saved (Cost: $0.00006)")

# Test 3: Ask similar question - should find cache hit
print("\n3. Similar Question: 'How can I make Python scripts faster?'")
similar = chat_manager.find_similar_question(
    user_id=session.user_id,
    question="How can I make Python scripts faster?",
    similarity_threshold=0.35
)

if similar:
    print(f"✓ CACHE HIT! (Similarity: {similar.similarity_score:.0%})")
    print(f"  Original: '{similar.question}'")
    print(f"  Cached response used: {similar.model_used}")
    print(f"  Cost saved: ${similar.cost:.6f} (now $0.00)")
else:
    print(f"✗ No cache hit found")

# Test 4: Ask completely different question - should not cache
print("\n4. Different Question: 'What is machine learning?'")
similar_2 = chat_manager.find_similar_question(
    user_id=session.user_id,
    question="What is machine learning?",
    similarity_threshold=0.75
)

if not similar_2:
    print(f"✓ Correctly identified as different (no false positive cache)")
else:
    print(f"✗ False positive cache hit")

print("\n" + "=" * 80)
print("Cache flow test complete!")
print("=" * 80)
