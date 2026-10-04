"""Digital Governance & Cybersecurity Module Seeding Logic.

Seeds official curriculum, lessons, national examination, and procedural CTF challenges.
"""
import json
import tempfile
import base64
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.models import Department, Course, Module, Lesson, Assessment, Question, Skill, CourseSkill
from app.modules.digital_governance.models import CyberSandboxTemplate, CyberSandboxChallenge
from app.modules.digital_governance.services.templates import get_template

def seed_digital_governance_curriculum(db: Session):
    """
    Seeds the official Digital Governance, Cyber Defense & Public Digital Architecture curriculum,
    covering the 5 mandatory Government of India civil-service pillars:
    1. Cybersecurity (CERT-In directives, Section 70B IT Act 2000, CII protection, SOC telemetry)
    2. Data Privacy (Digital Personal Data Protection Act 2023, Data Fiduciaries, DPBI)
    3. Digital Signatures & PKI (IT Act Sections 3 & 3A, CCA, Class 3 DSC, e-Office, Indian Evidence Act Section 65B)
    4. Government Cloud (GI Cloud / MeghRaj, MeitY empanelment, STQC audits, data sovereignty)
    5. Digital Public Infrastructure (DPI / India Stack, Aadhaar e-KYC, DigiLocker, PFMS DBT, API Setu)
    """
    course_title = "Digital Governance, Cyber Defense & Public Digital Architecture"
    existing_course = db.query(Course).filter(Course.title == course_title).first()
    if existing_course:
        return

    print(f"Seeding official curriculum: '{course_title}'...")

    # 1. Ensure Department exists
    dept = db.query(Department).filter(Department.name.ilike("%National e-Governance Division%")).first()
    if not dept:
        dept = Department(
            name="National e-Governance Division (NeGD) & CERT-In",
            description="Apex national bodies administering digital governance architecture, India Stack integration, and national cyber incident response under MeitY."
        )
        db.add(dept)
        db.flush()

    # 2. Ensure Skills exist
    gov_skills = [
        ("Critical Infrastructure Cyber Defense & CERT-In Compliance", "Cybersecurity"),
        ("Data Privacy Compliance & DPDP Act 2023", "Data Governance"),
        ("Public Key Infrastructure (PKI) & Digital Signatures", "Digital Governance"),
        ("Government Cloud Architecture & MeghRaj Strategy", "Cloud Computing"),
        ("Digital Public Infrastructure (DPI) & India Stack", "Public Administration")
    ]
    skill_objs = []
    for s_name, s_cat in gov_skills:
        s_obj = db.query(Skill).filter(Skill.name == s_name).first()
        if not s_obj:
            s_obj = Skill(name=s_name, category=s_cat)
            db.add(s_obj)
            db.flush()
        skill_objs.append(s_obj)
    db.commit()

    # 3. Create Course
    course = Course(
        title=course_title,
        overview="Comprehensive capacity-building program for civil servants and public sector administrators on Government of India digital mandates. Covers CERT-In cyber defense directives, the Digital Personal Data Protection Act (DPDP 2023), Public Key Infrastructure (PKI) & eSign in e-Office, MeghRaj (GI Cloud) architecture, and Digital Public Infrastructure (DPI / India Stack).",
        instructor="Dr. Sanjay Bahl (DG, CERT-In) & Smt. Debjani Ghosh, NeGD",
        organization="National e-Governance Division (NeGD) & CERT-In",
        duration_hours=10.0,
        difficulty="intermediate",
        source="internal",
        category="Digital Governance",
        rating=4.96,
        enrolled_count=2450,
        is_popular=True,
        is_new=True
    )
    db.add(course)
    db.flush()

    # Link Course Skills
    for s_obj in skill_objs:
        db.add(CourseSkill(course_id=course.id, skill_id=s_obj.id))
    db.flush()

    # 4. Create 5 Modules with in-depth Lessons and In-Lesson Practice Activities (MCQs)

    # ── MODULE 1: Cybersecurity ──────────────────────────────────────────────
    m1 = Module(
        course_id=course.id,
        title="Module 1: Critical Infrastructure Cyber Defense & CERT-In Directives",
        description="Statutory reporting rules under Section 70B of IT Act 2000, NCIIPC audit framework, and SOC telemetry triage.",
        order=1
    )
    db.add(m1)
    db.flush()

    l1_1 = Lesson(
        module_id=m1.id,
        title="Lesson 1: Statutory Mandate of CERT-In & Mandatory 6-Hour Reporting",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=3Hpd_1O5F9o",
        content="""# Statutory Mandate of CERT-In & Mandatory 6-Hour Incident Reporting

The **Indian Computer Emergency Response Team (CERT-In)** functions under Section 70B of the **Information Technology Act, 2000** as the national nodal agency for responding to computer security incidents.

### Mandatory Directives (Directions of 28 April 2022)
Under the provisions of sub-section (6) of section 70B of the IT Act, CERT-In issued mandatory cybersecurity directions:

1. **6-Hour Mandatory Reporting Window**:
   - Any service provider, intermediary, data center, body corporate, and government organization **must report specified cyber security incidents to CERT-In within six (6) hours** of noticing or being brought to notice of such incidents.
   - Reportable incidents include targeted scanning, compromise of critical systems, unauthorized access to IT systems/data, ransomware outbreaks, and identity theft attacks.

2. **System Clock Synchronization**:
   - All government entities and service providers must connect to the **Network Time Protocol (NTP)** servers of the National Physical Laboratory (NPL) or National Informatics Centre (NIC), or NTP servers traceable to them, to ensure uniform forensic timeline reconstruction.

3. **Mandatory 180-Day Log Retention**:
   - All ICT system logs across all servers, domain controllers, firewalls, and network appliances must be securely maintained within the Indian jurisdiction for a rolling duration of **at least 180 consecutive days**.

> **Crucial Rule for Civil Servants**: Failure to comply with CERT-In directions is punishable under Section 70B(7) of the IT Act with imprisonment up to one year, or with a fine up to one lakh rupees, or both.""",
        activity_question="Under CERT-In directions issued under Section 70B of the IT Act, within what mandatory timeframe must government organizations report cyber security incidents to CERT-In?",
        activity_options_json=json.dumps([
            "Within 6 hours of noticing or being brought to notice of the incident",
            "Within 24 hours of concluding internal departmental forensics",
            "Within 7 working days following public disclosure",
            "At the conclusion of the quarterly audit cycle"
        ]),
        activity_correct_option=0,
        activity_explanation="Under Section 70B(6) directions issued by CERT-In, all government bodies, intermediaries, and enterprises must report specified cyber incidents within six (6) hours of detection.",
        order=1
    )

    l1_2 = Lesson(
        module_id=m1.id,
        title="Lesson 2: SOC Authentication Telemetry & Incident Triage",
        content_type="video",
        duration_minutes=30,
        video_url="https://www.youtube.com/watch?v=v3iUx2SNspY",
        content="""# SOC Authentication Telemetry & Incident Triage

Security Operations Center (SOC) analysts in government infrastructure continuously monitor authentication logs to protect sensitive public portals (such as PFMS, e-Office, and state treasury databases).

### Anatomy of an Authentication Attack
When investigating brute-force and credential-stuffing incidents (such as *Operation NightShift*):
1. **Telemetry Ingestion**: Review Windows Event ID `4625` (Anomalous Logon Failure) and Event ID `4624` (Successful Logon).
2. **Behavioral Spikes**: Hundreds of failed authentication attempts originating from a single external IP address targeting distinct usernames within minutes indicate dictionary brute-forcing.
3. **Breach Pivot**: A subsequent Event `4624` (Logon Type 10 - Remote Interactive / RDP) from that identical IP indicates compromise of administrative credentials.
4. **Post-Exploitation Triage**: Look for immediate execution of Living-off-the-Land Binaries (LOLBins) such as `powershell.exe -enc`, `certutil -urlcache`, or unauthorized user group modifications.

### Incident Containment Protocol
- Immediately isolate the target host at the network switch / VLAN layer.
- **Do not power down the physical server**, as powering down erases volatile RAM containing adversary memory injection artifacts.
- Preserve RAM image and disk forensics under Section 65B of the Indian Evidence Act.""",
        activity_question="During an off-hours security alert on a core government server, multiple rapid failed logins followed by a single successful interactive login from an anomalous external IP indicates which type of incident?",
        activity_options_json=json.dumps([
            "Brute-force credential stuffing followed by unauthorized account compromise",
            "Scheduled automated system backup synchronization",
            "Routine network packet jitter and latency fluctuation",
            "Legitimate remote maintenance by authorized system administrators"
        ]),
        activity_correct_option=0,
        activity_explanation="A burst of failed authentication attempts followed by a successful logon from an untrusted external IP is a classic indicator of brute force or credential stuffing, requiring immediate network isolation and triage.",
        order=2
    )
    db.add_all([l1_1, l1_2])
    db.flush()

    # ── MODULE 2: Data Privacy (DPDP Act 2023) ──────────────────────────────
    m2 = Module(
        course_id=course.id,
        title="Module 2: Data Privacy & Compliance under DPDP Act 2023",
        description="Obligations of Data Fiduciaries, Significant Data Fiduciaries (SDF), citizen consent frameworks, and Data Protection Board of India enforcement.",
        order=2
    )
    db.add(m2)
    db.flush()

    l2_1 = Lesson(
        module_id=m2.id,
        title="Lesson 1: Obligations of Data Fiduciaries & Significant Data Fiduciaries",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=76fcelayw00",
        content="""# Obligations of Data Fiduciaries under the DPDP Act 2023

Enacted in August 2023, the **Digital Personal Data Protection Act, 2023 (DPDP Act)** regulates the processing of digital personal data in India.

### Key Statutory Actors
- **Data Principal**: The citizen to whom the personal data relates.
- **Data Fiduciary**: Any person, ministry, department, or body corporate who determines the purpose and means of processing of personal data.
- **Data Processor**: An entity that processes personal data on behalf of a Data Fiduciary.

### Core Obligations of Government Data Fiduciaries (Section 8)
1. **Reasonable Security Safeguards**: Obligated to implement appropriate technical and organizational measures to prevent personal data breach.
2. **Mandatory Breach Reporting**: In the event of a personal data breach, the Data Fiduciary must give notice of the breach to the **Data Protection Board of India (DPBI)** and to each affected Data Principal.
3. **Purpose Limitation & Data Erasure**: Must erase personal data as soon as the specified purpose is no longer being served and retention is no longer necessary for legal or business purposes.

### Significant Data Fiduciaries (SDF) (Section 10)
Entities designated as SDFs (based on volume, sensitivity, and national security impact) must:
- Appoint a resident **Data Protection Officer (DPO)** who reports directly to the apex executive.
- Appoint an independent **Data Auditor** to evaluate compliance.
- Undertake periodic **Data Protection Impact Assessments (DPIA)**.""",
        activity_question="Under the Digital Personal Data Protection Act 2023 (DPDP), what constitutes a primary statutory obligation of a government department acting as a Data Fiduciary?",
        activity_options_json=json.dumps([
            "Implement reasonable security safeguards to prevent breaches and erase personal data once the specified purpose is fulfilled",
            "Monetize citizen demographic data to commercial third parties to subsidize portal maintenance",
            "Publish unredacted citizen registries and Aadhaar numbers on open public noticeboards",
            "Retain citizen personal records indefinitely without any purpose limitation"
        ]),
        activity_correct_option=0,
        activity_explanation="Under Section 8 of the DPDP Act 2023, a Data Fiduciary must implement reasonable technical and organizational safeguards and erase personal data as soon as the specified purpose is completed.",
        order=1
    )

    l2_2 = Lesson(
        module_id=m2.id,
        title="Lesson 2: Consent Standards, Notice & Citizens' Rights",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=wLlQMNbH7wk",
        content="""# Consent Standards, Notice & Enforcement under DPDP Act 2023

### Standard of Valid Consent (Section 6)
Consent must be:
- **Free, specific, informed, unconditional, and unambiguous**, with a clear affirmative action.
- Accompanied by a pre-consent **Notice** detailing the personal data to be collected, purpose of processing, how to exercise rights, and grievance redressal contact.
- Must be available in English or any of the **22 languages specified in the Eighth Schedule** to the Constitution.

### Rights of Citizens (Data Principals)
1. **Right to Access Information**: Summary of personal data processed and identities of Data Fiduciaries/Processors shared with.
2. **Right to Correction & Erasure**: Right to rectify inaccurate data and erase data no longer required.
3. **Right to Grievance Redressal**: Readily available dispute resolution mechanisms before approaching the Board.
4. **Right to Nominate**: Ability to designate a nominee in the event of death or incapacity.

### Penalties Imposed by the Data Protection Board of India
The Schedule prescribes stringent monetary penalties:
- **Up to ₹250 crore**: For significant failure to take reasonable security safeguards leading to a personal data breach.
- **Up to ₹200 crore**: For failure to notify the Board and affected citizens regarding a personal data breach.
- **Up to ₹200 crore**: For non-fulfillment of additional obligations in relation to processing children's data.""",
        activity_question="What is the maximum penalty that can be levied by the Data Protection Board of India on a Data Fiduciary for failure to implement reasonable security safeguards leading to a significant personal data breach?",
        activity_options_json=json.dumps([
            "Up to ₹250 crore",
            "Up to ₹50 lakh",
            "Up to ₹5 crore",
            "No financial penalty, only an informal administrative reprimand"
        ]),
        activity_correct_option=0,
        activity_explanation="The Schedule to the DPDP Act 2023 empowers the Data Protection Board of India to levy penalties of up to ₹250 crore for failure to take reasonable security safeguards to prevent a personal data breach.",
        order=2
    )
    db.add_all([l2_1, l2_2])
    db.flush()

    # ── MODULE 3: Digital Signatures & PKI ────────────────────────────────────
    m3 = Module(
        course_id=course.id,
        title="Module 3: Public Key Infrastructure (PKI), Digital Signatures & e-Office",
        description="Controller of Certifying Authorities (CCA) standards, cryptographic validity of Class 3 DSC, Aadhaar eSign, and non-repudiation.",
        order=3
    )
    db.add(m3)
    db.flush()

    l3_1 = Lesson(
        module_id=m3.id,
        title="Lesson 1: Cryptographic Foundations of Class 3 DSC & PKI Hierarchy",
        content_type="video",
        duration_minutes=20,
        video_url="https://www.youtube.com/watch?v=yUeI4nqvNs8",
        content="""# Cryptographic Foundations of Class 3 DSC & India's PKI Hierarchy

In official governance, electronic documents and procurement tenders must satisfy the highest levels of authenticity, non-repudiation, and integrity.

### India's PKI Legal Architecture
Under the **Information Technology Act, 2000 (Sections 17–34)**:
1. **Controller of Certifying Authorities (CCA)**: Apex regulatory authority appointed by the Central Government. The CCA operates the **Root Certifying Authority of India (RCAI)**.
2. **Licensed Certifying Authorities (CAs)**: Entities licensed by CCA (such as NICCA, CDAC, eMudhra) that issue Digital Signature Certificates (DSC) to officers.
3. **Class 3 DSC Standards**:
   - Issued on cryptographic FIPS 140-2 Level 2 USB cryptographic hardware tokens.
   - The private key is generated inside the hardware chip and can **never be exported**.
   - Employs asymmetric cryptography (RSA 2048-bit or ECDSA) with SHA-256 hashing.

### Digital Signature Process
1. A cryptographic hash (digest) of the electronic file is computed via SHA-256.
2. The hash is encrypted using the officer's **Private Key** (stored on the DSC token).
3. Any recipient verifies the file using the officer's **Public Key** obtained from the certified CA public registry.
4. If a single character in the document is altered, the decrypted hash does not match, immediately alerting the recipient to tampering.""",
        activity_question="In India's PKI hierarchy established under the IT Act 2000, who operates the National Root CA and regulates all licensed Certifying Authorities (CAs)?",
        activity_options_json=json.dumps([
            "The Controller of Certifying Authorities (CCA)",
            "Local district magistrates and collectors",
            "Individual commercial hardware token manufacturers",
            "Local telecom service providers"
        ]),
        activity_correct_option=0,
        activity_explanation="Under Section 18 of the IT Act 2000, the Controller of Certifying Authorities (CCA) operates the Root Certifying Authority of India (RCAI) and exercises statutory oversight over all licensed Certifying Authorities.",
        order=1
    )

    l3_2 = Lesson(
        module_id=m3.id,
        title="Lesson 2: e-Office Implementation & Non-Repudiation under Section 65B",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=jbBe4AS5pk0",
        content="""# e-Office Implementation & Non-Repudiation under Section 65B

The Government of India's **e-Office** system (developed by NIC) has digitized secretariat files and inter-ministerial correspondence.

### Non-Repudiation in e-Office
Non-repudiation is the assurance that the author of an electronic document or official notation cannot successfully dispute the authenticity of their signature:
- When an Under Secretary or Joint Secretary signs a file notation in e-Office using DSC or **Aadhaar eSign**, an indelible audit trail binds the user ID, timestamp, IP address, and cryptographic signature.
- **Aadhaar eSign (Online Electronic Signature Service)**: Uses Aadhaar biometric or OTP authentication to facilitate legally binding on-demand electronic signing under Second Schedule to the IT Act.

### Admissibility in Courts: Section 65B Certificate
Under **Section 65B of the Indian Evidence Act, 1872** (and corresponding provisions in the Bharatiya Sakshya Adhiniyam):
- Electronic records (emails, server logs, signed e-Office notes) are admissible as primary evidence provided they are accompanied by a **Section 65B Certificate**.
- The certificate must be signed by a person occupying a responsible official position in relation to the operation of the relevant device or management of relevant activities, identifying the electronic record and describing the device's regular operational integrity.""",
        activity_question="Why is an asymmetric cryptographic digital signature or Aadhaar eSign required for official notations in e-Office instead of a scanned handwritten image?",
        activity_options_json=json.dumps([
            "It provides cryptographic non-repudiation and tamper evidence that detects any post-signing alterations",
            "Because image scanners are prohibited in government offices",
            "Because scanned images consume more cloud storage bandwidth",
            "Because image formats cannot be viewed on mobile devices"
        ]),
        activity_correct_option=0,
        activity_explanation="Under Sections 3 and 3A of the IT Act, asymmetric public key cryptography binds the signatory to the document hash, ensuring tamper-evidence and legal non-repudiation in courts of law.",
        order=2
    )
    db.add_all([l3_1, l3_2])
    db.flush()

    # ── MODULE 4: Government Cloud (MeghRaj / GI Cloud) ──────────────────────
    m4 = Module(
        course_id=course.id,
        title="Module 4: Government Cloud Strategy (MeghRaj / GI Cloud) & Sovereignty",
        description="MeitY Cloud adoption guidelines, STQC audit empanelment, sovereign data localization, and tenant isolation.",
        order=4
    )
    db.add(m4)
    db.flush()

    l4_1 = Lesson(
        module_id=m4.id,
        title="Lesson 1: The MeghRaj Architecture & MeitY Empanelment Standards",
        content_type="video",
        duration_minutes=20,
        video_url="https://www.youtube.com/watch?v=BH7SdE0nX5k",
        content="""# The MeghRaj Architecture & MeitY Empanelment Standards

The Government of India launched the **GI Cloud initiative (named "MeghRaj")** to accelerate e-services delivery while optimizing government ICT spending.

### Core Architectural Models under MeghRaj
1. **National Cloud (NIC Cloud)**: Dedicated sovereign cloud infrastructure operated by the National Informatics Centre for critical central and state government workloads.
2. **MeitY Empaneled Commercial Cloud Service Providers (CSPs)**: Certified public cloud providers providing scalable compute, storage, and disaster recovery.
3. **Government Community Cloud (GCC)**: Physically and logically segregated cloud infrastructure dedicated exclusively to Indian government and public sector organizations, guaranteeing zero co-location with commercial private tenants.

### Empanelment Criteria
Before a CSP can host government applications:
- Must undergo rigorous third-party auditing by the **Standardisation Testing and Quality Certification (STQC) Directorate**.
- Must certify adherence to ISO 27001, ISO 27017 (Cloud Security), ISO 27018 (Cloud Privacy), and MeitY SLA terms.""",
        activity_question="Under the Government of India's MeghRaj policy, which national directorate conducts third-party technical security audits before a Cloud Service Provider is empaneled by MeitY?",
        activity_options_json=json.dumps([
            "Standardisation Testing and Quality Certification (STQC) Directorate",
            "Local municipal telecommunications board",
            "International commercial advertising councils",
            "Private unaccredited software vendors"
        ]),
        activity_correct_option=0,
        activity_explanation="MeitY mandates rigorous third-party auditing by the STQC Directorate to verify technical security, physical separation, and SLA compliance before cloud providers can host government data.",
        order=1
    )

    l4_2 = Lesson(
        module_id=m4.id,
        title="Lesson 2: Sovereign Data Localization, Tenant Isolation & Audits",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=70oYrSnRgoI",
        content="""# Sovereign Data Localization, Tenant Isolation & Security Audits

When civil servants architect e-governance systems (such as land records, health registries, or DBT databases) on cloud platforms, national sovereignty principles apply.

### Strict Data Localization Mandate
- **All customer data, transit data, and data at rest must remain strictly within India**.
- **Disaster Recovery (DR) and Near-DR Sites**: All replicated backups and secondary sites must also be located exclusively within the territorial borders of India.
- **Cross-Border Transfer Restrictions**: Indian government data cannot be replicated to foreign jurisdictions or subjected to foreign extra-territorial subpoenas without prior explicit authorization from the Ministry of Electronics & IT.

### Virtual and Physical Isolation Controls
1. **Virtual Private Cloud (VPC)**: Isolated network segments with dedicated subnets, security groups, and access control lists.
2. **Hardware Security Modules (HSM)**: Dedicated FIPS 140-2 Level 3 HSMs for customer-managed encryption keys, ensuring the cloud provider cannot decrypt government databases.
3. **Continuous Auditing**: Regular vulnerability assessments (VAPT) and red teaming conducted by CERT-In empaneled security auditing organizations.""",
        activity_question="What is the mandatory data localization policy for all Indian sovereign government and citizen records hosted on empaneled clouds under MeghRaj?",
        activity_options_json=json.dumps([
            "All primary data, secondary backups, and disaster recovery sites must reside strictly within the territorial boundaries of India",
            "Data can be freely backed up to any foreign data center without notification",
            "Only user passwords must remain in India, citizen data may be exported freely",
            "Backups must be distributed across overseas unverified cloud tenants"
        ]),
        activity_correct_option=0,
        activity_explanation="MeitY's cloud adoption framework strictly mandates that all government data, including replication, logs, and disaster recovery copies, must reside exclusively within the geographic borders of India.",
        order=2
    )
    db.add_all([l4_1, l4_2])
    db.flush()

    # ── MODULE 5: Digital Public Infrastructure (DPI / India Stack) ──────────
    m5 = Module(
        course_id=course.id,
        title="Module 5: Digital Public Infrastructure (DPI) & India Stack Integration",
        description="Aadhaar authentication protocols, DigiLocker gateways, PFMS Direct Benefit Transfer (DBT), and API Setu interoperability.",
        order=5
    )
    db.add(m5)
    db.flush()

    l5_1 = Lesson(
        module_id=m5.id,
        title="Lesson 1: Foundational DPI: Aadhaar Authentication & DigiLocker Gateways",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=YyXAxDD4wuQ",
        content="""# Foundational DPI: Aadhaar Authentication & DigiLocker Gateways

India's **Digital Public Infrastructure (DPI / India Stack)** provides population-scale digital building blocks that enable inclusive public service delivery.

### 1. The Identity Layer: Aadhaar Architecture
- **Aadhaar Authentication API (UIDAI)**: Verifies identity in real-time using biometric (fingerprint/iris/face) or OTP authentication.
- **e-KYC Service**: Secure, paperless electronic Know Your Customer process returning cryptographically signed citizen identity demographic data.
- **Virtual ID (VID) and Aadhaar Masking**: Privacy-preserving mechanisms ensuring the 12-digit physical Aadhaar number is never stored in plain text across departmental databases.

### 2. The Document Layer: DigiLocker Ecosystem
Operated under Rule 9A of the **Information Technology (Preservation and Retention of Information by Intermediaries Providing Digital Locker Facilities) Rules, 2016**:
- Issued documents in DigiLocker are **deemed to be at par with original physical documents**.
- **Issuers**: Public universities, transport departments, CBSE, and tax departments push authenticated machine-readable XML/PDF records directly to a citizen's URI.
- **Requesters**: Government agencies query citizen credentials with citizen consent via secure API, eliminating physical attestation and fraudulent paper certificates.""",
        activity_question="Under Rule 9A of the Information Technology (Digital Locker) Rules, 2016, what is the legal status of digital documents pulled directly through the DigiLocker system?",
        activity_options_json=json.dumps([
            "They are legally deemed to be at par with original physical documents",
            "They are considered invalid hearsay unless re-attested by a gazetted officer on stamp paper",
            "They are only valid for 24 hours from download",
            "They require notarization at a district civil court"
        ]),
        activity_correct_option=0,
        activity_explanation="Rule 9A of the IT Rules 2016 explicitly provides that electronic documents issued into or pulled through DigiLocker shall be treated at par with original physical documents.",
        order=1
    )

    l5_2 = Lesson(
        module_id=m5.id,
        title="Lesson 2: Public Financial Management (PFMS DBT) & API Setu Interoperability",
        content_type="video",
        duration_minutes=25,
        video_url="https://www.youtube.com/watch?v=aL5vxyHzr1w",
        content="""# Public Financial Management (PFMS DBT) & API Setu Interoperability

### Direct Benefit Transfer (DBT) & PFMS
The **Public Financial Management System (PFMS)** administered by the Controller General of Accounts (CGA):
1. **Treasury Single Account (TSA)**: Funds remain in the Consolidated Fund of India until the exact moment of beneficiary release, eliminating parking of idle funds in commercial bank accounts.
2. **Aadhaar Payment Bridge (APB)**: Integrates PFMS with NPCI, routing welfare subsidies directly to the Aadhaar-seeded bank account of the beneficiary.
3. **Public Accounts Verification**: Validates account validity and IFSC formatting prior to disbursement, virtually eliminating ghost beneficiaries and payment leakages.

### API Setu (OpenForge) Data Exchange
**API Setu** serves as the Government of India's national data exchange highway:
- Enables seamless, consent-based, machine-to-machine data exchange between diverse ministries and state departments.
- Standardizes OpenAPI specifications and eliminates duplicate paperwork (e.g., verifying vehicle registration via Vahan API during subsidy verification).""",
        activity_question="How does the Public Financial Management System (PFMS) ensure just-in-time funding and eliminate leakage in Direct Benefit Transfer (DBT) schemes?",
        activity_options_json=json.dumps([
            "Direct electronic fund transfer via the Aadhaar Payment Bridge (APB) to verified beneficiary accounts without intermediary parking",
            "Disbursing physical currency through unverified local agents",
            "Retaining block allocations indefinitely in commercial investment funds",
            "Transferring welfare grants to unauthorized private trusts"
        ]),
        activity_correct_option=0,
        activity_explanation="PFMS integrates directly with the Treasury Single Account and the NPCI Aadhaar Payment Bridge, enabling direct just-in-time transfers into verified citizen bank accounts.",
        order=2
    )
    db.add_all([l5_1, l5_2])
    db.flush()

    # 5. Comprehensive Certification Assessment (15 MCQs across all 5 Domains)
    assessment = Assessment(
        course_id=course.id,
        title="Digital Governance & National Cyber Defense Certification Examination",
        description="Comprehensive official competency examination evaluating mastery across the 5 pillars of Indian digital governance: Cybersecurity & CERT-In Directives, Data Privacy (DPDP Act 2023), Public Key Infrastructure & Digital Signatures, Government Cloud (MeghRaj), and Digital Public Infrastructure (DPI / India Stack).",
        time_limit_minutes=30,
        pass_threshold_percent=70.0
    )
    db.add(assessment)
    db.flush()

    # 15 Detailed Civil-Service Level Questions
    questions_data = [
        # Domain 1: Cybersecurity & CERT-In Directives (Q1, Q2, Q3)
        (
            "Under the mandatory directions issued by CERT-In under Section 70B(6) of the Information Technology Act 2000, within what timeframe must a government ministry or critical intermediary report a confirmed cyber security incident?",
            [
                "Within 6 hours of noticing or being brought to notice of the incident",
                "Within 24 hours of concluding the internal departmental inquiry",
                "Within 72 hours of receiving a formal request from local police",
                "Within 15 days in the monthly security review brief"
            ],
            0,
            "CERT-In directions of 28 April 2022 strictly mandate that all government departments, intermediaries, and enterprises must report specified cyber incidents within six (6) hours of noticing them."
        ),
        (
            "Which national agency is designated under Section 70A of the Information Technology Act 2000 as the National Nodal Agency in respect of Critical Information Infrastructure Protection (CIIP) in India?",
            [
                "National Critical Information Infrastructure Protection Centre (NCIIPC)",
                "National Disaster Management Authority (NDMA)",
                "Telecom Regulatory Authority of India (TRAI)",
                "Press Council of India (PCI)"
            ],
            0,
            "Section 70A of the IT Act 2000 establishes the National Critical Information Infrastructure Protection Centre (NCIIPC) as the designated nodal agency for protecting national critical information infrastructure."
        ),
        (
            "During an investigation of an off-hours security alert on a core government portal, what is the critical reason for avoiding a hard power-down of the compromised server?",
            [
                "Powering down wipes volatile system memory (RAM), destroying crucial in-memory malware artifacts, network sockets, and decryption keys",
                "Powering down triggers an automatic hardware self-destruct mechanism",
                "Powering down cancels the server's cloud subscription immediately",
                "Powering down corrupts the physical power supply cables"
            ],
            0,
            "In forensic triage, live system memory (RAM) contains critical volatile artifacts (injected shellcode, active network connections, injected DLLs). Powering down destroys volatile evidence required under Section 65B of the Evidence Act."
        ),

        # Domain 2: Data Privacy & DPDP Act 2023 (Q4, Q5, Q6)
        (
            "Under the Digital Personal Data Protection Act, 2023 (DPDP Act), what is the statutory status of an Indian government ministry or department that determines the purpose and means of processing citizens' personal data?",
            [
                "Data Fiduciary",
                "Data Principal",
                "Commercial Intermediary",
                "Arbitration Tribunal"
            ],
            0,
            "Under Section 2(i) of the DPDP Act 2023, any entity, department, or company that determines the purpose and means of personal data processing is legally classified as a Data Fiduciary."
        ),
        (
            "What is the maximum monetary penalty that may be levied by the Data Protection Board of India on a Data Fiduciary for significant failure to take reasonable security safeguards to prevent a personal data breach under the DPDP Act 2023?",
            [
                "Up to ₹250 crore",
                "Up to ₹50 lakh",
                "Up to ₹10 crore",
                "A non-monetary formal administrative reprimand"
            ],
            0,
            "The Schedule to the DPDP Act 2023 prescribes financial penalties of up to ₹250 crore for significant failure to implement reasonable security safeguards to prevent personal data breach."
        ),
        (
            "Which mandatory statutory requirement applies exclusively to entities designated as 'Significant Data Fiduciaries' (SDF) under Section 10 of the DPDP Act 2023?",
            [
                "Appoint an India-resident Data Protection Officer (DPO) and conduct periodic Data Protection Impact Assessments (DPIA)",
                "Publish raw citizen biometric databases in open CSV format",
                "Offer all government public services completely free of internet connectivity",
                "Migrate all database servers exclusively to foreign cloud providers"
            ],
            0,
            "Section 10 of the DPDP Act 2023 mandates that Significant Data Fiduciaries must appoint an India-based DPO, retain an independent data auditor, and undertake periodic DPIAs."
        ),

        # Domain 3: Digital Signatures & PKI (Q7, Q8, Q9)
        (
            "Under Section 18 of the Information Technology Act 2000, which apex statutory authority operates the National Root CA (NRCAI) and licenses Certifying Authorities across India?",
            [
                "The Controller of Certifying Authorities (CCA)",
                "The Governor of the Reserve Bank of India",
                "The Ministry of Parliamentary Affairs",
                "The Chief Justice of High Courts"
            ],
            0,
            "The Controller of Certifying Authorities (CCA) operates the Root Certifying Authority of India (RCAI) under the IT Act 2000 and licenses Certifying Authorities like NICCA and CDAC."
        ),
        (
            "In government e-procurement and e-Office file notings, how does an asymmetric cryptographic digital signature (Class 3 DSC) guarantee non-repudiation?",
            [
                "The document hash is encrypted with the signer's secret private key, proving conclusively that only the holder of the token could have signed it",
                "By watermarking the officer's name in red ink on the computer monitor",
                "By locking the computer keyboard for 24 hours following signature generation",
                "By automatically converting the entire document into an uneditable image"
            ],
            0,
            "Under Sections 3 and 3A of the IT Act, asymmetric public key cryptography encrypts the file hash using the private key, binding the signatory to the document and establishing legal non-repudiation."
        ),
        (
            "Under Section 65B of the Indian Evidence Act, what is mandatory for electronic records (such as e-Office files, emails, or server logs) to be admissible as evidence in a court of law?",
            [
                "A signed Certificate under Section 65B identifying the record and certifying the operational integrity of the producing computer system",
                "A verbal endorsement by a private commercial notary",
                "A handwritten physical transcription on judicial stamp paper",
                "A certificate of export issued by an international courier"
            ],
            0,
            "Section 65B mandates that electronic records must be accompanied by an official certificate identifying the electronic record, describing the production device, and affirming regular operations."
        ),

        # Domain 4: Government Cloud / MeghRaj (Q10, Q11, Q12)
        (
            "Under the Government of India's GI Cloud (MeghRaj) adoption guidelines, which mandatory technical audit must a commercial Cloud Service Provider (CSP) complete before empanelment by MeitY?",
            [
                "Third-party security and controls audit conducted by the STQC Directorate",
                "Financial credit evaluation by foreign banking syndicates",
                "Consumer satisfaction survey by digital marketing agencies",
                "Visual website branding inspection by municipal authorities"
            ],
            0,
            "MeitY requires all CSPs seeking empanelment to undergo rigorous technical security, architectural, and isolation audits conducted by the STQC (Standardisation Testing and Quality Certification) Directorate."
        ),
        (
            "What is the Government of India's mandatory policy regarding data localization and replication for sovereign government cloud workloads under MeghRaj?",
            [
                "All customer data, backups, replication streams, and disaster recovery data centers must reside exclusively within the territory of India",
                "Backups may be mirrored to any overseas server without prior notification",
                "Data may reside offshore as long as encryption keys are held on an officer's phone",
                "Disaster recovery sites must be deployed in neutral international waters"
            ],
            0,
            "MeitY's cloud adoption framework mandates that all government data, including replication and disaster recovery copies, must reside strictly within the geographical boundaries of India."
        ),
        (
            "What is the primary architectural differentiator of a Government Community Cloud (GCC) compared to a public cloud deployment under MeghRaj?",
            [
                "GCC ensures dedicated physical and logical segregation exclusively for government entities, with zero co-tenancy with commercial private tenants",
                "GCC provides unlimited free computing hardware to private corporations",
                "GCC operates entirely without internet access or networking cables",
                "GCC allows anonymous citizen logins without authentication"
            ],
            0,
            "A Government Community Cloud (GCC) provides physically or logically isolated infrastructure dedicated exclusively to Indian government entities, preventing co-mingling with commercial tenants."
        ),

        # Domain 5: Digital Public Infrastructure (DPI / India Stack) (Q13, Q14, Q15)
        (
            "Under Rule 9A of the Information Technology (Preservation and Retention of Information by Intermediaries Providing Digital Locker Facilities) Rules, 2016, how are digital certificates pulled via DigiLocker treated?",
            [
                "They are deemed legally at par with original physical documents",
                "They are treated as inadmissible hearsay unless physically notarized",
                "They expire automatically within 48 hours of citizen download",
                "They can only be used for informal non-official communication"
            ],
            0,
            "Rule 9A of the IT Rules 2016 provides that electronic documents issued into or pulled through DigiLocker shall be treated legally at par with original physical documents."
        ),
        (
            "In the context of Direct Benefit Transfer (DBT) administration, what role does the NPCI Aadhaar Payment Bridge (APB) perform within the PFMS ecosystem?",
            [
                "Routes welfare subsidy disbursements directly to the citizen's Aadhaar-seeded bank account without requiring manual entry of account numbers and IFSC",
                "Acts as an unverified peer-to-peer cryptocurrency exchange",
                "Converts central government funds into retail department shopping coupons",
                "Stores unencrypted paper records of citizen welfare transactions"
            ],
            0,
            "The Aadhaar Payment Bridge (APB) administered by NPCI allows welfare departments to credit funds directly using Aadhaar numbers, eliminating payment failures caused by bank merger IFSC changes."
        ),
        (
            "What is the strategic objective of the Government of India's API Setu (OpenForge) platform in public service delivery?",
            [
                "Facilitate standardized, consent-based, machine-to-machine data exchange between diverse departmental applications, eliminating redundant physical document submissions",
                "Charge citizens convenience fees for browsing government websites",
                "Replace civil service officers with automated phone answering systems",
                "Restrict public access to official gazette notifications"
            ],
            0,
            "API Setu serves as the national API exchange highway, enabling real-time, consent-based verification of citizen records (driving licenses, caste certificates, land records) between disparate government systems."
        )
    ]

    for order_idx, (q_text, opts, correct_idx, expl) in enumerate(questions_data, start=1):
        q_obj = Question(
            assessment_id=assessment.id,
            text=q_text,
            options_json=json.dumps(opts),
            correct_option_index=correct_idx,
            explanation=expl,
            order=order_idx
        )
        db.add(q_obj)

    db.commit()
    print("Digital Governance & Cyber Defense curriculum and 15-question examination successfully seeded!")


