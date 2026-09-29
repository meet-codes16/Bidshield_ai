"""Seed script for BidShield AI.
Seeds exactly 5 Officer accounts, 10 Bidder accounts, 10 realistic tenders,
requirements, synthetic document files, and diverse bid evaluation scenarios.
All passwords hashed with Argon2. Strictly obeys UNIQUE(tender_id, bidder_id).
"""
import uuid
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import select
from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.core.config import settings
from app.models.entities import (
    User, Organization, Bidder, Tender, Requirement, Bid, Document, DocumentVersion,
    ComplianceResult, RiskAssessment, AIAnalysis, AuditLog,
    Role, TenderStatus, BidStatus, ComplianceStatus, RiskLevel, VerificationStatus
)
from app.services.hash_service import sha256_file
from app.services.audit_service import log_event
from app.services.document_service import extract_pdf_pages, save_extracted

OFFICERS = [
    {
        "email": "officer.mp@bidshield.demo",
        "password": "Demo@MP2026",
        "full_name": "Rajesh Verma",
        "org": "Madhya Pradesh Public Works Dept.",
        "state": "Madhya Pradesh",
    },
    {
        "email": "officer.rajasthan@bidshield.demo",
        "password": "Demo@RJ2026",
        "full_name": "Sunita Shekhawat",
        "org": "Rajasthan Urban Development Dept.",
        "state": "Rajasthan",
    },
    {
        "email": "officer.maharashtra@bidshield.demo",
        "password": "Demo@MH2026",
        "full_name": "Priya Sharma",
        "org": "Maharashtra Infrastructure Development",
        "state": "Maharashtra",
    },
    {
        "email": "officer.gujarat@bidshield.demo",
        "password": "Demo@GJ2026",
        "full_name": "Kirit Patel",
        "org": "Gujarat Energy & Petrochemicals Dept.",
        "state": "Gujarat",
    },
    {
        "email": "officer.up@bidshield.demo",
        "password": "Demo@UP2026",
        "full_name": "Alok Tripathi",
        "org": "Uttar Pradesh Public Works Dept.",
        "state": "Uttar Pradesh",
    },
]

