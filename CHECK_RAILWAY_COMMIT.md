# 🔍 Railway Deployment Verification

## Problem Found:

Railway logs show at **Nov 11, 5:42 AM**:
```
[LEARNING] Recorded: general (success=False, feedback=None)
```

This is the OLD behavior - query should be "research", not "general".

---

## What You Need to Check in Railway Dashboard:

### 1. Find the Deployed Commit SHA

**In Railway:**
1. Go to your TORQ Console deployment
2. Click on the latest deployment
3. Look for **"Commit SHA"** or **"Git Commit"**
4. It should show: `956ecce` (the merge commit from PR #15)

**If it shows a different commit → Railway didn't deploy PR #15**

---

### 2. Check Deployment Time

**Look for:**
- Deployment timestamp should be **after Nov 10, 10:01 PM CST**
- If earlier → Railway is running old code

---

### 3. Check Build Logs

**Search for this in Railway build logs:**
```
Installing dependencies from requirements.txt
python-socketio>=5.9.0
```

**If you DON'T see python-socketio → Old code is deployed**

---

### 4. Check Environment Variables

**In Railway settings:**
- Look for `RAILWAY_GIT_COMMIT_SHA`
- Should be: `956ecce20f50fd72cd6626a47069e657cce1a15b`

---

### 5. Alternative: Check the Actual Deployed File

**In Railway runtime logs, run this command:**

If Railway has a shell/console access:
```bash
grep "if score >" /app/torq_console/ui/intent_detector.py
```

**Expected output (NEW):**
```python
if score > 0.1:  # Minimum threshold (lowered from 0.3 to catch "search" queries)
```

**Bad output (OLD):**
```python
if score > 0.3:  # Minimum threshold
```

---

## Quick Test:

**Tell me these 3 things:**

1. **What commit SHA** does Railway show for the current deployment?
2. **When was it deployed?** (date/time)
3. **Did you see** `python-socketio` in the build logs?

Then I'll know exactly what's wrong.
