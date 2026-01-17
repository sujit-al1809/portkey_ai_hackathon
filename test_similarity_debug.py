#!/usr/bin/env python3
"""
Debug similarity calculation
"""

import sys
sys.path.insert(0, './backend')

from session_manager import chat_manager

print("=" * 80)
print("Testing Similarity Calculation")
print("=" * 80)

# Test various question pairs
test_pairs = [
    ("How do I optimize Python code?", "How can I make Python scripts faster?"),
    ("How do I optimize Python code?", "What is machine learning?"),
    ("optimize python", "optimize python"),
    ("optimize python", "make python faster"),
    ("How do I optimize Python code?", "How do I optimize Python?"),
]

for q1, q2 in test_pairs:
    score = chat_manager._calculate_similarity(q1, q2)
    print(f"\nQ1: '{q1}'")
    print(f"Q2: '{q2}'")
    print(f"Similarity: {score:.2f} ({score:.0%})")
    print(f"Cache hit at 0.50 threshold: {'✓ YES' if score >= 0.50 else '✗ NO'}")
    print(f"Cache hit at 0.30 threshold: {'✓ YES' if score >= 0.30 else '✗ NO'}")