def seed_cybersec_challenges(db: Session):
    """Seed all 8 procedural CTF challenges into the cyber_sandbox_challenges table."""
    import tempfile
    import base64
    from pathlib import Path
    from app.modules.digital_governance.services.templates import get_template

    challenges_map = [
        ("01-soc-auth-investigation", "01-soc-auth-investigation", False),
        ("03-compromised-linux-server", "03-compromised-linux-server", False),
        ("04-vulnerable-web-app", "04-vulnerable-web-app", False),
        ("05-threat-hunting-lotl", "05-threat-hunting-lotl", False),
        ("06-pki-token-dispute", "06-pki-token-dispute", False),
        ("07-meghraj-cloud-audit", "07-meghraj-cloud-audit", False),
    ]

    for cid, tmpl_key, is_flagship in challenges_map:
        existing = db.query(CyberSandboxChallenge).filter_by(id=cid).first()
        tmpl = get_template(tmpl_key)
        if not tmpl:
            continue

        slots = tmpl.generate_random_slots(seed=f"official_seed_{cid}")
        flag = tmpl.compute_flag(slots)
        hints = tmpl.generate_hints(slots)
        objectives = tmpl.generate_objectives(slots)
        scenario_md = tmpl.generate_scenario_description(slots)

        # 1. Seed or update CyberSandboxTemplate (Human-Designed Template)
        existing_tmpl = db.query(CyberSandboxTemplate).filter_by(id=tmpl_key).first()
        if not existing_tmpl:
            template_record = CyberSandboxTemplate(
                id=tmpl_key,
                title=tmpl.title,
                category=tmpl.category,
                difficulty=tmpl.difficulty,
                competency_id=tmpl.competency_id,
                points=tmpl.base_points,
                duration_minutes=tmpl.duration_minutes,
                tags_json=json.dumps(tmpl.tags),
                mitre_techniques_json=json.dumps(tmpl.mitre_techniques),
                scenario_template=scenario_md,
                instructions_template=scenario_md,
                hints_template_json=json.dumps(hints),
                artifacts_spec_json=json.dumps(list(tmpl.get_slot_schema().keys())),
            )
            db.add(template_record)
            db.flush()
        else:
            existing_tmpl.title = tmpl.title
            existing_tmpl.category = tmpl.category
            existing_tmpl.difficulty = tmpl.difficulty
            existing_tmpl.competency_id = tmpl.competency_id
            existing_tmpl.points = tmpl.base_points
            existing_tmpl.duration_minutes = tmpl.duration_minutes
            existing_tmpl.tags_json = json.dumps(tmpl.tags)
            existing_tmpl.mitre_techniques_json = json.dumps(tmpl.mitre_techniques)
            existing_tmpl.scenario_template = scenario_md
            existing_tmpl.instructions_template = scenario_md
            existing_tmpl.hints_template_json = json.dumps(hints)
            existing_tmpl.artifacts_spec_json = json.dumps(list(tmpl.get_slot_schema().keys()))

        # 2. Seed or update CyberSandboxChallenge (Generated/Concrete Lab Challenge)
        existing = db.query(CyberSandboxChallenge).filter_by(id=cid).first()

        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            data_files = tmpl.synthesize_artifacts(slots, p)
            nb_path = tmpl.generate_notebook(slots, p)

            artifacts = {}
            for fname, fpath in data_files.items():
                if fpath.is_file():
                    try:
                        artifacts[fname] = fpath.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        artifacts[fname] = "base64:" + base64.b64encode(fpath.read_bytes()).decode("ascii")
            nb_code = nb_path.read_text(encoding="utf-8") if nb_path.is_file() else ""

        if existing:
            existing.template_id = tmpl_key
            existing.title = tmpl.title
            existing.category = tmpl.category
            existing.difficulty = tmpl.difficulty
            existing.points = tmpl.base_points
            existing.duration_minutes = tmpl.duration_minutes
            existing.competency_id = tmpl.competency_id
            existing.is_flagship = is_flagship
            existing.tags_json = json.dumps(tmpl.tags)
            existing.mitre_techniques_json = json.dumps(tmpl.mitre_techniques)
            existing.objectives_json = json.dumps(objectives)
            existing.scenario_markdown = scenario_md
            existing.flag = flag
            existing.hints_json = json.dumps(hints)
            existing.artifacts_json = json.dumps(artifacts)
            existing.notebook_code = nb_code
        else:
            challenge = CyberSandboxChallenge(
                id=cid,
                template_id=tmpl_key,
                title=tmpl.title,
                category=tmpl.category,
                difficulty=tmpl.difficulty,
                points=tmpl.base_points,
                duration_minutes=tmpl.duration_minutes,
                competency_id=tmpl.competency_id,
                is_flagship=is_flagship,
                tags_json=json.dumps(tmpl.tags),
                mitre_techniques_json=json.dumps(tmpl.mitre_techniques),
                objectives_json=json.dumps(objectives),
                scenario_markdown=scenario_md,
                flag=flag,
                hints_json=json.dumps(hints),
                artifacts_json=json.dumps(artifacts),
                notebook_code=nb_code,
            )
            db.add(challenge)

    db.commit()
    print(f"All {len(challenges_map)} Cybersecurity Sandbox challenges successfully seeded into database!")

