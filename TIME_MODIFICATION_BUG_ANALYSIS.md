# 🐛 Time Modification Bug Analysis

## 🔴 **Critical Issue Found**

### **Problem:** `modify_reservation_time()` function has syntax errors and unreachable code

---

## 🔍 **Current Code Analysis**

### **File:** `api/google_calendar.py` Lines 284-435

```python
def modify_reservation_time(self, client_name: str, new_date: str, new_time: str) -> bool:
    """Update the start/end time for the client's upcoming reservation."""
    event = self._find_upcoming_event_by_client(client_name)
    if not event:
        return False

    # Infer service name from summary like "[予約] カット - Name (Staff)"
    summary = event.get('summary', '')
    inferred_service = None
    try:
        # Extract the part between "[予約] " and " -"
        if summary.startswith("[予約]") and ' -' in summary:
            inferred_service = summary.replace("[予約] ", "", 1).split(" -", 1)[0].strip()
    except Exception:
        pass

    duration_minutes = self._get_service_duration_minutes(inferred_service or "")

    try:
        start_dt = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()

        event['start'] = {
            'dateTime': start_iso,
            'timeZone': self.timezone,
        }
        event['end'] = {
            'dateTime': end_iso,
            'timeZone': self.timezone,
        }

        updated = self.service.events().update(
            calendarId=self.calendar_id,
            eventId=event['id'],
            body=event
        ).execute()

        print(f"Modified reservation time for {client_name}: {updated.get('htmlLink')}")
        return True
    except Exception as e:
        print(f"Failed to modify reservation time: {e}")
        return False  # ← LINE 331: FUNCTION ENDS HERE!
    
    try:  # ← LINE 333: UNREACHABLE CODE!
        # Parse date and time
        date_str = reservation_data['date']  # ← reservation_data is not defined!
        service = reservation_data['service']
        staff = reservation_data['staff']
        
        # ... 100+ lines of code from create_reservation_event() ...
```

---

## ❌ **What's Wrong?**

### **Issue #1: Unreachable Code After Return Statement**

**Line 331:** `return False` - Function ends here
**Line 333:** `try:` - This code is **NEVER EXECUTED** because it comes after a return statement

**Result:** The function always returns `False` and never performs the actual modification!

### **Issue #2: Wrong Function Logic**

The function is trying to:
1. Find event by client name (❌ Wrong - should use reservation ID)
2. Infer service from summary (❌ Unnecessary - we have the service data)
3. Calculate duration from inferred service (❌ Wrong - we have the actual service)

### **Issue #3: Copied Code from Wrong Function**

Lines 333-435 contain code from `create_reservation_event()` that was accidentally copied into `modify_reservation_time()`. This code:
- References `reservation_data` (not defined in this function)
- Creates new events instead of modifying existing ones
- Is unreachable anyway due to the return statement

---

## 🔍 **Root Cause Analysis**

### **Why Time Modification Fails:**

1. **Function Always Returns False:**
   ```python
   # Line 1393-1397 in reservation_flow.py
   calendar_success = self.google_calendar.modify_reservation_time(
       reservation["client_name"], 
       selected_date,
       start_time
   )
   
   if not calendar_success:  # ← This is ALWAYS True!
       return "申し訳ございません。カレンダーの更新に失敗しました。"
   ```

2. **Wrong Event Selection:**
   ```python
   # Line 290 in google_calendar.py
   event = self._find_upcoming_event_by_client(client_name)
   ```
   - Finds **any upcoming event** by client name
   - If user has multiple reservations, modifies the **WRONG ONE**

3. **No Actual Calendar Update:**
   - The function returns `False` before reaching the update logic
   - Calendar events are never actually modified

---

## ✅ **The Solution**

### **Option 1: Fix the Current Function (Quick Fix)**

Remove the unreachable code and fix the logic:

