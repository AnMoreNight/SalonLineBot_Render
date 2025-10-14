# 🌏 Timezone Analysis: Asia/Tokyo (UTC+9) in Full Project

## 📋 Summary

- **Configured Timezone:** `Asia/Tokyo` (UTC+9)
- **Library Used:** `pytz`
- **Configuration:** Environment variable `GOOGLE_CALENDAR_TIMEZONE` (defaults to "Asia/Tokyo")

---

## 🔍 Detailed Analysis

### **1. Timezone Configuration**

**File:** `api/google_calendar.py`  
**Line 20:**
```python
self.timezone = os.getenv("GOOGLE_CALENDAR_TIMEZONE", "Asia/Tokyo")
```

**Analysis:**
- ✅ Timezone is configurable via environment variable
- ✅ Defaults to "Asia/Tokyo" (UTC+9)
- ✅ Used throughout the Google Calendar Helper

---

### **2. Timezone Usage Patterns**

#### **Pattern 1: Creating Events with Timezone**

**Locations:** Lines 169-173, 314-318, 388-392

```python
event = {
    'start': {
        'dateTime': start_iso,  # e.g., "2025-10-16T13:00:00"
        'timeZone': self.timezone,  # "Asia/Tokyo"
    },
    'end': {
        'dateTime': end_iso,
        'timeZone': self.timezone,  # "Asia/Tokyo"
    },
}
```

**Analysis:**
- ✅ Correctly sets timezone for event start/end
- ✅ Google Calendar API will interpret times as Asia/Tokyo
- ❌ **ISSUE:** `start_iso` and `end_iso` are created from naive datetime objects (no timezone info)

**Example:**
```python
# Line 143-145
start_datetime = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
# Result: datetime(2025, 10, 16, 13, 0, 0) ← NO TIMEZONE INFO (naive)

start_iso = start_datetime.isoformat()
# Result: "2025-10-16T13:00:00" ← No timezone in string
```

**Verdict:** ✅ **Works** because timezone is specified separately in the event object

---

#### **Pattern 2: Querying Events (UTC+Z Format)**

**Locations:** Lines 218-219, 258, 460-461, 596-597, 733

```python
events_result = self.service.events().list(
    calendarId=self.calendar_id,
    timeMin=start_date.isoformat() + 'Z',  # ← Adding 'Z' means UTC!
    timeMax=end_date.isoformat() + 'Z',    # ← UTC!
    ...
)
```

**Analysis:**
- ❌ **MAJOR ISSUE:** Appending 'Z' means the time is interpreted as UTC
- ❌ If `start_date = "2025-10-16T00:00:00"`, adding 'Z' makes it `2025-10-16T00:00:00Z` (UTC)
- ❌ In Asia/Tokyo (UTC+9), this is actually `2025-10-16T09:00:00+09:00` local time
- ❌ **Missing 9 hours of events!**

**Example Problem:**
```python
# Line 592, 596-597 in get_events_for_date
start_date = datetime.strptime("2025-10-16", "%Y-%m-%d")
# Result: datetime(2025, 10, 16, 0, 0, 0) ← No timezone

timeMin = start_date.isoformat() + 'Z'
# Result: "2025-10-16T00:00:00Z" ← This is UTC 00:00
# In Tokyo time, this is: 2025-10-16 09:00+09:00
# So we MISS events from 00:00 to 09:00 Tokyo time!
```

**Verdict:** ❌ **CRITICAL BUG** - Missing events due to timezone mismatch

---

#### **Pattern 3: Using Timezone-Aware Datetime**

**Location:** Line 526

```python
tz = pytz.timezone(self.timezone)  # Asia/Tokyo
business_start = tz.localize(datetime.combine(date, datetime.min.time().replace(hour=9)))
```

**Analysis:**
- ✅ Correctly creates timezone-aware datetime
- ✅ `business_start` will have timezone info (Asia/Tokyo)

**Example:**
```python
date = date(2025, 10, 16)
business_start = tz.localize(datetime.combine(date, time(9, 0)))
# Result: datetime(2025, 10, 16, 9, 0, tzinfo=<DstTzInfo 'Asia/Tokyo' JST+9:00:00 STD>)
```

**Verdict:** ✅ **Correct** - Properly handles timezone

---

#### **Pattern 4: Parsing Event Times from API**

**Locations:** Lines 496, 501, 535-536

```python
event_start = datetime.fromisoformat(event['start'].get('dateTime', ''))
# Google returns: "2025-10-16T13:00:00+09:00"
# Result: datetime(2025, 10, 16, 13, 0, 0, tzinfo=timezone(timedelta(seconds=32400)))
```

**Analysis:**
- ✅ Google Calendar API returns timezone-aware strings
- ✅ `fromisoformat()` correctly parses timezone info
- ✅ Preserves UTC+9 offset

**Verdict:** ✅ **Correct** - Properly parses timezone from API

---

## 🐛 Critical Issues Found

### **Issue 1: UTC 'Z' Suffix in Event Queries** ❌

**Problem:** All event queries append 'Z' to naive datetime, causing 9-hour offset

**Affected Lines:**
- Line 218: `timeMin=now.isoformat() + 'Z'`
- Line 219: `timeMax=end.isoformat() + 'Z'`
- Line 258: `timeMin=datetime.now().isoformat() + 'Z'`
- Line 460: `timeMin=start_date.isoformat() + 'Z'`
- Line 461: `timeMax=end_date.isoformat() + 'Z'`
- Line 596: `timeMin=start_date.isoformat() + 'Z'`
- Line 597: `timeMax=end_date.isoformat() + 'Z'`
- Line 733: `timeMin=datetime.now().isoformat() + 'Z'`

