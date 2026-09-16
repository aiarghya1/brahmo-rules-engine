-- ============================================================
-- BRAHMO Rules Engine — Seed Data
-- 1 org | 20 hierarchy levels | 7 users | 50 knowledge nodes | 10 edges
-- Run AFTER schema.sql
-- ============================================================

-- ============================================================
-- Organization
-- ============================================================
INSERT INTO organizations (id, name, segment, config) VALUES
('supra', 'Supra Multi-Specialty Hospital', 'hospital',
 '{"derivability_threshold": 0.7, "max_candidate_set": 50, "token_budget": 4000}');

-- ============================================================
-- 15-Level Hierarchy (DAG structure)
-- ============================================================
INSERT INTO hierarchy_levels (id, org_id, level_number, level_name, department, parent_ids, zone) VALUES
-- Level 1: Hospital Root
('HL-01', 'supra', 1, 'Hospital', NULL, '{}', 1),

-- Level 3: Divisions
('HL-03-CLIN', 'supra', 3, 'Clinical Division', NULL, '{"HL-01"}', 1),
('HL-03-ADMIN', 'supra', 3, 'Administrative Division', NULL, '{"HL-01"}', 1),

-- Level 5: Departments
('HL-05-ORTHO', 'supra', 5, 'Orthopaedics Department', 'ortho', '{"HL-03-CLIN"}', 1),
('HL-05-MED', 'supra', 5, 'General Medicine Department', 'medicine', '{"HL-03-CLIN"}', 1),
('HL-05-CARDIO', 'supra', 5, 'Cardiology Department', 'cardiology', '{"HL-03-CLIN"}', 1),
('HL-05-PAEDS', 'supra', 5, 'Paediatrics Department', 'paediatrics', '{"HL-03-CLIN"}', 1),
('HL-05-SURG', 'supra', 5, 'Surgery Department', 'surgery', '{"HL-03-CLIN"}', 1),
('HL-05-ICU', 'supra', 5, 'ICU Department', 'icu', '{"HL-03-CLIN"}', 1),

-- Level 8: Sub-departments / Specialties
('HL-08-ORTHO-GEN', 'supra', 8, 'Ortho General', 'ortho', '{"HL-05-ORTHO"}', 1),
('HL-08-ORTHO-TKR', 'supra', 8, 'Ortho TKR Unit', 'ortho', '{"HL-05-ORTHO"}', 1),
('HL-08-MED-GEN', 'supra', 8, 'Medicine General', 'medicine', '{"HL-05-MED"}', 1),
('HL-08-CARDIO-CCU', 'supra', 8, 'Cardiac Care Unit', 'cardiology', '{"HL-05-CARDIO"}', 1),

-- Level 10: Wards
('HL-10-ORTHO-W', 'supra', 10, 'Ortho Ward', 'ortho', '{"HL-08-ORTHO-GEN"}', 1),
('HL-10-MED-W', 'supra', 10, 'Medicine Ward', 'medicine', '{"HL-08-MED-GEN"}', 1),
('HL-10-PAEDS-W', 'supra', 10, 'Paediatrics Ward', 'paediatrics', '{"HL-05-PAEDS"}', 1),

-- Level 12: Patient-level (examples)
('HL-12-RAJAN', 'supra', 12, 'Patient: Rajan', 'ortho', '{"HL-10-ORTHO-W"}', 1),
('HL-12-PADMA', 'supra', 12, 'Patient: Padma', 'medicine', '{"HL-10-MED-W"}', 1),

-- Multi-parent example: Post-TKR Protocol belongs to BOTH Ortho and Surgery
('HL-08-POST-TKR', 'supra', 8, 'Post-TKR Protocol Area', 'ortho', '{"HL-05-ORTHO", "HL-05-SURG"}', 1),

-- Zone 2: Global (hospital-wide, bypass BFS but go through 5 checks)
('HL-GLOBAL', 'supra', 3, 'Global Constraints', NULL, '{"HL-01"}', 2);

