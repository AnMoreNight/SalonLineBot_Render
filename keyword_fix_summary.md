# Keyword Matching Fix for Reservation Modification

## Issue Found

User input "日時変更したい" (datetime change) was not being recognized in the modification flow, causing the bot to ask the same question again instead of proceeding to time modification.

### Screenshot Analysis:
```
User: "日時変更したい"
Bot: "何を変更しますか？以下のキーワードでお答えください:" (asked again)

User: (number works fine)
```

## Root Cause

The keyword "日時変更したい" was **NOT** in the `time_change` navigation keywords list.

### What Was in the Keywords:
- ✅ "時間変更したい" (time change)
- ✅ "時間を変更したい" (change the time)
- ❌ "日時変更したい" (datetime change) - **MISSING**

### Where "日時変更したい" Was:
- It was only in the `modify` intent keywords (for initial modification request)
- It was NOT in the `time_change` navigation keywords (for field selection)

## The Fix

Added "日時" (datetime) variations to the `time_change` keywords in `api/data/keywords.json`:

### Before:
```json
"time_change": [
  "時間変更したい",
  "時間を変更したい",
  "別の時間にしたい",
  "他の時間を選択したい"
]
```

### After:
```json
"time_change": [
  "時間変更したい",
  "時間を変更したい",
  "日時変更したい",      ← ADDED
  "日時を変更したい",    ← ADDED
  "別の時間にしたい",
  "他の時間を選択したい"
]
```

## Why This Happened

1. User is in `modify_select_field` step
2. User inputs "日時変更したい"
3. `_handle_field_selection()` checks keywords
4. "日時変更したい" is NOT in `time_change` keywords
5. Falls through to else block
6. Asks the same question again ❌

## What Now Works

### All Time Change Keywords:
- ✅ "時間変更したい" (time change)
- ✅ "時間を変更したい" (change the time)
- ✅ "日時変更したい" (datetime change) **← NOW WORKS**
- ✅ "日時を変更したい" (change the datetime) **← NOW WORKS**
- ✅ "別の時間にしたい" (want different time)
- ✅ "他の時間を選択したい" (want to select other time)

### How Matching Works:

```python
# Normalize and match case-insensitively
message_normalized = message.strip().lower()

if any(keyword.lower() in message_normalized for keyword in time_change_keywords):
    return self._handle_time_modification(user_id, message)
```

## Complete User Flow Now

### Using Number:
```
Bot: "何を変更しますか？"
User: "1"
Bot: Shows available time slots ✅
```

### Using Text Keyword (時間):
```
Bot: "何を変更しますか？"
User: "時間変更したい"
Bot: Shows available time slots ✅
```

### Using Text Keyword (日時):
```
Bot: "何を変更しますか？"
User: "日時変更したい"
Bot: Shows available time slots ✅ ← NOW FIXED
```

## Files Modified

1. **api/data/keywords.json**
   - Added "日時変更したい" to `time_change` keywords
   - Added "日時を変更したい" to `time_change` keywords

## Testing

### Test Cases:
1. ✅ Number input "1" → Works
2. ✅ "時間変更したい" → Works
3. ✅ "日時変更したい" → **NOW WORKS**
4. ✅ "日時を変更したい" → **NOW WORKS**
5. ✅ With whitespace " 日時変更したい " → Works (trimmed)
6. ✅ Case variations → Works (case-insensitive)

## Summary

The issue was simply that the keyword "日時変更したい" (which the user naturally uses) was missing from the `time_change` navigation keywords. Now both "時間" (time) and "日時" (datetime) variations are supported for time modification selection.

This is a natural language improvement - users think of "日時" (datetime) when they want to change the time of their reservation, so we need to support both "時間" and "日時" keywords.
