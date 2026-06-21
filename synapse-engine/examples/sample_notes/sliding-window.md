# Algorithm Patterns

Sliding Window: a technique that maintains a moving range (window) over a sequence
and updates an aggregate as the window expands or contracts, solving many
substring and subarray problems in O(n) time.

Hash Map — a data structure mapping keys to values with average O(1) insertion and
lookup, often used to remember characters or counts already seen.

Two Pointers: a pattern using two indices that move through a sequence to avoid a
nested loop, common in sorted-array and partition problems.

Big-O notation describes how an algorithm's running time or space grows as the
input size grows; O(n) means linear growth.

For "longest substring without repeating characters", the optimal approach is a
sliding window plus a hash map of last-seen indices, giving O(n) time and O(1)
space over a fixed alphabet.