BIDDERS = [
    {
        "email": "bidder01@bidshield.demo", "password": "Bidder@01",
        "full_name": "Arjun Mehta", "org": "Apex InfraTech Pvt. Ltd.",
        "gstin": "27AAACA1234A1Z5", "pan": "AAACA1234A", "reg": "REG-MH-2024-1182",
        "address": "401 Technopark, MIDC Andheri East, Mumbai, Maharashtra 400093",
    },
    {
        "email": "bidder02@bidshield.demo", "password": "Bidder@02",
        "full_name": "Bhavik Shah", "org": "Bharat Digital Systems Pvt. Ltd.",
        "gstin": "24BBBCB2345B1Z6", "pan": "BBBCB2345B", "reg": "REG-GJ-2023-4521",
        "address": "Plot 12, Infocity Gandhinagar, Gujarat 382007",
    },
    {
        "email": "bidder03@bidshield.demo", "password": "Bidder@03",
        "full_name": "Chirag Rathore", "org": "NexGen Solutions India Pvt. Ltd.",
        "gstin": "08CCCC03456C1Z7", "pan": "CCCC03456C", "reg": "REG-RJ-2022-8923",
        "address": "B-44 Malviya Industrial Area, Jaipur, Rajasthan 302017",
    },
    {
        "email": "bidder04@bidshield.demo", "password": "Bidder@04",
        "full_name": "Deepak Chouhan", "org": "Vertex Engineering Services Pvt. Ltd.",
        "gstin": "23DDDCD4567D1Z8", "pan": "DDDCD4567D", "reg": "REG-MP-2024-6712",
        "address": "Sector C, Industrial Area Govindpura, Bhopal, Madhya Pradesh 462023",
    },
    {
        "email": "bidder05@bidshield.demo", "password": "Bidder@05",
        "full_name": "Eshwar Dixit", "org": "BluePeak Technologies Pvt. Ltd.",
        "gstin": "09EEECE5678E1Z9", "pan": "EEECE5678E", "reg": "REG-UP-2023-3498",
        "address": "Tech Zone 4, Greater Noida, Uttar Pradesh 201308",
    },
    {
        "email": "bidder06@bidshield.demo", "password": "Bidder@06",
        "full_name": "Farhan Ansari", "org": "Arvind Infrastructure Solutions Pvt. Ltd.",
        "gstin": "27FFFCA6789F1ZA", "pan": "FFFCA6789F", "reg": "REG-MH-2021-9871",
        "address": "7th Floor, Cerebrum IT Park, Kalyani Nagar, Pune, Maharashtra 411014",
    },
    {
        "email": "bidder07@bidshield.demo", "password": "Bidder@07",
        "full_name": "Gaurav Joshi", "org": "TechBridge Systems Pvt. Ltd.",
        "gstin": "24GGGCA7890G1ZB", "pan": "GGGCA7890G", "reg": "REG-GJ-2024-5542",
        "address": "Sindhu Bhavan Road, Bodakdev, Ahmedabad, Gujarat 380054",
    },
    {
        "email": "bidder08@bidshield.demo", "password": "Bidder@08",
        "full_name": "Harish Meena", "org": "Suryodaya Engineering Pvt. Ltd.",
        "gstin": "08HHHCA8901H1ZC", "pan": "HHHCA8901H", "reg": "REG-RJ-2023-1129",
        "address": "RIICO Industrial Area, Mansarovar, Jaipur, Rajasthan 302020",
    },
    {
        "email": "bidder09@bidshield.demo", "password": "Bidder@09",
        "full_name": "Inderjit Yadav", "org": "Innovexa Digital Pvt. Ltd.",
        "gstin": "23IIICA9012I1ZD", "pan": "IIICA9012I", "reg": "REG-MP-2022-7782",
        "address": "Electronic Complex, Pardesipura, Indore, Madhya Pradesh 452010",
    },
    {
        "email": "bidder10@bidshield.demo", "password": "Bidder@10",
        "full_name": "Jitendra Maurya", "org": "PrimeGrid Technologies Pvt. Ltd.",
        "gstin": "09JJJCA0123J1ZE", "pan": "JJJCA0123J", "reg": "REG-UP-2024-9943",
        "address": "Vibhuti Khand, Gomti Nagar, Lucknow, Uttar Pradesh 226010",
    },
]

