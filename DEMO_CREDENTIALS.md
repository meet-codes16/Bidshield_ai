# BidShield AI — Demo Credentials & Evaluation Guide

This document lists the realistic synthetic accounts and credentials provisioned in BidShield AI for live evaluation and demonstration. All passwords are encrypted with **Argon2** password hashing in the database.

---

## 1. Ministry / Procurement Officer Accounts (5 States)

These accounts represent state procurement departments and public works directorates across India. Officers can create tenders, inspect bidder submissions, review AI-generated compliance scores, examine Groq LLM executive summaries, and record legally accountable audit decisions.

| State | Officer Name | Department / Ministry | Work Email | Demo Password |
|---|---|---|---|---|
| **Madhya Pradesh** | Rajesh Verma | Madhya Pradesh Public Works Dept. | `officer.mp@bidshield.demo` | `Demo@MP2026` |
| **Rajasthan** | Sunita Shekhawat | Rajasthan Urban Development Dept. | `officer.rajasthan@bidshield.demo` | `Demo@RJ2026` |
| **Maharashtra** | Priya Sharma | Maharashtra Infrastructure Development | `officer.maharashtra@bidshield.demo` | `Demo@MH2026` |
| **Gujarat** | Kirit Patel | Gujarat Energy & Petrochemicals Dept. | `officer.gujarat@bidshield.demo` | `Demo@GJ2026` |
| **Uttar Pradesh** | Alok Tripathi | Uttar Pradesh Public Works Dept. | `officer.up@bidshield.demo` | `Demo@UP2026` |

*Legacy alias:* `officer@bidshield.ai` / `BidShield@2026` is also supported for backward compatibility.

---

## 2. Registered Vendor / Bidder Accounts (10 Vendors)

These accounts represent real-world enterprise vendors across different sectors. Each vendor has a verified profile, statutory registration (GSTIN, PAN), and submitted technical bids.

| # | Vendor Organization | State | Sign-in Email | Demo Password | GSTIN | PAN |
|---|---|---|---|---|---|---|
| **01** | Apex InfraTech Pvt. Ltd. | Maharashtra | `bidder01@bidshield.demo` | `Bidder@01` | `27AAACA1234A1Z5` | `AAACA1234A` |
| **02** | Bharat Digital Systems Pvt. Ltd. | Gujarat | `bidder02@bidshield.demo` | `Bidder@02` | `24BBBCB2345B1Z6` | `BBBCB2345B` |
| **03** | NexGen Solutions India Pvt. Ltd. | Rajasthan | `bidder03@bidshield.demo` | `Bidder@03` | `08CCCC03456C1Z7` | `CCCC03456C` |
| **04** | Vertex Engineering Services Pvt. Ltd. | Madhya Pradesh | `bidder04@bidshield.demo` | `Bidder@04` | `23DDDCD4567D1Z8` | `DDDCD4567D` |
| **05** | BluePeak Technologies Pvt. Ltd. | Uttar Pradesh | `bidder05@bidshield.demo` | `Bidder@05` | `09EEECE5678E1Z9` | `EEECE5678E` |
| **06** | Arvind Infrastructure Solutions Pvt. Ltd. | Maharashtra | `bidder06@bidshield.demo` | `Bidder@06` | `27FFFCA6789F1ZA` | `FFFCA6789F` |
| **07** | TechBridge Systems Pvt. Ltd. | Gujarat | `bidder07@bidshield.demo` | `Bidder@07` | `24GGGCG7890G1ZB` | `GGGCG7890G` |
| **08** | Surya Buildcon Projects Pvt. Ltd. | Rajasthan | `bidder08@bidshield.demo` | `Bidder@08` | `08HHHCH8901H1ZC` | `HHHCH8901H` |
| **09** | Kavach Cyber Security Solutions Pvt. Ltd. | Madhya Pradesh | `bidder09@bidshield.demo` | `Bidder@09` | `23IIICI9012I1ZD` | `IIICI9012I` |
| **10** | Pratham Healthcare Equipments Pvt. Ltd. | Uttar Pradesh | `bidder10@bidshield.demo` | `Bidder@10` | `09JJJCJ0123J1ZE` | `JJJCJ0123J` |

*Legacy alias:* `bidder@bidshield.ai` / `BidShield@2026` is also supported for backward compatibility.

---

## 3. Strict Rules & Constraints Enforced

1. **One Bid Per Bidder Per Tender**:
   - Enforced at database level via `UNIQUE(tender_id, bidder_id)` constraint.
   - Enforced at API level (`POST /api/bids/tenders/{tender_id}/bids`) returning `409 Conflict`.
   - Enforced on frontend UI: Once submitted, the tender row shows `Bid Submitted (Locked)` with a button to view the existing bid instead of allowing duplicate submissions.
2. **Cryptographic Audit Trail**:
   - Every tender published, bid submitted, document uploaded, AI analysis executed, and officer decision is chained with SHA-256 hashes (`previous_hash -> current_hash`).
   - Exportable via the **Audit Trail** screen.
3. **Hybrid AI Engine**:
   - Deterministic rule verification + scikit-learn TF-IDF RAG retrieval + Groq LLM executive reasoning (`openai/gpt-oss-20b`).
   - Cached in `ai_analyses` table for instant review rendering.
