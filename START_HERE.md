# 👋 Start Here - Simple Setup Guide

**AI-Powered Complaint Resolution System for Collinson Insurance**

This guide is written for **everyone** - no technical experience needed!

---

## 📋 What You Need

1. **A Computer** with internet connection
2. **10 minutes** of time
3. **An API Key** from Anthropic (we'll show you how to get it)

That's it!

---

## 🚀 Step-by-Step Setup

### Step 1: Get Your API Key (3 minutes)

An API key is like a password that lets the AI work for you.

1. **Go to:** https://console.anthropic.com/
2. **Sign up** for an account (it's free to start)
3. **Click** "API Keys" in the left menu
4. **Click** "Create Key"
5. **Copy** the key (it looks like: `sk-ant-api03-xxxxxxxxxxxx`)

**Important:** Keep this key private! Don't share it with anyone.

---

### Step 2: Add Your API Key (2 minutes)

1. **Find the file** called `.env.example` in this folder
2. **Make a copy** and rename it to `.env`
3. **Open `.env`** with any text editor (Notepad, TextEdit, etc.)
4. **Find the line** that says:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```
5. **Replace** `your_api_key_here` with your actual key:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key
   ```
6. **Save** the file

**That's it!** You're now configured.

---

### Step 3: Load Example Data (1 minute)

Open a terminal/command prompt and type:

```bash
python cli.py init
```

This loads 5 example complaints into the system so you can try it out.

You'll see messages saying it's loading complaints - this is normal!

---

### Step 4: Try It! (2 minutes)

Now the fun part - let's see what the AI can do!

**View all complaints:**
```bash
python cli.py list
```

You'll see 5 complaints from customers like Marco Rossi and Sarah Williams.

**Process a complaint with AI:**
```bash
python cli.py process COMP-2024-001
```

Wait 30-60 seconds and watch the magic:
- ✅ AI classifies the complaint
- ✅ AI analyzes the insurance policy
- ✅ AI writes a response in Italian
- ✅ Shows you saved 3+ hours of work!

---

## 🎯 What Can You Do?

### See All Complaints
```bash
python cli.py list
```

Shows all the complaints in the system.

### Process a Complaint
```bash
python cli.py process COMP-2024-001
```

Let AI analyze a complaint and draft a response.

### See Time & Money Saved
```bash
python cli.py metrics
```

Shows how much time and money you're saving with AI.

### Check Everything Is Working
```bash
python cli.py validate
```

Makes sure everything is set up correctly.

---

## 💡 Understanding the Results

When you process a complaint, you'll see three main sections:

### 1. CLASSIFICATION
```
Category: trip_cancellation
Confidence: 92%
Urgency: high
```

**What this means:** The AI read the complaint and figured out:
- It's about trip cancellation
- It's 92% confident in this classification
- It's high urgency (customer mentioned legal action)

### 2. POLICY ANALYSIS
```
Coverage Decision: COVERED
Confidence: 88%
Reasoning: Customer's father's unexpected heart attack...
```

**What this means:** The AI read the 50+ page policy and determined:
- The claim should be covered
- It's 88% confident in this decision
- It explains why with specific policy references

### 3. TIME SAVINGS
```
Manual Process Time: 4.25 hours
AI-Assisted Time: 1.0 hours
Time Saved: 3.25 hours (76%)
```

**What this means:**
- A human would normally take 4.25 hours
- With AI help, it only takes 1 hour
- You just saved 3.25 hours!

---

## ❓ Common Questions

**Q: Do I need to know programming?**
A: No! Just copy and paste the commands above.

**Q: Will this cost money?**
A: Claude API has a free tier. Each complaint costs about £0.10-0.20 in API calls.

**Q: Is it safe?**
A: Yes! All data stays on your computer. Only the complaint text is sent to Claude for analysis.

**Q: What if something goes wrong?**
A: Type `python cli.py validate` to check your setup. See TROUBLESHOOTING.md for help.

**Q: Can I use real complaints?**
A: Yes! But start with the examples first to learn how it works.

**Q: Does AI replace the complaint handlers?**
A: No! AI does the boring research. Humans still make the final decisions.

---

## 🎬 Demo This to Your Team (5-Minute Version)

### Show the Problem (1 minute)
```bash
python cli.py list
```

**Say:** "Here are 5 complaints. Each one currently takes 4+ hours to handle manually."

### Show the Solution (3 minutes)
```bash
python cli.py process COMP-2024-001
```

**Say:** "Watch AI analyze the complaint, read the policy, and draft a response in 60 seconds..."

**Point out:**
- ✅ Classified correctly
- ✅ Found the right policy sections
- ✅ Wrote professional Italian response
- ✅ Saved 3+ hours

### Show the Impact (1 minute)
```bash
python cli.py metrics
```

**Say:** "Across 100 monthly complaints, this saves:
- 325 hours per month
- £25,000 per month
- £300,000 per year"

---

## 📱 Quick Reference Card

Print this out and keep it handy!

| Command | What It Does |
|---------|--------------|
| `python cli.py init` | Load example data (first time only) |
| `python cli.py list` | See all complaints |
| `python cli.py process COMP-2024-001` | Process a complaint with AI |
| `python cli.py metrics` | See time & money saved |
| `python cli.py validate` | Check everything works |
| `python cli.py --help` | See all commands |

---

## 🆘 Something Not Working?

### "ANTHROPIC_API_KEY not set"
👉 **Fix:** Check your `.env` file has the correct API key

### "No complaints found"
👉 **Fix:** Run `python cli.py init` to load examples

### "Command not found"
👉 **Fix:** Make sure you're in the right folder

### Still stuck?
👉 **Look at:** `docs/TROUBLESHOOTING.md`
👉 **Or ask:** Your IT team

---

## 🎓 Next Steps

Once you're comfortable with the basics:

1. **See DEMO_GUIDE.md** - Full presentation script
2. **See README.md** - Complete documentation
3. **Try processing** all 5 example complaints
4. **Show your team** - Share the time savings!
5. **Plan integration** - Connect to your real systems

---

## 💪 You're Ready!

You now know enough to:
- ✅ Run the system
- ✅ Process complaints
- ✅ See the benefits
- ✅ Demo to others

**Let's transform complaint handling! 🚀**

---

**Need more help?**
- `DEMO_GUIDE.md` - Detailed presentation guide
- `README.md` - Full technical documentation
- `docs/TROUBLESHOOTING.md` - Fix common issues
- `docs/QA_REPORT.md` - Quality testing results

**Questions?** Ask your technical contact or the person who shared this with you!