**Impact:**
- Events from 00:00-09:00 Tokyo time are MISSED
- Events searches start 9 hours late in Tokyo timezone

**Example:**
```
User wants events for 2025-10-16 (Tokyo time)
Code sends: timeMin="2025-10-16T00:00:00Z" (UTC)
Google interprets: 2025-10-16 00:00 UTC = 2025-10-16 09:00 Tokyo
Result: MISSES events from 00:00-09:00 Tokyo time!
```

---

### **Issue 2: Using `datetime.utcnow()` and `datetime.now()`** ❌

**Problem:** Using timezone-naive datetime functions

**Affected Lines:**
- Line 214: `now = datetime.utcnow()` ← UTC time, no timezone
- Line 258: `datetime.now().isoformat()` ← Local system time, no timezone
- Line 733: `datetime.now().isoformat()` ← Local system time, no timezone

**Impact:**
- System time might not be Tokyo time
- UTC time doesn't account for Tokyo offset
- Inconsistent behavior across deployments

---

## ✅ Correct Implementations

### **What's Working:**

1. ✅ **Event Creation:** Events are created with correct timezone specification
2. ✅ **Business Hours:** Uses `pytz.timezone()` to create timezone-aware times
3. ✅ **Event Parsing:** Correctly parses timezone from Google Calendar API responses

---

## 🔧 Recommended Fixes

### **Fix 1: Use Timezone-Aware Datetime for Queries**

**Instead of:**
```python
start_date = datetime.strptime(date_str, "%Y-%m-%d")
timeMin = start_date.isoformat() + 'Z'  # ❌ Wrong!
```

**Should be:**
```python
tz = pytz.timezone(self.timezone)
start_date = datetime.strptime(date_str, "%Y-%m-%d")
start_date_aware = tz.localize(start_date)
timeMin = start_date_aware.isoformat()  # Includes +09:00
```

### **Fix 2: Use Timezone-Aware `now()`**

**Instead of:**
```python
now = datetime.utcnow()  # ❌ Wrong!
```

**Should be:**
```python
tz = pytz.timezone(self.timezone)
now = datetime.now(tz)  # Timezone-aware Tokyo time
```

### **Fix 3: Convert UTC to Tokyo Time**

**Instead of:**
```python
now = datetime.utcnow()
timeMin = now.isoformat() + 'Z'
```

**Should be:**
```python
tz = pytz.timezone(self.timezone)
now_tokyo = datetime.now(tz)
timeMin = now_tokyo.isoformat()
```

---

## 📊 Summary Table

| Location | Current Implementation | Issue | Correct? |
|----------|----------------------|-------|----------|
| Line 20 | `self.timezone = "Asia/Tokyo"` | None | ✅ |
| Line 169-173 | Event creation with timezone | None | ✅ |
| Line 214 | `datetime.utcnow()` | No timezone info | ❌ |
| Line 218-219 | `.isoformat() + 'Z'` | Forces UTC, 9-hour offset | ❌ |
| Line 258 | `datetime.now() + 'Z'` | System time as UTC | ❌ |
| Line 460-461 | `.isoformat() + 'Z'` | Forces UTC, 9-hour offset | ❌ |
| Line 526 | `tz.localize()` | None | ✅ |
| Line 535-536 | `fromisoformat()` | None | ✅ |
| Line 596-597 | `.isoformat() + 'Z'` | Forces UTC, 9-hour offset | ❌ |
| Line 733 | `datetime.now() + 'Z'` | System time as UTC | ❌ |

---

## 🎯 Impact Assessment

### **High Impact Issues:**

1. **`get_events_for_date()` (Lines 596-597)** - CRITICAL
   - Used by modification flow
   - Missing events from 00:00-09:00 Tokyo time
   - Causes wrong available slots calculation

2. **Event search queries (Lines 218-219, 460-461, 733)** - HIGH
   - Affects all event searches
   - Wrong time range in Tokyo timezone

### **Medium Impact Issues:**

1. **`datetime.utcnow()` (Line 214)** - MEDIUM
   - Used for finding upcoming events
   - May work on UTC server, fails on local/other timezones

---

## 🚀 Action Items

### **Priority 1 (Critical):**
- [ ] Fix `get_events_for_date()` to use timezone-aware datetime
- [ ] Remove all `+ 'Z'` suffixes from isoformat calls
- [ ] Add timezone to all datetime objects before API calls

### **Priority 2 (High):**
- [ ] Replace `datetime.utcnow()` with `datetime.now(tz)`
- [ ] Replace `datetime.now()` with `datetime.now(tz)`
- [ ] Ensure all Google Calendar API calls use proper timezone

### **Priority 3 (Best Practice):**
- [ ] Add timezone validation/logging
- [ ] Document timezone handling
- [ ] Add tests for timezone correctness

---

## 💡 Timezone Best Practices

1. **Always use timezone-aware datetime objects**
2. **Never append 'Z' to naive datetime**
3. **Use `pytz.timezone()` for consistency**
4. **Test across different timezones**
5. **Log timezone info for debugging**

---

## 📝 Conclusion

**Current State:** ❌ **BROKEN** - Critical timezone issues causing 9-hour offset

**Impact:** Events from 00:00-09:00 Tokyo time are not retrieved, causing incorrect available slot calculations

**Solution:** Replace all naive datetime + 'Z' with timezone-aware datetime.isoformat()

**Estimated Fix Time:** 30 minutes to fix all occurrences and test