```python
def modify_reservation_time(self, client_name: str, new_date: str, new_time: str) -> bool:
    """Update the start/end time for the client's upcoming reservation."""
    event = self._find_upcoming_event_by_client(client_name)
    if not event:
        return False

    # Infer service name from summary like "[予約] カット - Name (Staff)"
    summary = event.get('summary', '')
    inferred_service = None
    try:
        # Extract the part between "[予約] " and " -"
        if summary.startswith("[予約]") and ' -' in summary:
            inferred_service = summary.replace("[予約] ", "", 1).split(" -", 1)[0].strip()
    except Exception:
        pass

    duration_minutes = self._get_service_duration_minutes(inferred_service or "")

    try:
        start_dt = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()

        event['start'] = {
            'dateTime': start_iso,
            'timeZone': self.timezone,
        }
        event['end'] = {
            'dateTime': end_iso,
            'timeZone': self.timezone,
        }

        updated = self.service.events().update(
            calendarId=self.calendar_id,
            eventId=event['id'],
            body=event
        ).execute()

        print(f"Modified reservation time for {client_name}: {updated.get('htmlLink')}")
        return True
    except Exception as e:
        print(f"Failed to modify reservation time: {e}")
        return False

    # REMOVE ALL CODE FROM LINE 333 ONWARDS - IT'S UNREACHABLE!
```

### **Option 2: Create Proper Function (Recommended)**

Create `modify_reservation_by_id()` that uses reservation ID instead of client name:

```python
def modify_reservation_by_id(
    self, 
    reservation_id: str, 
    new_date: str = None,
    new_start_time: str = None,
    new_end_time: str = None
) -> bool:
    """Modify a reservation by its ID"""
    try:
        # Find the event by reservation ID
        event = self.get_reservation_by_id(reservation_id)
        
        if not event:
            print(f"Reservation {reservation_id} not found")
            return False
        
        # Extract current event details
        current_start = event.get('start', {}).get('dateTime', '')
        
        if current_start:
            start_dt = datetime.fromisoformat(current_start)
        else:
            print(f"No start time found for reservation {reservation_id}")
            return False
        
        # Apply modifications
        if new_date:
            new_date_obj = datetime.strptime(new_date, "%Y-%m-%d")
            start_dt = start_dt.replace(
                year=new_date_obj.year,
                month=new_date_obj.month,
                day=new_date_obj.day
            )
        
        if new_start_time:
            time_obj = datetime.strptime(new_start_time, "%H:%M")
            start_dt = start_dt.replace(hour=time_obj.hour, minute=time_obj.minute)
        
        # Calculate end time (keep same duration)
        if current_end:
            current_end_dt = datetime.fromisoformat(current_end)
            duration = current_end_dt - datetime.fromisoformat(current_start)
            end_dt = start_dt + duration
        else:
            end_dt = start_dt + timedelta(minutes=60)
        
        # Update the event
        event['start'] = {
            'dateTime': start_dt.isoformat(),
            'timeZone': self.timezone
        }
        event['end'] = {
            'dateTime': end_dt.isoformat(),
            'timeZone': self.timezone
        }
        
        updated_event = self.service.events().update(
            calendarId=self.calendar_id,
            eventId=event['id'],
            body=event
        ).execute()
        
        print(f"Successfully modified reservation {reservation_id}")
        return True
        
    except Exception as e:
        print(f"Failed to modify reservation {reservation_id}: {e}")
        return False
```

---

## 📊 **Impact Summary**

| Issue | Current Behavior | After Fix |
|-------|------------------|-----------|
| **Function Logic** | Always returns False | ✅ Returns True on success |
| **Event Selection** | Wrong event (by client name) | ✅ Correct event (by ID) |
| **Calendar Update** | Never happens | ✅ Actually updates calendar |
| **Multiple Reservations** | Modifies wrong one | ✅ Modifies correct one |

---

## 🎯 **Recommended Action**

**Option 2 (Create `modify_reservation_by_id()`)** is recommended because:

1. ✅ **Reliability:** Always modifies the correct reservation
2. ✅ **Accuracy:** Uses reservation ID instead of client name
3. ✅ **Future-proof:** Works with multiple reservations
4. ✅ **Clean:** No unreachable code or syntax errors

**Priority:** 🔴 **CRITICAL** - Fix immediately

---

## 🚀 **Next Steps**

1. **Remove unreachable code** from `modify_reservation_time()` (lines 333-435)
2. **Create `modify_reservation_by_id()`** function
3. **Update `_process_time_modification()`** to use the new function
4. **Test time modification** on real LINE account

**Expected Result:** Time modification will actually update the Google Calendar event! 🎉
