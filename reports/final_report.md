# Fintech Review Analytics: Final Report

> **Omega Consultancy** | 10 Academy Week 2 Challenge
> Date: May 19, 2026

---

## Executive Summary

This report analyzes **1500 Google Play Store reviews** across three Ethiopian banks:
- **Commercial Bank of Ethiopia (CBE)**
- **Bank of Abyssinia (BOA)**
- **Dashen Bank**

Our pipeline scraped, cleaned, classified sentiment, extracted themes, and stored results in PostgreSQL. Key findings reveal distinct satisfaction drivers and critical pain points for each bank.

---

## Methodology

### Data Collection
- **Source:** Google Play Store reviews
- **Tool:** `google-play-scraper` Python library
- **Coverage:** 400+ reviews per bank (1,200+ total)
- **Fields:** Review text, rating (1–5), date, bank name

### Sentiment Analysis
- **Primary Model:** DistilBERT (`distilbert-base-uncased-finetuned-sst-2-english`)
- **Fallback:** VADER (lexicon-based) for comparison
- **Output:** positive / negative / neutral labels with confidence scores

### Thematic Analysis
- **Method:** Keyword extraction via TF-IDF + rule-based theme assignment
- **Themes:** Account Access Issues, Transaction Performance, UI & Design, Customer Support, Feature Requests, App Stability

### Database
- **System:** PostgreSQL
- **Schema:** Relational (banks ↔ reviews with FK)

---

## Cross-Bank Comparison

| bank                               |   total_reviews |   avg_rating |   positive_pct |   negative_pct | top_theme               | top_pain_point          | top_driver              |
|:-----------------------------------|----------------:|-------------:|---------------:|---------------:|:------------------------|:------------------------|:------------------------|
| Bank of Abyssinia Mobile           |             500 |         1.69 |           10.8 |           72.6 | General                 | Account Access Issues   | N/A                     |
| Commercial Bank of Ethiopia Mobile |             500 |         2.67 |           19.2 |           70.8 | Transaction Performance | Transaction Performance | N/A                     |
| Dashen Bank SuperApp               |             500 |         3.84 |           57.6 |           29.8 | General                 | Account Access Issues   | Transaction Performance |

---


## Bank of Abyssinia Mobile: Deep Dive

### Satisfaction Drivers

No strong positive themes identified. Consider running targeted satisfaction surveys.

### Pain Points

**1. Account Access Issues** (95 reviews, 73.7% negative)
> "I opened a diaspora account and a local account with your bank. I often travel overseas and cannot access my account, tr..."

**2. Transaction Performance** (93 reviews, 71.0% negative)
> "Please update the app. The previous version was much more stable, fast, and reliable. This version is the worst. 1, It t..."

**3. App Stability** (86 reviews, 70.9% negative)
> "I can't load money to my telebirr account. It says error bla bla. And the app is not smooth, it takes time to load every..."

### Recommendations

**P1: Fix Account Access Issues**

*Account Access Issues is the top complaint (95 reviews, 73.7% negative). Example: 'I opened a diaspora account and a local account with your bank. I often travel overseas and cannot access my account, tr...'*

**Action Items:**
- Implement biometric login (fingerprint / face ID)
- Add 'remember device' option to reduce OTP fatigue
- Create self-service password reset flow

*Expected Impact:* Reduce negative reviews by 20-30% and improve app store rating by 0.3 stars

**P2: Improve App Stability**

*App Stability reviews average 1.3 stars. Crashes and freezes directly drive uninstalls.*

**Action Items:**
- Implement crash analytics (Firebase Crashlytics)
- Add offline mode for critical transactions
- Reduce app size and memory footprint

*Expected Impact:* Reduce churn by 15% and improve store rating

---


## Commercial Bank of Ethiopia Mobile: Deep Dive

### Satisfaction Drivers

No strong positive themes identified. Consider running targeted satisfaction surveys.

### Pain Points

**1. Transaction Performance** (213 reviews, 74.6% negative)
> "The app has some issues we need to have a place where we save our contacts where we usually send money to, after update ..."

