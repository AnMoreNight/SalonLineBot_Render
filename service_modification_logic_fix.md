# Service Modification Logic Fix

## Issue

When a user wants to change the service in a reservation, the bot was comparing ONLY the current service duration with the new service duration, not checking if the new service can actually fit in the available time slots for that date.

## Previous Logic (Incorrect)

```python
# OLD - Only checked current duration vs new duration
current_duration = int(reservation["duration"])
if current_duration < new_duration:
    return "現在の時間では新しいサービスができません"
```

### Problems with Old Logic:

1. ❌ Only compared durations (60 min vs 90 min)
2. ❌ Didn't check actual calendar availability
3. ❌ Didn't ignore current reservation slot
4. ❌ Would reject valid service changes if current slot was shorter

### Example of Old Logic Failure:

**Scenario:**
- Current reservation: カット (60 min) at 10:00-11:00
- User wants to change to: カット+カラー (90 min)
- Available slots on that date: 11:00-13:00 (2 hours free)

**Old behavior:**
```
Bot: "現在の時間（60分）ではカット+カラー（90分）のサービスができません"
❌ WRONG - There IS a 90-min slot available at 11:00-13:00!
```

## New Logic (Correct)

```python
# NEW - Check if new service can fit in ANY available slot
available_slots = self.google_calendar.get_available_slots_for_service(
    reservation["date"], 
    new_service,
    reservation["reservation_id"]  # Exclude current reservation
)

if not available_slots:
    return "その日には新しいサービスが可能な時間がありません"
```

### Improvements with New Logic:

1. ✅ **Ignores current reservation** (via `exclude_reservation_id`)
2. ✅ **Checks actual calendar availability** for that date
3. ✅ **Considers new service duration** when finding slots
4. ✅ **Returns all available time slots** that can accommodate the new service

### Example of New Logic Success:

**Scenario:**
- Current reservation: カット (60 min) at 10:00-11:00
- User wants to change to: カット+カラー (90 min)
- Available slots on that date: 11:00-13:00 (2 hours free)

**New behavior:**
```
Bot: Checks calendar for 90-min slots (excluding 10:00-11:00)
Found: 11:00-13:00 (90 min available) ✅
Bot: "サービス変更が完了しました！"
✅ CORRECT - The service change is allowed!
```

## How It Works Now

### Step 1: User Selects New Service
```
User: "カット+カラー"
```

### Step 2: System Validates Service Exists
```python
if new_service not in self.services:
    return "そのサービスは提供しておりません"
```

### Step 3: System Checks Calendar Availability (NEW)
```python
# Get available slots that can accommodate the new service duration
available_slots = self.google_calendar.get_available_slots_for_service(
    reservation["date"],          # Same date as current reservation
    new_service,                  # New service name
    reservation["reservation_id"] # Exclude current reservation
)
```

### Step 4: Validate Availability
```python
if not available_slots:
    # No time slots available for this service duration
    return "その日には新しいサービスが可能な時間がありません"
else:
    # Available slots found, proceed with update
    # Updates calendar and sheets
    return "サービス変更が完了しました！"
```

## Technical Details

### `get_available_slots_for_service` Method

This method in `google_calendar.py`:
1. Gets all events for the date
2. Excludes the current reservation (via `reservation_id`)
3. Generates all possible time slots
4. Filters slots by service duration
5. Returns only slots that can accommodate the service

### Parameters:
- `date_str`: The date to check (e.g., "2025-10-16")
- `service_name`: The service to check duration for (e.g., "カット+カラー")
- `exclude_reservation_id`: Current reservation to ignore (e.g., "RES-20251016-4549")

### Returns:
```python
[
    {'time': '11:00', 'end_time': '12:30', 'duration': 90},
    {'time': '13:00', 'end_time': '14:30', 'duration': 90},
    # Only slots that can fit 90-min service
]
```

## Benefits

### Before:
- ❌ Rejected valid service changes
- ❌ Forced users to change time first
- ❌ Poor user experience
- ❌ Didn't consider actual calendar

### After:
- ✅ Allows service changes if ANY slot is available
- ✅ Ignores current reservation properly
- ✅ Better user experience
- ✅ Uses actual calendar availability
- ✅ More accurate validation

## Example Flows

### Flow 1: Service Change Possible
```
Current: カット (60 min) at 10:00-11:00
New: カット+カラー (90 min)
Available: 11:00-13:00 (free)

Result: ✅ Service change allowed
```

### Flow 2: Service Change Not Possible
```
Current: カット (60 min) at 10:00-11:00
New: パーマ (120 min)
Available: 11:00-12:00 (only 60 min free)

Result: ❌ Service change rejected
Message: "その日にはパーマ（120分）が可能な時間がありません"
```

### Flow 3: Same or Shorter Service
```
Current: カット+カラー (90 min) at 10:00-11:30
New: カット (60 min)

Result: ✅ Always allowed (shorter service)
```

## Error Messages

### Old Error Message:
```
申し訳ございませんが、現在の時間（60分）ではカット+カラー（90分）のサービスができません。

時間も変更する場合は、まず「時間変更したい」を選択してください。
```

### New Error Message:
```
申し訳ございませんが、2025-10-16にはカット+カラー（90分）が可能な時間がありません。

別の日付または別のサービスをご検討いただくか、スタッフまでお問い合わせください。
```

## Summary

The service modification logic now properly:
1. **Ignores the current reservation time slot**
2. **Checks actual calendar availability** for the new service
3. **Validates if new service duration can fit** in any available slot
4. **Provides accurate feedback** to users

This makes the service modification feature much more useful and accurate!
