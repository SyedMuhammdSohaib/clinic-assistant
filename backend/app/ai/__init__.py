"""AI features. Safety rules that hold everywhere in this package:

1. AI never decides anything medical. Red flags come from the doctor's rules; answers
   come only from the doctor's approved list; medicines need the doctor's approval.
2. Whatever AI reads from a parent is shown back to the parent to confirm before it is saved.
3. Names, phone numbers and ID numbers are removed before text is sent to an AI service.
"""