TENDERS = [
    {
        "number": "TND-2026-101",
        "title": "State Data Center Modernization & Cloud Migration",
        "department": "IT & Electronics Dept. · Madhya Pradesh",
        "category": "INFORMATION TECHNOLOGY",
        "value": 65000000,
        "days": 25,
        "status": TenderStatus.PUBLISHED,
        "desc": "Turnkey infrastructure modernization, hybrid cloud migration, and Tier-III data center upgrade for state e-governance systems.",
        "reqs": [
            ("Valid company incorporation certificate (CIN)", True, 1.0),
            ("Active GST registration certificate with clear tax compliance", True, 1.0),
            ("ISO 27001 Information Security Management Certification", True, 1.0),
            ("Minimum 5 years demonstrated experience in enterprise cloud migration", True, 1.0),
            ("Average annual audited turnover of at least ₹15 crore for last 3 financial years", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-102",
        "title": "AI-Powered Automated Traffic Enforcement & Monitoring",
        "department": "Home & Transport Dept. · Maharashtra",
        "category": "AI MONITORING",
        "value": 92000000,
        "days": 18,
        "status": TenderStatus.PUBLISHED,
        "desc": "Supply, installation, and 5-year maintenance of ANPR cameras, speed violation detection, and automated challan generation software.",
        "reqs": [
            ("Certificate of Incorporation under Companies Act", True, 1.0),
            ("Valid GST and PAN verification documentation", True, 1.0),
            ("CMMI Level 3 or higher software quality appraisal", False, 0.8),
            ("Proven track record in deploying smart city computer vision systems", True, 1.0),
            ("Audited net worth above ₹10 crore as on March 31, 2025", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-103",
        "title": "Integrated Municipal Waste & Water Digital Management System",
        "department": "Urban Development Dept. · Gujarat",
        "category": "SMART CITY",
        "value": 48000000,
        "days": 14,
        "status": TenderStatus.PUBLISHED,
        "desc": "Deployment of IoT-enabled waste bin telemetry, water pressure sensors, SCADA dashboard, and municipal supervisor mobile apps.",
        "reqs": [
            ("Valid company registration & MCA filings", True, 1.0),
            ("GST compliance certificate with zero pending departmental notices", True, 1.0),
            ("Prior municipal IoT deployment completion certificate", True, 1.0),
            ("Financial solvency certificate from a Scheduled Commercial Bank of min ₹5 crore", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-104",
        "title": "Statewide Hospital Diagnostic Equipment Digitization",
        "department": "Medical Health & Family Welfare · Rajasthan",
        "category": "HEALTHCARE TECHNOLOGY",
        "value": 78000000,
        "days": 30,
        "status": TenderStatus.PUBLISHED,
        "desc": "Integration of digital radiology, pathology LIMS, and central health records repository across 45 district hospitals.",
        "reqs": [
            ("Company incorporation and valid OEM authorization letters", True, 1.0),
            ("GST and tax clearance certificates", True, 1.0),
            ("ISO 13485 Medical Devices Quality Certification", True, 1.0),
            ("Experience in HL7 / FHIR compliant hospital information software", True, 1.0),
            ("Annual turnover exceeding ₹12 crore", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-105",
        "title": "Unified Public Grievance Redressal & Citizen Portal",
        "department": "Administrative Reforms · Uttar Pradesh",
        "category": "E-GOVERNANCE",
        "value": 34000000,
        "days": 10,
        "status": TenderStatus.PUBLISHED,
        "desc": "Omnichannel grievance intake platform with AI classification, automated SLA routing, SMS tracking, and call center dashboard.",
        "reqs": [
            ("Company registration certificate", True, 1.0),
            ("GST registration and active filing proof", True, 1.0),
            ("Demonstrated public grievance / helpdesk portal deployment experience", True, 1.0),
            ("24x7 technical support SLA guarantee for 3 years", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-106",
        "title": "Comprehensive Enterprise Cybersecurity Operations Center (SOC)",
        "department": "Science & Technology Dept. · Madhya Pradesh",
        "category": "CYBERSECURITY",
        "value": 115000000,
        "days": 21,
        "status": TenderStatus.PUBLISHED,
        "desc": "Establishment of a 24x7 Managed Security Operations Center with SIEM, SOAR, threat intelligence, and Cert-In empanelment.",
        "reqs": [
            ("CERT-In Empanelled Information Security Auditing Organization status", True, 1.0),
            ("Valid GST and legal incorporation certificate", True, 1.0),
            ("ISO 27001 and ISO 20000 certifications", True, 1.0),
            ("Minimum 3 completed SOC implementation projects for public sector or BFSI", True, 1.0),
            ("Dedicated team of certified analysts (CISSP, CEH, CISM)", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-107",
        "title": "Smart Grid Metering & IoT Analytics Infrastructure",
        "department": "Energy & Petrochemicals · Gujarat",
        "category": "ENERGY & UTILITIES",
        "value": 140000000,
        "days": 35,
        "status": TenderStatus.PUBLISHED,
        "desc": "Installation of 500,000 smart prepaid electricity meters with automated meter reading (AMR) and analytics engine.",
        "reqs": [
            ("Class-A Electrical Contractor license & Company incorporation", True, 1.0),
            ("GST and tax compliance certificate", True, 1.0),
            ("BIS certification for smart energy meters (IS 16444)", True, 1.0),
            ("Cumulative turnover of ₹50 crore in power/metering domain", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-108",
        "title": "Digitization & Archival of Land Revenue Records",
        "department": "Revenue & Forest Dept. · Maharashtra",
        "category": "DOCUMENT DIGITIZATION",
        "value": 39000000,
        "days": -5,
        "status": TenderStatus.CLOSED,
        "desc": "High-resolution scanning, indexing, metadata tagging, and geo-referenced indexing of 8 million historical land records.",
        "reqs": [
            ("Company incorporation certificate", True, 1.0),
            ("GST clearance certificate", True, 1.0),
            ("Prior archival digitization experience for government departments", True, 1.0),
            ("Data security and confidentiality bond compliance", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-109",
        "title": "Solar Power Rooftop Installation Across District Collectorates",
        "department": "Renewable Energy Development · Rajasthan",
        "category": "RENEWABLE ENERGY",
        "value": 52000000,
        "days": 28,
        "status": TenderStatus.PUBLISHED,
        "desc": "Design, supply, installation, testing and commissioning of 15 kW to 100 kW grid-connected solar PV rooftop plants with net metering.",
        "reqs": [
            ("MNRE approved channel partner / EPC contractor certificate", True, 1.0),
            ("GST registration and clearance", True, 1.0),
            ("Minimum 3 years solar EPC execution experience", True, 1.0),
            ("Average annual turnover of at least ₹6 crore", True, 1.0),
        ]
    },
    {
        "number": "TND-2026-110",
        "title": "Rural Telemedicine Network & Remote Patient Care Units",
        "department": "Health & Family Welfare · Uttar Pradesh",
        "category": "TELEHEALTH",
        "value": 61000000,
        "days": -2,
        "status": TenderStatus.CLOSED,
        "desc": "Setup of 120 rural telemedicine kiosks with point-of-care diagnostics, video consultation software, and electronic prescription gateway.",
        "reqs": [
            ("Company registration certificate", True, 1.0),
            ("GST and PAN documents", True, 1.0),
            ("Telemedicine software compliance with National Digital Health Mission (ABDM)", True, 1.0),
            ("Hardware and software maintenance SLA for 3 years", True, 1.0),
        ]
    },
]


def seed_database(force=False):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded
        officer_count = db.scalar(select(User).where(User.role.in_([Role.OFFICER, Role.MINISTRY_OFFICER])))
        if officer_count and not force:
            print("Database already contains officer accounts. Skipping full re-seed.")
            return

        print("Seeding fresh demo database...")
        now = datetime.now(timezone.utc)

        # 1. Seed 5 Officers
        officer_objs = []
        for off in OFFICERS:
            org = db.scalar(select(Organization).where(Organization.name == off["org"]))
            if not org:
                org = Organization(name=off["org"])
                db.add(org); db.flush()
            user = db.scalar(select(User).where(User.email == off["email"]))
            if not user:
                user = User(
                    email=off["email"],
                    password_hash=hash_password(off["password"]),
                    full_name=off["full_name"],
                    role=Role.MINISTRY_OFFICER,
                    organization_id=org.id,
                )
                db.add(user); db.flush()
                log_event(db, user.id, "USER_REGISTERED", "user", user.id, {"role": "MINISTRY_OFFICER", "org": off["org"]})
            officer_objs.append(user)

        # Also preserve officer@bidshield.ai as an alias pointing to Priya Sharma for legacy demo tests
        priya_org = db.scalar(select(Organization).where(Organization.name == "Maharashtra Infrastructure Development"))
        legacy_officer = db.scalar(select(User).where(User.email == "officer@bidshield.ai"))
        if not legacy_officer and priya_org:
            db.add(User(
                email="officer@bidshield.ai",
                password_hash=hash_password("BidShield@2026"),
                full_name="Priya Sharma",
                role=Role.MINISTRY_OFFICER,
                organization_id=priya_org.id
            ))
            db.flush()

        # 2. Seed 10 Bidders
        bidder_objs = []
        for bdata in BIDDERS:
            org = db.scalar(select(Organization).where(Organization.name == bdata["org"]))
            if not org:
                org = Organization(name=bdata["org"])
                db.add(org); db.flush()

            user = db.scalar(select(User).where(User.email == bdata["email"]))
            if not user:
                user = User(
                    email=bdata["email"],
                    password_hash=hash_password(bdata["password"]),
                    full_name=bdata["full_name"],
                    role=Role.BIDDER,
                    organization_id=org.id,
                )
                db.add(user); db.flush()

            b_profile = db.scalar(select(Bidder).where(Bidder.organization_id == org.id))
            if not b_profile:
                b_profile = Bidder(
                    organization_id=org.id,
                    organization_name=org.name,
                    gstin=bdata["gstin"],
                    pan=bdata["pan"],
                    registration_number=bdata["reg"],
                    address=bdata["address"],
                    verification_status=VerificationStatus.VERIFIED,
                )
                db.add(b_profile); db.flush()
            bidder_objs.append(b_profile)

        # Legacy bidder alias for backwards-compatibility
        apex_org = db.scalar(select(Organization).where(Organization.name == "Apex InfraTech Pvt. Ltd."))
        legacy_bidder = db.scalar(select(User).where(User.email == "bidder@bidshield.ai"))
        if not legacy_bidder and apex_org:
            db.add(User(
                email="bidder@bidshield.ai",
                password_hash=hash_password("BidShield@2026"),
                full_name="Arjun Mehta",
                role=Role.BIDDER,
                organization_id=apex_org.id
            ))
            db.flush()

        # 3. Seed 10 Realistic Tenders
        tender_objs = []
        for idx, tdata in enumerate(TENDERS):
            t_obj = db.scalar(select(Tender).where(Tender.tender_number == tdata["number"]))
            assigned_officer = officer_objs[idx % len(officer_objs)]
            if not t_obj:
                deadline = now + timedelta(days=tdata["days"])
                t_obj = Tender(
                    tender_number=tdata["number"],
                    title=tdata["title"],
                    description=tdata["desc"],
                    department=tdata["department"],
                    category=tdata["category"],
                    estimated_value=tdata["value"],
                    publish_date=now - timedelta(days=20),
                    submission_deadline=deadline,
                    status=tdata["status"],
                    created_by=assigned_officer.id,
                )
                db.add(t_obj); db.flush()
                log_event(db, assigned_officer.id, "TENDER_CREATED", "tender", t_obj.id, {"tender_number": tdata["number"]})
                log_event(db, assigned_officer.id, "TENDER_PUBLISHED", "tender", t_obj.id)

                for text, mand, w in tdata["reqs"]:
                    req = Requirement(
                        tender_id=t_obj.id,
                        requirement_text=text,
                        mandatory=mand,
                        weight=w,
                        category=tdata["category"],
                    )
                    db.add(req); db.flush()
            tender_objs.append(t_obj)

        # 4. Prepare Sample Evidence PDF on disk
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        sample_doc_id = uuid.uuid4()
        sample_pdf_path = upload_dir / f"{sample_doc_id}.pdf"
        if not sample_pdf_path.exists():
            # Create a valid minimal synthetic PDF with realistic company evidence text
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 72), "Apex InfraTech Pvt. Ltd. — Comprehensive Technical Bid Evidence\n\n"
                                       "1. Certificate of Incorporation: CIN U72900MH2018PTC309124, registered in Mumbai.\n"
                                       "2. GST Registration: GSTIN 27AAACA1234A1Z5, status Active, returns filed up to date.\n"
                                       "3. Information Security: ISO 27001:2022 Certified (Certificate No: IS-982314-IND).\n"
                                       "4. Experience: Over 7 years of enterprise cloud migration and government infrastructure projects.\n"
                                       "5. Audited Financial Turnover: FY 2022-23: ₹18.2 Cr, FY 2023-24: ₹21.5 Cr, FY 2024-25: ₹24.8 Cr.\n"
                                       "6. Net Worth: Positive net worth of ₹16.4 Crore certified by statutory auditors.\n"
                                       "7. Authorized Signatory: Arjun Mehta, Director, Apex InfraTech Pvt. Ltd.")
            doc.save(str(sample_pdf_path))
            doc.close()

        sample_hash = sha256_file(str(sample_pdf_path))

        # 5. Seed Bids demonstrating different evaluation scenarios
        # Strict constraint: (tender_id, bidder_id) must be UNIQUE!
        bids_to_seed = [
            # Scenario A: Bidder 01 on Tender 101 -> Fully compliant (PASS, LOW risk)
            {
                "tender_idx": 0, "bidder_idx": 0, "status": BidStatus.UNDER_REVIEW,
                "ai_rec": "PASS", "risk_level": RiskLevel.LOW, "risk_score": 12.0,
                "comp_score": 100.0, "mand_score": 100.0,
                "overall_ai": "Bidder meets all mandatory and technical criteria. High financial turnover and ISO 27001 verified.",
                "strengths": ["Turnover exceeds ₹15 crore threshold.", "ISO 27001 valid certificate present."],
                "concerns": [],
            },
            # Scenario B: Bidder 02 on Tender 102 -> Needs Review / Clarification (MEDIUM risk)
            {
                "tender_idx": 1, "bidder_idx": 1, "status": BidStatus.CLARIFICATION_REQUIRED,
                "ai_rec": "REVIEW", "risk_level": RiskLevel.MEDIUM, "risk_score": 42.0,
                "comp_score": 75.0, "mand_score": 80.0,
                "overall_ai": "Technical capability satisfied but CMMI Level 3 quality certificate requires clarification.",
                "strengths": ["Strong smart city computer vision portfolio."],
                "concerns": ["CMMI Level 3 certificate expired last month; renewal confirmation pending."],
            },
            # Scenario C: Bidder 03 on Tender 103 -> Incompliant / Mandatory Failure (HIGH risk)
            {
                "tender_idx": 2, "bidder_idx": 2, "status": BidStatus.UNDER_REVIEW,
                "ai_rec": "REVIEW", "risk_level": RiskLevel.HIGH, "risk_score": 78.0,
                "comp_score": 40.0, "mand_score": 50.0,
                "overall_ai": "Bank solvency certificate is missing and past municipal telemetry references incomplete.",
                "strengths": ["Valid GST registration."],
                "concerns": ["Missing mandatory Scheduled Commercial Bank solvency certificate.", "Incomplete experience evidence."],
            },
            # Scenario D: Bidder 04 on Tender 101 -> Submitted / Evaluated
            {
                "tender_idx": 0, "bidder_idx": 3, "status": BidStatus.ACCEPTED,
                "ai_rec": "PASS", "risk_level": RiskLevel.LOW, "risk_score": 15.0,
                "comp_score": 95.0, "mand_score": 100.0,
                "overall_ai": "Excellent technical qualifications and cloud migration references. Approved by officer.",
                "strengths": ["Enterprise cloud expertise demonstrated."],
                "concerns": [],
            },
            # Scenario E: Bidder 05 on Tender 104 -> Accepted
            {
                "tender_idx": 3, "bidder_idx": 4, "status": BidStatus.ACCEPTED,
                "ai_rec": "PASS", "risk_level": RiskLevel.LOW, "risk_score": 18.0,
                "comp_score": 90.0, "mand_score": 100.0,
                "overall_ai": "ISO 13485 and FHIR hospital integration documentation fully satisfied.",
                "strengths": ["Healthcare interoperability expertise."],
                "concerns": [],
            },
            # Scenario F: Bidder 06 on Tender 105 -> Submitted
            {
                "tender_idx": 4, "bidder_idx": 5, "status": BidStatus.SUBMITTED,
                "ai_rec": "PASS", "risk_level": RiskLevel.LOW, "risk_score": 20.0,
                "comp_score": 88.0, "mand_score": 100.0,
                "overall_ai": "Grievance redressal portal references clear.",
                "strengths": ["State citizen portal references."],
                "concerns": [],
            },
        ]

        for s in bids_to_seed:
            t = tender_objs[s["tender_idx"]]
            b_profile = bidder_objs[s["bidder_idx"]]
            existing_bid = db.scalar(select(Bid).where(Bid.tender_id == t.id, Bid.bidder_id == b_profile.id))
            if not existing_bid:
                bid = Bid(
                    tender_id=t.id,
                    bidder_id=b_profile.id,
                    status=s["status"],
                    submitted_at=now - timedelta(days=2),
                    ai_recommendation=s["ai_rec"],
                    officer_decision="APPROVE" if s["status"] == BidStatus.ACCEPTED else ("CLARIFICATION_REQUIRED" if s["status"] == BidStatus.CLARIFICATION_REQUIRED else None),
                    officer_reason="Officer reviewed evidence." if s["status"] == BidStatus.ACCEPTED else None,
                )
                db.add(bid); db.flush()

                # Add sample document with unique ID and file
                doc_id = uuid.uuid4()
                bid_pdf_path = upload_dir / f"{doc_id}.pdf"
                shutil.copyfile(sample_pdf_path, bid_pdf_path)
                try:
                    pages = extract_pdf_pages(str(bid_pdf_path))
                    save_extracted(doc_id, pages)
                except Exception:
                    pass

                doc = Document(
                    id=doc_id,
                    bid_id=bid.id,
                    document_type="TECHNICAL_BID",
                    original_filename="Technical_Bid_Evidence.pdf",
                    mime_type="application/pdf",
                    file_size=sample_pdf_path.stat().st_size,
                    sha256=sample_hash,
                    status="PROCESSED",
                    storage_key=f"{doc_id}.pdf"
                )
                db.add(doc)
                db.add(DocumentVersion(document_id=doc_id, version_number=1, sha256=sample_hash, storage_key=f"{doc_id}.pdf"))
                db.flush()

                # Add Compliance Results for each requirement
                reqs = db.scalars(select(Requirement).where(Requirement.tender_id == t.id)).all()
                for ri, r in enumerate(reqs):
                    is_pass = (s["comp_score"] >= 80) or (ri == 0)
                    cr = ComplianceResult(
                        bid_id=bid.id,
                        requirement_id=r.id,
                        status=ComplianceStatus.PASS if is_pass else ComplianceStatus.REVIEW,
                        confidence=0.92 if is_pass else 0.45,
                        explanation="Evidence confirmed in uploaded technical package." if is_pass else "Document evidence requires clarification or is incomplete.",
                        ai_recommendation="PASS" if is_pass else "REVIEW"
                    )
                    db.add(cr)

                # Add Risk Assessment
                db.add(RiskAssessment(
                    bid_id=bid.id,
                    risk_score=s["risk_score"],
                    risk_level=s["risk_level"],
                    factors={"compliance_deficit": max(0, 100 - s["comp_score"]) * 0.45}
                ))

                # Add AI Analysis
                db.add(AIAnalysis(
                    bid_id=bid.id,
                    overall_assessment=s["overall_ai"],
                    key_strengths=s["strengths"],
                    key_concerns=s["concerns"],
                    clarifications_required=["Please upload certified copy"] if s["risk_level"] != RiskLevel.LOW else [],
                    model_name="llama-3.3-70b-versatile"
                ))

                log_event(db, officer_objs[0].id, "BID_SUBMITTED", "bid", bid.id)
                log_event(db, officer_objs[0].id, "AI_ANALYSIS_COMPLETED", "bid", bid.id, {"compliance_score": s["comp_score"], "risk": s["risk_level"].value})

        db.commit()
        print("Demo database seeded successfully with 5 officers, 10 bidders, 10 tenders, and realistic bids.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(force=True)