-- ============================================================
-- 7 Users
-- ============================================================
INSERT INTO users (id, org_id, name, role, department, ceiling_level, write_ceiling, compliance_clearance) VALUES
('U-PRIYA',  'supra', 'Nurse Priya',       'VIEWER',  'ortho',     10, NULL, '{}'),
('U-VIKRAM', 'supra', 'Dr. Vikram (HOD)',   'HOD',     'ortho',      4, 4,    '{}'),
('U-ANANYA', 'supra', 'Dr. Ananya',         'EDITOR',  'medicine',   8, 8,    '{}'),
('U-SHARMA', 'supra', 'Dr. Sharma (HOD)',   'HOD',     'medicine',   4, 4,    '{}'),
('U-RAVI',   'supra', 'Pharmacist Ravi',    'VIEWER',  'pharmacy',  12, NULL, '{}'),
('U-SUNITA', 'supra', 'Dr. Sunita (QA)',    'QUALITY', 'quality',    6, 8,    '{"MNPI"}'),
('U-SURESH', 'supra', 'Admin Suresh',       'ADMIN',   'admin',      1, 1,    '{"MNPI", "PHI", "CONFIDENTIAL"}');

-- ============================================================
-- 50 KNOWLEDGE NODES
-- ============================================================
-- ZONE 2: GLOBAL NODES (10 nodes — injected for ALL users)
-- These bypass BFS but go through all 5 checks
-- ============================================================

INSERT INTO knowledge_nodes (id, org_id, hierarchy_level_id, type, title, content, importance, zone, status, derivability_score, compliance_tags, department) VALUES

('N-G01', 'supra', 'HL-GLOBAL', 'CONSTRAINT', 'Warfarin-NSAID Interaction',
 'CRITICAL: Never prescribe NSAIDs (ibuprofen, aspirin, diclofenac) to patients on Warfarin. Risk of life-threatening GI bleed. Alternative: Paracetamol for pain, PPI cover if anti-inflammatory needed. Supra policy: automatic pharmacy flag on co-prescription.',
 0.98, 2, 'ACTIVE', 0.15, '{}', NULL),

('N-G02', 'supra', 'HL-GLOBAL', 'CONSTRAINT', 'Penicillin Allergy Cross-Reactivity',
 'Patients with documented penicillin allergy: 10% cross-reactivity with 1st-gen cephalosporins, <2% with 3rd-gen. Supra protocol: use azithromycin as first-line alternative. Always check allergy band before ANY antibiotic.',
 0.95, 2, 'ACTIVE', 0.20, '{}', NULL),

('N-G03', 'supra', 'HL-GLOBAL', 'CONSTRAINT', 'Blood Transfusion Two-Person Verification',
 'ALL blood transfusions require two-person verification of patient identity, blood type, and unit number. Single-person verification = protocol violation. Supra incident 2024: near-miss due to single verification.',
 0.97, 2, 'ACTIVE', 0.10, '{}', NULL),

('N-G04', 'supra', 'HL-GLOBAL', 'CONSTRAINT', 'Hand Hygiene 5-Moment Compliance',
 'WHO 5-moment hand hygiene compliance is mandatory. Supra target: 95%. Current: 88%. Alcohol-based handrub at every bed. Non-compliance is a reportable incident.',
 0.90, 2, 'ACTIVE', 0.75, '{}', NULL),

('N-G05', 'supra', 'HL-GLOBAL', 'ANTI_PATTERN', 'Verbal Orders Without Documentation',
 'NEVER accept verbal orders for medication changes without written/electronic confirmation within 1 hour. Supra incident 2023: wrong dose administered due to verbal order mishearing. Exception: cardiac arrest situations only.',
 0.92, 2, 'ACTIVE', 0.12, '{}', NULL),

('N-G06', 'supra', 'HL-GLOBAL', 'CONSTRAINT', 'Patient Identification Two-Identifier Rule',
 'Verify patient identity with TWO identifiers (name + DOB, or name + hospital ID) before any procedure, medication, or blood draw. Wristband check mandatory.',
 0.93, 2, 'ACTIVE', 0.80, '{}', NULL),

('N-G07', 'supra', 'HL-GLOBAL', 'FACT', 'Supra Hospital Emergency Codes',
 'Code Blue: cardiac arrest. Code Red: fire. Code Pink: infant abduction. Code Grey: combative patient. Code Orange: mass casualty. All staff must know codes for their floor.',
 0.70, 2, 'ACTIVE', 0.18, '{}', NULL),