**2. Account Access Issues** (65 reviews, 81.5% negative)
> "To the Commercial Bank of Ethiopia (CBE), I am writing to express my concern regarding the recent update to the CBE Mobi..."

**3. App Stability** (64 reviews, 71.9% negative)
> "The app is getting worse and worse after every "update". The UI is inconsistent, you haven't fixed the issue with Mpesa ..."

### Recommendations

**P1: Fix Transaction Performance**

*Transaction Performance is the top complaint (213 reviews, 74.6% negative). Example: 'The app has some issues we need to have a place where we save our contacts where we usually send money to, after update ...'*

**Action Items:**
- Optimize backend API response times
- Add transaction progress indicators
- Implement retry logic for failed transfers

*Expected Impact:* Reduce negative reviews by 20-30% and improve app store rating by 0.3 stars

**P2: Improve App Stability**

*App Stability reviews average 2.2 stars. Crashes and freezes directly drive uninstalls.*

**Action Items:**
- Implement crash analytics (Firebase Crashlytics)
- Add offline mode for critical transactions
- Reduce app size and memory footprint

*Expected Impact:* Reduce churn by 15% and improve store rating

---


## Dashen Bank SuperApp: Deep Dive

### Satisfaction Drivers

**1. Transaction Performance** (133 reviews, 60.2% positive)
> "Dashen Bank SuperApp is userfriendly, fast, and very convenient for daily banking. Transactions are smooth, and the app ..."

**2. UI & Design** (67 reviews, 86.6% positive)
> "The best mobile super app in Ethiopia specifically I like it's User interface(UI)"

**3. Customer Support** (32 reviews, 65.6% positive)
> "Why havent you fixed this issue  Temporarily Unavailable We're currently updating this service to improve your experienc..."

### Pain Points

**1. Account Access Issues** (30 reviews, 56.7% negative)
> "The app is grand. but it's missing two things. one is the option to see exchange rates and the other is, when opening th..."

**2. App Stability** (28 reviews, 71.4% negative)
> "The worst mobile banking app ever... I don't think I am ever going to deposit anything from now on if I can't use the ap..."

### Recommendations

**P1: Fix Account Access Issues**

*Account Access Issues is the top complaint (30 reviews, 56.7% negative). Example: 'The app is grand. but it's missing two things. one is the option to see exchange rates and the other is, when opening th...'*

**Action Items:**
- Implement biometric login (fingerprint / face ID)
- Add 'remember device' option to reduce OTP fatigue
- Create self-service password reset flow

*Expected Impact:* Reduce negative reviews by 20-30% and improve app store rating by 0.3 stars

**P2: Amplify Transaction Performance**

*Users love Transaction Performance (133 reviews, 60.2% positive). Double down on this strength.*

**Action Items:**
- Market 'instant transfer' as key differentiator
- Add transfer speed badges in UI

*Expected Impact:* Increase user retention and positive word-of-mouth

**P2: Improve App Stability**

*App Stability reviews average 2.3 stars. Crashes and freezes directly drive uninstalls.*

**Action Items:**
- Implement crash analytics (Firebase Crashlytics)
- Add offline mode for critical transactions
- Reduce app size and memory footprint

*Expected Impact:* Reduce churn by 15% and improve store rating

---

## Limitations & Ethical Considerations

- **Scraping constraints:** Google Play Store rate limits may restrict review volume
- **Language bias:** Analysis focuses on English reviews; Amharic feedback is excluded
- **Self-selection bias:** Reviewers tend to be either very satisfied or very dissatisfied
- **Temporal bias:** Reviews reflect current app versions; past issues may be resolved
- **Privacy:** No personally identifiable information was collected or stored

---

## Suggested Next Steps

1. **Quarterly tracking:** Re-run pipeline monthly to track sentiment trends
2. **Amharic NLP:** Add Amharic language support for broader coverage
3. **Competitor expansion:** Add more Ethiopian banks (Awash, Hibret, etc.)
4. **Integration:** Feed real-time alerts to product teams via Slack/email
5. **Predictive modeling:** Build churn prediction from review sentiment + app usage data

---

*Report generated by Omega Consultancy Data Analytics Pipeline*
*Version: 1.0 | 2026-05-19 16:21 UTC*