# 📅 Google Calendar Sharing Issue - Solution Guide

## 🚨 **Problem Identified:**
When sharing your salon calendar with others, they only see "busy" events without details (client names, services, etc.).

## 🔍 **Root Cause:**
Google Calendar has different sharing permission levels. By default, shared calendars only show "free/busy" information for privacy.

## ✅ **Solutions:**

### **Solution 1: Change Calendar Sharing Permissions (Recommended)**

#### **Step 1: Access Calendar Settings**
1. Go to [Google Calendar](https://calendar.google.com)
2. Find your salon calendar in the left sidebar
3. Click the **three dots** (⋮) next to your calendar name
4. Select **"Settings and sharing"**

#### **Step 2: Update Sharing Permissions**
1. Scroll down to **"Share with specific people"**
2. For each person you want to share with:
   - Click **"Add people"**
   - Enter their email address
   - Change permission from **"See only free/busy"** to **"See all event details"**
   - Click **"Send"**

#### **Step 3: Alternative - Make Calendar Public**
1. In the same settings page
2. Scroll to **"Access permissions"**
3. Check **"Make available to public"**
4. Set permission to **"See all event details"**
5. Copy the **"Public URL to this calendar"**

### **Solution 2: Update Calendar URL in Your System**

#### **Current URL Format:**
```
https://calendar.google.com/calendar/embed?src=CALENDAR_ID
```

#### **Better URL Formats:**

**Option A: Public Calendar URL (if made public)**
```
https://calendar.google.com/calendar/embed?src=CALENDAR_ID&ctz=Asia%2FTokyo
```

**Option B: Shared Calendar URL (for specific users)**
```
https://calendar.google.com/calendar/embed?src=CALENDAR_ID&mode=AGENDA&ctz=Asia%2FTokyo
```

**Option C: Full Calendar View**
```
https://calendar.google.com/calendar/embed?src=CALENDAR_ID&mode=WEEK&ctz=Asia%2FTokyo&showTitle=0&showNav=1&showDate=1&showTabs=1&showCalendars=1
```

### **Solution 3: Create a Public Calendar View**

#### **Step 1: Create a New Public Calendar**
1. In Google Calendar, click **"+"** next to "Other calendars"
2. Select **"Create new calendar"**
3. Name it "Salon Public View"
4. Make it **public** with **"See all event details"** permission

#### **Step 2: Copy Events to Public Calendar**
1. For each reservation event, copy it to the public calendar
2. Or use Google Apps Script to automate this

### **Solution 4: Use Calendar Embed with Better Parameters**

#### **Enhanced Embed URL:**
```
https://calendar.google.com/calendar/embed?src=CALENDAR_ID&ctz=Asia%2FTokyo&mode=WEEK&showTitle=0&showNav=1&showDate=1&showTabs=1&showCalendars=1&showTz=1&height=600&wkst=1&bgcolor=%23ffffff&color=%23B1365F
```

#### **Parameters Explained:**
- `ctz=Asia%2FTokyo` - Tokyo timezone
- `mode=WEEK` - Week view
- `showTitle=0` - Hide calendar title
- `showNav=1` - Show navigation
- `showDate=1` - Show date
- `showTabs=1` - Show tabs
- `showCalendars=1` - Show calendar list
- `showTz=1` - Show timezone
- `height=600` - Calendar height
- `wkst=1` - Week starts on Sunday
- `bgcolor=%23ffffff` - White background
- `color=%23B1365F` - Calendar color

## 🔧 **Technical Implementation:**

### **Update Calendar URL Method:**

```python
def get_calendar_url(self) -> str:
    """Get the public Google Calendar URL for viewing availability"""
    if not self.calendar_id:
        return "https://calendar.google.com/calendar"
    
    # Enhanced calendar URL with better visibility
    base_url = f"https://calendar.google.com/calendar/embed?src={self.calendar_id}"
    params = [
        "ctz=Asia%2FTokyo",  # Tokyo timezone
        "mode=WEEK",         # Week view
        "showTitle=0",       # Hide title
        "showNav=1",         # Show navigation
        "showDate=1",        # Show date
        "showTabs=1",        # Show tabs
        "showCalendars=1",   # Show calendar list
        "showTz=1",          # Show timezone
        "height=600",        # Calendar height
        "wkst=1",            # Week starts Sunday
        "bgcolor=%23ffffff", # White background
        "color=%23B1365F"    # Calendar color
    ]
    
    return f"{base_url}&{'&'.join(params)}"
```

### **Alternative: Public Calendar URL**

```python
def get_public_calendar_url(self) -> str:
    """Get the public calendar URL (if calendar is made public)"""
    if not self.calendar_id:
        return "https://calendar.google.com/calendar"
    
    # Public calendar URL format
    return f"https://calendar.google.com/calendar/embed?src={self.calendar_id}&ctz=Asia%2FTokyo"
```

## 📋 **Step-by-Step Fix:**

### **Immediate Fix (5 minutes):**
1. Go to Google Calendar settings
2. Find your salon calendar
3. Click "Settings and sharing"
4. Scroll to "Access permissions"
5. Check "Make available to public"
6. Set to "See all event details"
7. Copy the public URL

### **Long-term Fix (15 minutes):**
1. Create a dedicated public calendar
2. Set proper sharing permissions
3. Update your system to use the new URL
4. Test with different users

## 🎯 **Recommended Approach:**

### **For Small Salons:**
- Make the main calendar public with "See all event details"
- Use the enhanced embed URL

### **For Larger Salons:**
- Create a separate public calendar
- Copy only necessary information (time slots, availability)
- Keep detailed client information private

### **For Maximum Privacy:**
- Share calendar with specific people only
- Set each person to "See all event details"
- Use the shared calendar URL

## 🔍 **Testing Your Fix:**

1. **Open the calendar URL in incognito mode**
2. **Check if you can see event details**
3. **Test with different user accounts**
4. **Verify timezone display is correct**

## 📞 **Need Help?**

If you're still having issues:
1. Check if the calendar is actually public
2. Verify the calendar ID is correct
3. Test the URL in different browsers
4. Check if there are any Google Workspace restrictions

## 🎉 **Expected Result:**

After implementing the fix, users should see:
- ✅ Full event details (client names, services, times)
- ✅ Proper timezone display (Tokyo time)
- ✅ Professional calendar appearance
- ✅ Easy navigation and viewing