('N-G08', 'supra', 'HL-GLOBAL', 'CONSTRAINT', 'Antibiotic Stewardship 72-Hour Review',
 'All empiric antibiotics must be reviewed at 72 hours. De-escalate based on culture results. Supra policy: pharmacy auto-alerts at 72 hours if no review documented.',
 0.88, 2, 'ACTIVE', 0.25, '{}', NULL),

('N-G09', 'supra', 'HL-GLOBAL', 'CONSTRAINT', 'Fall Risk Assessment on Admission',
 'Every patient assessed for fall risk using Morse Fall Scale on admission and every shift change. Score >= 45: high risk, bed alarm required.',
 0.85, 2, 'ACTIVE', 0.55, '{}', NULL),

('N-G10', 'supra', 'HL-GLOBAL', 'FACT', 'Supra Formulary Preferred Brands',
 'Supra formulary preferred brands: Paracetamol (Calpol/Dolo), Omeprazole (Omez), Amoxicillin (Mox), Metformin (Glycomet). Use formulary brand unless clinical reason documented.',
 0.65, 2, 'ACTIVE', 0.30, '{}', NULL),

-- ============================================================
-- ORTHOPAEDICS NODES (15 nodes — Priya's department)
-- ============================================================

('N-O01', 'supra', 'HL-05-ORTHO', 'CONSTRAINT', 'Post-Op Vitals Monitoring',
 'Post-operative vitals must be recorded every 15 minutes for first 4 hours, then hourly for 24 hours. Supra ortho-specific: include neurovascular check (pulse, sensation, movement) for all limb surgeries.',
 0.94, 1, 'ACTIVE', 0.35, '{}', 'ortho'),

('N-O02', 'supra', 'HL-08-ORTHO-TKR', 'DECISION', 'Paracetamol First-Line Post-TKR',
 'Supra Ortho uses Paracetamol 650mg QDS as first-line post-TKR pain management. Escalation: Tramadol 50mg if VAS > 6. AVOID NSAIDs due to bleeding risk at surgical site. Decision by Dr. Vikram, Jan 2025.',
 0.88, 1, 'ACTIVE', 0.08, '{}', 'ortho'),

('N-O03', 'supra', 'HL-08-ORTHO-TKR', 'ANTI_PATTERN', 'Never Discharge TKR Under 48 Hours',
 'Do NOT discharge TKR patients before 48 hours post-op. Past incident: patient discharged at 36 hours developed DVT at home. Minimum 48 hours with physiotherapy assessment before discharge.',
 0.91, 1, 'ACTIVE', 0.10, '{}', 'ortho'),

('N-O04', 'supra', 'HL-05-ORTHO', 'DECISION', 'Zimmer Implant Preference',
 'Supra Ortho Department uses Zimmer Biomet as preferred TKR implant vendor. Alternative: Smith & Nephew for revision cases only. Decision based on 3-year outcomes review, Dr. Vikram, 2024.',
 0.72, 1, 'ACTIVE', 0.05, '{}', 'ortho'),

('N-O05', 'supra', 'HL-10-ORTHO-W', 'FACT', 'Ortho Ward Bed Capacity',
 'Ortho Ward: 45 beds. 12 post-surgical, 8 traction, 25 general ortho. Usual occupancy: 85-90%. Peak (winter fractures): 100%+, overflow to Medicine Ward.',
 0.50, 1, 'ACTIVE', 0.40, '{}', 'ortho'),

('N-O06', 'supra', 'HL-05-ORTHO', 'CONSTRAINT', 'DVT Prophylaxis Protocol',
 'ALL ortho surgical patients receive DVT prophylaxis: Enoxaparin 40mg SC daily starting 12 hours post-op. Duration: 14 days for TKR, 28 days for THR. Contraindication: active bleeding, platelet <50K.',
 0.93, 1, 'ACTIVE', 0.30, '{}', 'ortho'),

('N-O07', 'supra', 'HL-08-ORTHO-GEN', 'DECISION', 'Fracture X-Ray Protocol',
 'All suspected fractures: minimum 2 views (AP + lateral). Joint involvement: add oblique view. Growth plate involvement in paediatrics: compare with contralateral side. Digital X-ray preferred over CR.',
 0.75, 1, 'ACTIVE', 0.60, '{}', 'ortho'),

('N-O08', 'supra', 'HL-10-ORTHO-W', 'FACT', 'Ortho Ward Nurse-Patient Ratio',
 'Ortho Ward nurse-patient ratio: 1:6 (day), 1:8 (night). Post-surgical first 24 hours: 1:4. ICU-step-down patients: 1:2 until stable.',
 0.55, 1, 'ACTIVE', 0.35, '{}', 'ortho'),

('N-O09', 'supra', 'HL-08-POST-TKR', 'CONSTRAINT', 'Post-TKR Physiotherapy Start',
 'Physiotherapy MUST begin within 24 hours of TKR. Day 1: ankle pumps, static quads. Day 2: CPM machine, assisted standing. Delay beyond 24 hours increases stiffness risk significantly.',
 0.90, 1, 'ACTIVE', 0.20, '{}', 'ortho'),

('N-O10', 'supra', 'HL-05-ORTHO', 'ANTI_PATTERN', 'Weight-Bearing Before X-Ray Confirmation',
 'NEVER allow weight-bearing on a fractured limb before X-ray confirmation of alignment. Past incident: patient with tibial fracture allowed to stand, causing displacement requiring surgery.',
 0.89, 1, 'ACTIVE', 0.15, '{}', 'ortho'),

-- HOD-level Ortho nodes (visible to Vikram L4, NOT to Priya L10)
('N-O11', 'supra', 'HL-05-ORTHO', 'DECISION', 'Ortho Department Budget Allocation 2026',
 'FY 2026 budget: ₹4.2 Cr. Implants: 45%, Staffing: 30%, Equipment: 15%, Training: 10%. New arthroscopy equipment approved Q3. Budget review: Dr. Vikram quarterly.',
 0.70, 1, 'ACTIVE', 0.05, '{"MNPI"}', 'ortho'),

('N-O12', 'supra', 'HL-05-ORTHO', 'DECISION', 'Ortho Vendor Negotiation Strategy',
 'Renegotiate Zimmer contract in July 2026. Target: 12% discount on volume commitment of 200+ implants. Fallback: Smith & Nephew willing to offer 15% below current Zimmer price.',
 0.65, 1, 'ACTIVE', 0.03, '{"MNPI", "CONFIDENTIAL"}', 'ortho'),

-- Patient-level nodes
('N-O13', 'supra', 'HL-12-RAJAN', 'FACT', 'Patient Rajan: Warfarin History',
 'Rajan, 68M. On Warfarin 5mg daily for AF. INR target 2.0-3.0. GI bleed history 2024 (NSAID interaction). STRICTLY NO NSAIDs. Current INR: 2.4 (last checked 3 days ago).',
 0.88, 1, 'ACTIVE', 0.02, '{}', 'ortho'),

('N-O14', 'supra', 'HL-12-RAJAN', 'CONSTRAINT', 'Patient Rajan: Absolute NSAID Contraindication',
 'ABSOLUTE CONTRAINDICATION: No ibuprofen, no aspirin, no diclofenac for patient Rajan. Previous GI bleed 2024 was NSAID-induced while on Warfarin. Use Paracetamol ONLY for pain.',
 0.99, 1, 'ACTIVE', 0.01, '{}', 'ortho'),

('N-O15', 'supra', 'HL-10-ORTHO-W', 'DECISION', 'Ortho Night Shift Handover Protocol',
 'Night shift handover: 15-minute structured handover using SBAR format. Include: pending labs, new admissions past 4 hours, patients for morning surgery, any clinical concerns. Must be documented in ward log.',
 0.72, 1, 'ACTIVE', 0.45, '{}', 'ortho'),

-- ============================================================
-- GENERAL MEDICINE NODES (8 nodes — Ananya's department, NOT Priya's)
-- ============================================================

('N-M01', 'supra', 'HL-05-MED', 'CONSTRAINT', 'Diabetic Fasting Protocol',
 'Supra Medicine: for diabetic patients observing religious fasts — adjust insulin timing, NOT dose. Pre-fast: shift long-acting insulin to evening. During fast: monitor BG q4h. Break fast immediately if BG < 70.',
 0.90, 1, 'ACTIVE', 0.15, '{}', 'medicine'),

('N-M02', 'supra', 'HL-05-MED', 'DECISION', 'Sepsis Protocol v3 2026',
 'Supra Sepsis Bundle v3 (2026): blood cultures before antibiotics, lactate within 1 hour, 30mL/kg crystalloid for hypotension, vasopressors if MAP <65 after fluids. Updated from v2 which had 3-hour lactate window.',
 0.95, 1, 'ACTIVE', 0.25, '{}', 'medicine'),

('N-M03', 'supra', 'HL-08-MED-GEN', 'ANTI_PATTERN', 'Insulin Sliding Scale Alone',
 'Do NOT use insulin sliding scale as sole glycemic management. Past incident: patient with DKA had only sliding scale, no basal insulin — readmitted in 48 hours. Always include basal insulin.',
 0.87, 1, 'ACTIVE', 0.30, '{}', 'medicine'),

('N-M04', 'supra', 'HL-12-PADMA', 'FACT', 'Patient Padma: DM Fasting Patterns',
 'Padma, 62F. Type 2 DM on Metformin 1000mg BD + Glimepiride 2mg. Observes Ekadashi fasting (twice monthly). Adjusted protocol: skip Glimepiride on fast days, continue Metformin with evening meal.',
 0.82, 1, 'ACTIVE', 0.02, '{}', 'medicine'),

('N-M05', 'supra', 'HL-10-MED-W', 'DECISION', 'Medicine Ward IV Antibiotic Audit',
 'Weekly IV antibiotic audit by pharmacy team. Target: 80% appropriate prescribing. Current: 74%. Common errors: not stepping down to oral at 48-72 hours when clinically stable.',
 0.68, 1, 'ACTIVE', 0.20, '{}', 'medicine'),

('N-M06', 'supra', 'HL-05-MED', 'CONSTRAINT', 'Contrast Allergy Pre-Treatment',
 'Patients with documented contrast allergy: pre-treat with Hydrocortisone 200mg IV + Chlorpheniramine 10mg IV, 1 hour before procedure. Alternative imaging (MRI/ultrasound) preferred when feasible.',
 0.88, 1, 'ACTIVE', 0.35, '{}', 'medicine'),

('N-M07', 'supra', 'HL-05-MED', 'FACT', 'Medicine Department Specialty Clinics',
 'Medicine outpatient specialty clinics: DM clinic (Mon/Wed), Hypertension clinic (Tue/Thu), Respiratory clinic (Fri). Each clinic: 2 consultants, 1 registrar, 1 nurse.',
 0.45, 1, 'ACTIVE', 0.50, '{}', 'medicine'),

('N-M08', 'supra', 'HL-05-MED', 'DECISION', 'Sepsis Protocol v2 2024 (SUPERSEDED)',
 'OLD: Supra Sepsis Bundle v2 (2024): blood cultures before antibiotics, lactate within 3 hours. SUPERSEDED by v3 (2026) which tightened lactate window to 1 hour.',
 0.95, 1, 'SUPERSEDED', 0.25, '{}', 'medicine'),

-- ============================================================
-- CARDIOLOGY NODES (5 nodes — NOT reachable by Ortho users)
-- ============================================================

('N-C01', 'supra', 'HL-05-CARDIO', 'CONSTRAINT', 'Cardiac Catheterization Consent',
 'Written informed consent required minimum 4 hours before cardiac catheterization. Consent must include: procedure risks (0.1% mortality, 1% vascular complication), alternatives, and expected outcomes.',
 0.92, 1, 'ACTIVE', 0.30, '{}', 'cardiology'),

('N-C02', 'supra', 'HL-08-CARDIO-CCU', 'DECISION', 'CCU Troponin Protocol',
 'Serial troponin at 0, 3, 6 hours for STEMI rule-out. High-sensitivity troponin: if 0h < 5 ng/L AND no risk factors → early rule-out at 1 hour. Supra uses Abbott hs-cTnI assay.',
 0.90, 1, 'ACTIVE', 0.35, '{}', 'cardiology'),

('N-C03', 'supra', 'HL-05-CARDIO', 'ANTI_PATTERN', 'Discharge Without ECHO After First MI',
 'NEVER discharge a first MI patient without echocardiography. Past incident: patient discharged after NSTEMI without ECHO, returned in 2 weeks with CHF. Ejection fraction was 30%.',
 0.93, 1, 'ACTIVE', 0.15, '{}', 'cardiology'),

('N-C04', 'supra', 'HL-05-CARDIO', 'FACT', 'Cardiology Research Trial: ATOM-2026',
 'Ongoing trial: ATOM-2026 (Atorvastatin Optimization in MI). 50 patients enrolled. Comparing 40mg vs 80mg post-MI. PI: Dr. Mehta. IRB approved March 2026. CONFIDENTIAL until publication.',
 0.60, 1, 'ACTIVE', 0.05, '{"MNPI", "CONFIDENTIAL"}', 'cardiology'),

('N-C05', 'supra', 'HL-05-CARDIO', 'DECISION', 'Dual Antiplatelet Duration Post-Stent',
 'Supra Cardiology: DAPT (Aspirin + Clopidogrel/Ticagrelor) for 12 months post-DES. High bleeding risk: consider 6 months. Ultra-high ischemic risk: extend to 36 months. Decision documented per patient.',
 0.87, 1, 'ACTIVE', 0.40, '{}', 'cardiology'),

-- ============================================================
-- PAEDIATRICS NODES (3 nodes)
-- ============================================================

('N-P01', 'supra', 'HL-05-PAEDS', 'CONSTRAINT', 'Paediatric Drug Dose Weight-Based',
 'ALL paediatric drug doses must be weight-based (mg/kg). NEVER use adult fixed doses for children. Supra policy: weight documented on EVERY drug chart. Pharmacy double-checks paediatric prescriptions.',
 0.96, 1, 'ACTIVE', 0.50, '{}', 'paediatrics'),

('N-P02', 'supra', 'HL-10-PAEDS-W', 'DECISION', 'Paeds Ward Visiting Hours Extension',
 'Paeds Ward: parents allowed 24/7 (no visiting hour restriction). One parent can stay overnight. This policy improved parent satisfaction from 72% to 94% and reduced child anxiety scores.',
 0.60, 1, 'ACTIVE', 0.15, '{}', 'paediatrics'),

('N-P03', 'supra', 'HL-05-PAEDS', 'ANTI_PATTERN', 'Penicillin in Known Allergy Child',
 'CRITICAL: Patient Aadhya (3.5F) has documented penicillin allergy (anaphylaxis at 18 months). DO NOT prescribe amoxicillin, ampicillin, or any penicillin-class antibiotic. Use azithromycin.',
 0.99, 1, 'ACTIVE', 0.05, '{}', 'paediatrics'),

-- ============================================================
-- HOSPITAL-WIDE ADMIN NODES (4 nodes — visible only to ADMIN L1)
-- ============================================================

('N-A01', 'supra', 'HL-01', 'DECISION', 'Hospital Expansion Plan 2026-2028',
 'Board-approved: 80 additional beds by Q4 2027. New Oncology wing (40 beds), ICU expansion (20 beds), Ortho upgrade (20 beds). Total investment: ₹85 Cr. Contractor: L&T. STRICTLY CONFIDENTIAL.',
 0.80, 1, 'ACTIVE', 0.02, '{"MNPI", "CONFIDENTIAL"}', NULL),

('N-A02', 'supra', 'HL-01', 'DECISION', 'Staff Salary Restructuring 2026',
 'HR approved: 12% salary increase for nurses (effective July 2026), 8% for technicians. Consultant revision: performance-linked component increased from 15% to 25%. Board resolution #2026-014.',
 0.75, 1, 'ACTIVE', 0.01, '{"MNPI", "CONFIDENTIAL"}', NULL),

('N-A03', 'supra', 'HL-03-ADMIN', 'FACT', 'Hospital Accreditation Status',
 'NABH accreditation: valid until March 2027. Next assessment: October 2026. Gap areas: medication error reporting (82% vs 95% target), hand hygiene compliance (88% vs 95% target).',
 0.70, 1, 'ACTIVE', 0.20, '{}', NULL),

('N-A04', 'supra', 'HL-01', 'CONSTRAINT', 'Legal Case: Rajan Medico-Legal Hold',
 'LEGAL HOLD: All records related to patient Rajan (2024 GI bleed incident) are under medico-legal hold. NO modification, NO deletion, NO status change. Case: Rajan vs Supra, High Court Hyderabad.',
 0.95, 1, 'LEGAL_HOLD', 0.01, '{"CONFIDENTIAL"}', NULL),

-- ============================================================
-- HIGH-DERIVABILITY NODES (5 nodes — should be EXCLUDED by Check 5)
-- These contain knowledge the AI already has from training
-- ============================================================

('N-D01', 'supra', 'HL-05-ORTHO', 'FACT', 'What is a Total Knee Replacement',
 'Total knee replacement (TKR) is a surgical procedure where damaged knee joint surfaces are replaced with artificial components. Also called total knee arthroplasty (TKA).',
 0.40, 1, 'ACTIVE', 0.92, '{}', 'ortho'),

('N-D02', 'supra', 'HL-05-MED', 'FACT', 'Paracetamol Mechanism of Action',
 'Paracetamol (acetaminophen) is an analgesic and antipyretic. Mechanism: inhibits prostaglandin synthesis in the CNS. Standard adult dose: 500-1000mg every 4-6 hours, max 4g/day.',
 0.35, 1, 'ACTIVE', 0.95, '{}', 'medicine'),

('N-D03', 'supra', 'HL-GLOBAL', 'FACT', 'Normal Vital Sign Ranges Adult',
 'Normal adult vital signs: HR 60-100 bpm, BP 120/80 mmHg (normal), RR 12-20/min, SpO2 >95%, Temp 36.1-37.2°C. Variations normal for age, activity, and medication.',
 0.30, 1, 'ACTIVE', 0.98, '{}', NULL),

('N-D04', 'supra', 'HL-05-ORTHO', 'FACT', 'What is Deep Vein Thrombosis',
 'Deep vein thrombosis (DVT) is a blood clot in a deep vein, usually in the legs. Risk factors: surgery, immobility, cancer, pregnancy. Symptoms: leg swelling, pain, warmth.',
 0.35, 1, 'ACTIVE', 0.93, '{}', 'ortho'),

('N-D05', 'supra', 'HL-05-MED', 'FACT', 'What is Type 2 Diabetes Mellitus',
 'Type 2 diabetes mellitus is a chronic condition where the body becomes resistant to insulin or does not produce enough insulin. Most common form of diabetes. Risk factors: obesity, sedentary lifestyle, family history.',
 0.30, 1, 'ACTIVE', 0.96, '{}', 'medicine');

-- ============================================================
-- Typed Edges Between Nodes
-- ============================================================

INSERT INTO edges (source_id, target_id, edge_type) VALUES
-- SUPPORTS relationships
('N-O02', 'N-O01', 'SUPPORTS'),      -- Paracetamol decision supports post-op vitals
('N-O06', 'N-O01', 'SUPPORTS'),      -- DVT prophylaxis supports post-op monitoring
('N-O09', 'N-O03', 'SUPPORTS'),      -- PT start supports no-early-discharge
('N-G01', 'N-O14', 'SUPPORTS'),      -- Global Warfarin rule supports Rajan constraint

-- DERIVED_FROM relationships
('N-O03', 'N-O01', 'DERIVED_FROM'),  -- TKR discharge rule derived from post-op protocol
('N-O14', 'N-G01', 'DERIVED_FROM'),  -- Rajan NSAID ban derived from global Warfarin rule
('N-M02', 'N-M08', 'SUPERSEDES'),    -- Sepsis v3 supersedes Sepsis v2

-- CONTRADICTS
('N-D01', 'N-O02', 'SUPPORTS'),      -- Generic TKR info supports specific Supra TKR decision

-- REQUIRES
('N-O02', 'N-O06', 'REQUIRES'),      -- Paracetamol protocol requires DVT prophylaxis in place
('N-C02', 'N-C01', 'REQUIRES');      -- Troponin protocol requires cath consent process

-- ============================================================
-- Verification
-- ============================================================
-- SELECT COUNT(*) FROM knowledge_nodes;   -- expect 50
-- SELECT COUNT(*) FROM users;             -- expect 7
-- SELECT COUNT(*) FROM hierarchy_levels;  -- expect 20
-- SELECT COUNT(*) FROM edges;             -- expect 10
