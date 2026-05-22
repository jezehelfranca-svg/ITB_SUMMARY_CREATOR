// Fallback requirements database for Saudi Petro Rabigh BOTB Project
const REQUIREMENTS_DATA_SAUDI_PETRO_RABIGH_BOTB_PROJECT = {
  "project": "Saudi Petro Rabigh BOTB Project",
  "systems": {
    "DCS": {
      "name": "Distributed Control System (DCS)",
      "spec_no": "To be verified in bid documents",
      "category": "C&I",
      "rules": [
        {
          "file": "2270-8540-80-O002-0003.pdf",
          "page": "1",
          "matched": "fiber optic, analyzer, foc, dcs",
          "context": "FOC | FIBER OPTIC CABLE | FIBER OPTIC PATCH PANEL"
        }
      ],
      "highlights": [
        "Centralized dual-redundant hot-standby controllers (CPU/memory).",
        "Bump-less transfer between CPUs with maximum data loss of 50ms.",
        "All electronic modules/PCBs must have conformal coating for coastal corrosive protection.",
        "GPS time synchronization compatibility (redundant Master-Slave clock).",
        "Sequence of Events (SOE) recording with 1 millisecond resolution.",
        "System logs retention of at least 180 days for audit and incident investigations."
      ]
    },
    "ESD": {
      "name": "Emergency Shutdown System (ESD)",
      "spec_no": "To be verified in bid documents",
      "category": "C&I",
      "rules": [],
      "highlights": [
        "Fail-Safe design: loss of signal/power must not cause a hazard, while minimizing false trips.",
        "SIL level of PLCs, instruments, and solenoid valves determined via HAZOP & SIL study.",
        "Triple or double-sensing devices for binary/analog inputs required for protection of major auxiliaries.",
        "Independent safety PLC processor separate from the process DCS controller."
      ]
    },
    "HMIPIS": {
      "name": "Human-Machine Interface & Plant Information System",
      "spec_no": "To be verified in bid documents",
      "category": "C&I",
      "rules": [],
      "highlights": [
        "Operator Workstations: Minimum 3 OWS and 1 EOWS with dual-Ethernet interface.",
        "Large Video Screens (LVS): Minimum 2 screens with graphics processors in Central Control Room.",
        "Unified/integrated HMI environment for third-party package/OEM controls.",
        "Historian with minimum two months online storage capacity and zooming capability for trends."
      ]
    },
    "FieldInstruments": {
      "name": "Field Instruments & Transmitters",
      "spec_no": "To be verified in bid documents",
      "category": "C&I",
      "rules": [],
      "highlights": [
        "Coastal and highly corrosive environment design (Stainless Steel 316, IP66/NEMA 4X).",
        "Transmitters containing electronic components must have sunshields to protect from direct solar radiation.",
        "Outdoor field enclosures must be minimum IP65; indoor must be IP55.",
        "DP type flow transmitters must have Flow vs DP calibration curves provided."
      ]
    },
    "Analysers": {
      "name": "Online Process Analysers & SWAS",
      "spec_no": "To be verified in bid documents",
      "category": "C&I",
      "rules": [],
      "highlights": [
        "Online CO2 & moisture analysers located at the exit of gas filters.",
        "Analyser shelters: Supplied with 415V AC for HVAC and 110V/240V UPS power for analysers/PLCs.",
        "HVAC system in shelters: Redundant 1 working + 1 standby configuration with chemical air filters.",
        "Shelter safety: Ex-d explosion-proof lighting, fire alarm integration, grounding, and HVAC tripping."
      ]
    },
    "MMS": {
      "name": "Machine Monitoring System (MMS) / Vibration",
      "spec_no": "To be verified in bid documents",
      "category": "C&I",
      "rules": [],
      "highlights": [
        "Vibration and bearing temperature sensors for critical rotating equipment.",
        "All vibration parameters fed to Centralized DCS/PLC and displayed on OWS/LVS.",
        "High-speed processing modules and cards suitable for machinery protection."
      ]
    },
    "FGS": {
      "name": "Fire & Gas System Integration",
      "spec_no": "To be verified in bid documents",
      "category": "C&I",
      "rules": [
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "10",
          "matched": "network switch, fire alarm, fiber optic, ups, cctv, security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | ACS/CCTV server/storage located in the existing CCB over fiber optic cable connectivity. | The Contractor shall provide ACS/CCTV head end equipment which includes but not limited to"
        },
        {
          "file": "2525-8540-80-R591-5967.pdf",
          "page": "1",
          "matched": "fire alarm, foc, fiber optic, ups, access control, cctv, security",
          "context": "FIBER OPTIC CABLE - REDUNDANT | FIBER OPTIC CABLE (PROPOSED) | INDOOR & OUTDOOR CCTV CAMERAS SHALL BE PROVIDED"
        },
        {
          "file": "2525-8540-80-R591-5907.pdf",
          "page": "1",
          "matched": "fire alarm, foc, fiber optic, ups, access control, cctv, security",
          "context": "INDOOR & OUTDOOR CCTV CAMERAS SHALL BE PROVIDED | UPS SYSTEM. | ALL ACS & CCTV EQUIPMENT SHALL BE POWERED THROUGH"
        },
        {
          "file": "2525-8540-80-R591-5908.pdf",
          "page": "1",
          "matched": "fire alarm, foc, fiber optic, ups, access control, cctv, security",
          "context": "INDOOR & OUTDOOR CCTV CAMERAS SHALL BE PROVIDED | UPS SYSTEM. | ALL ACS & CCTV EQUIPMENT SHALL BE POWERED THROUGH"
        },
        {
          "file": "2525-8540-80-R591-5909.pdf",
          "page": "1",
          "matched": "fire alarm, foc, fiber optic, ups, access control, cctv, security",
          "context": "INDOOR & OUTDOOR CCTV CAMERAS SHALL BE PROVIDED | UPS SYSTEM. | ALL ACS & CCTV EQUIPMENT SHALL BE POWERED THROUGH"
        },
        {
          "file": "2525-8540-80-R591-5917.pdf",
          "page": "1",
          "matched": "fire alarm, foc, fiber optic, ups, access control, cctv, security",
          "context": "INDOOR & OUTDOOR CCTV CAMERAS SHALL BE PROVIDED | UPS SYSTEM. | ALL ACS & CCTV EQUIPMENT SHALL BE POWERED THROUGH"
        },
        {
          "file": "2525-8540-80-R591-5918.pdf",
          "page": "1",
          "matched": "fire alarm, foc, fiber optic, ups, access control, cctv, security",
          "context": "INDOOR & OUTDOOR CCTV CAMERAS SHALL BE PROVIDED | UPS SYSTEM. | ALL ACS & CCTV EQUIPMENT SHALL BE POWERED THROUGH"
        }
      ],
      "highlights": [
        "Plant-wide fire detection and coordination system covering smoke, heat, and flame detectors.",
        "Direct hardwired interface with PAGA for automated alarm tones and emergency beacons.",
        "Compliance with statutory regulatory authorities (OISD, PESO, TAC, CEA guidelines).",
        "Interlock logic to trip HVAC fans in control rooms and analyser shelters upon fire detection."
      ]
    },
    "CCTV": {
      "name": "Closed Circuit Television (CCTV) System",
      "spec_no": "To be verified in bid documents",
      "category": "Telecom",
      "rules": [
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "4",
          "matched": "cctv, access control, security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | implementation, and commissioning of the CCTV System and Access Control System scope for the"
        },
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "5",
          "matched": "cctv, access control, security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | Access Control System | CCTV"
        },
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "9",
          "matched": "cctv, access control, security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | CONTRACTOR shall provide a complete ACS and CCTV to facilitate controlled access and indoor / | Access Control system will be designed to support Plant Operations / Security requirements."
        },
        {
          "file": "2525-8540-80-R591-5969.pdf",
          "page": "1",
          "matched": "foc, fiber optic, ups, access control, cctv, security",
          "context": "FOC SM | ACS/CCTV CABINET | INDOOR & OUTDOOR CCTV CAMERAS SHALL BE PROVIDED"
        },
        {
          "file": "2270-8540-80-O002-0013.pdf",
          "page": "1",
          "matched": "telecommunication, foc, fiber optic, ups, telecom, cctv",
          "context": "PROCESS CCTV | EXISTING PROCESS CCTV SYSTEM. | NEW PROCESS CCTV PROVIDED FOR THE BOTB"
        }
      ],
      "highlights": [
        "IP-based high-resolution cameras (minimum 20 cameras: 12 outdoor, 8 indoor).",
        "Ex-proof Ex d / Ex ia housing for hazardous area cameras; IP66/IP67 weather-proof housing.",
        "Video recording history retention: Minimum 2 months (60 days) NVR storage.",
        "Cybersecurity compliance: STQC (MeitY) certification for cameras as per government norms.",
        "Integrated wash and spray installation with permanent service water connection."
      ]
    },
    "PAGA": {
      "name": "Public Address & General Alarm System",
      "spec_no": "To be verified in bid documents",
      "category": "Telecom",
      "rules": [],
      "highlights": [
        "IP-based PAGA system with redundant central controller (MCU) in Centralized Control Room.",
        "Audible output coverage in plant areas designed for +10dB above ambient plant noise.",
        "Hazardous plant area speakers must be flameproof/explosion-proof (Ex-d).",
        "Calling stations: Minimum 3 indoor and 5 outdoor type stations with amplifiers and acoustic hoods."
      ]
    },
    "Telephony": {
      "name": "Plant Telephone & Intercom System",
      "spec_no": "To be verified in bid documents",
      "category": "Telecom",
      "rules": [
        {
          "file": "2270-8540-80-O002-0005.pdf",
          "page": "1",
          "matched": "telecommunication, telephone, foc, fiber optic, ups, telecom",
          "context": "FOC | FIBER OPTIC CABLE | TELECOMMUNICATION ROOM"
        }
      ],
      "highlights": [
        "PABX / IP-based telephone system connecting plant offices, control rooms, and field stations.",
        "Rugged outdoor handsets (IP65/IP66) and flameproof telephones for hazardous areas.",
        "Supports speed dialing, hotline facilities, and system diagnostic alarms."
      ]
    },
    "Network": {
      "name": "Industrial Network & OT Cybersecurity",
      "spec_no": "To be verified in bid documents",
      "category": "Telecom",
      "rules": [
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "1",
          "matched": "security",
          "context": "Security Scope Of Work"
        },
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "2",
          "matched": "security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | PROJECT 213011-01025 - 2525-8540-80-R591-5948: Security Scope Of Work - Bottom of the"
        },
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "3",
          "matched": "security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx"
        },
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "6",
          "matched": "foc, fiber optic, battery, ups, security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | FOC | Fiber Optic Cable"
        },
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "7",
          "matched": "telecommunication, fiber optic, ups, telecom, security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | Execution Requirements for Security Projects | General Requirements of Security Directives"
        },
        {
          "file": "2525-8540-80-R591-5948.pdf",
          "page": "8",
          "matched": "security",
          "context": "2525-8540-80-R591-5948 SECURITY SOW Rev.C0.docx | OVERALL ARCH. SECURITY SYSTEM - SUBSTATIONS AND PIBs | OVERALL NETWORK ARCH. SECURITY SYSTEM - SS AND PIBs"
        }
      ],
      "highlights": [
        "Managed switches with dual-Ethernet and redundant communication paths.",
        "OT Cybersecurity: Compliance with IEC 62443 standards and system hardening.",
        "Demilitarized Zone (DMZ) firewalls and NIDS for secure network isolation.",
        "Remote connectivity restricted to read-only process viewing with secure access control."
      ]
    },
    "Cabling": {
      "name": "Structured Cabling & Fiber Optic System",
      "spec_no": "To be verified in bid documents",
      "category": "Telecom",
      "rules": [
        {
          "file": "2270-8540-80-O002-0002.pdf",
          "page": "1",
          "matched": "telecommunication, foc, fiber optic, ups, telecom",
          "context": "FOC | FIBER OPTIC CABLE | TELECOMMUNICATION ROOM"
        },
        {
          "file": "2270-8540-80-O002-0009.pdf",
          "page": "1",
          "matched": "telecommunication, structured cabling, foc, fiber optic, ups, telecom",
          "context": "FIBER OPTIC CABLE (FOC) | SM FOC DUPLEX | FOC #TBD01,"
        },
        {
          "file": "2270-8540-80-O002-0010.pdf",
          "page": "1",
          "matched": "ups, telecom, foc, fiber optic",
          "context": "UPS POWER | FOC #TBD03, | TELECOM"
        },
        {
          "file": "2270-8540-80-O002-0014.pdf",
          "page": "1",
          "matched": "foc, fiber optic",
          "context": "FOC | FIBER OPTIC CABLE | FIBER OPTIC PATCH PANEL"
        }
      ],
      "highlights": [
        "Single-mode G.652 Fiber Optic Cables (FOC) laid in protective HDPE ducts.",
        "FRP / GRP cable trays and junction boxes suitable for corrosive coastal environment.",
        "Power, control, and instrumentation cables: armoured, fire-resistant, and color-coded (grey/blue)."
      ]
    },
    "UPS": {
      "name": "UPS & DC Power Systems",
      "spec_no": "To be verified in bid documents",
      "category": "Telecom",
      "rules": [],
      "highlights": [
        "Dual-redundant UPS (2 x 100%) with Nickel-Cadmium battery banks, ACDB, and cell boosters.",
        "Backup duration: 3 hours for Simhadri (carbon capture plant) and 2 hours for Pudimadaka C&I systems.",
        "UPS alarm monitoring signals hooked up to Centralized DCS.",
        "DC fuse boxes of 63A rating provided."
      ]
    }
  },
  "challenges": [
    {
      "id": "pdf_tables",
      "title": "Complex PDF Layout & Schema Tables",
      "spec": "2525-8540-80-R591-5948.pdf Page 1",
      "description": "Bidding documents contain complex wiring scheds, camera layout sheets, and PAGA coverage maps in tables. Standard text parsers split cells and lose column alignments.",
      "mitigation": "Reviewer uses visual page coordinate grids and cell boundary maps during PyMuPDF scanning to preserve row association."
    },
    {
      "id": "scattered_requirements",
      "title": "Cross-System Requirement Scattering",
      "spec": "Scattered across 15 files",
      "description": "Cabling requirements are often detailed in civil/electrical files, cyber certifications in PLC/DCS guidelines, and alarm beacons under fire-safety codes, scattering telecom specs.",
      "mitigation": "Run multi-document semantic scanning referencing cable ducts, UPS feeds, and instrument panels back to a master telecom interface chart."
    },
    {
      "id": "cybersecurity_gap",
      "title": "IT/OT Segregation & Cybersecurity Gaps",
      "spec": "2525-8540-80-R591-5948.pdf Page 1",
      "description": "Cybersecurity compliance is mandated, but boundary responsibility between DCS switches, corporate firewalls, and telecom networks is frequently omitted.",
      "mitigation": "Draft explicit network interface boundary matrixes to define clear vendor scopes at DMZ junction interfaces."
    }
  ],
  "tqs": [
    {
      "id": 1,
      "subsystem": "CCTV",
      "docRef": "2525-8540-80-R591-5948.pdf",
      "clause": "Page 10",
      "description": "Specification contains conflicting requirements for CCTV video recording history. Part-A Page 43 mandates 2 months (60 days) minimum storage, whereas Part B references may call for 30 or 90 days. Please clarify the correct video recording history duration.",
      "proposal": "Bidder proposes to design and size the NVR storage capacity for 90 days of continuous recording at 25 fps, 1080p resolution, to ensure compliance with the highest specified standard."
    },
    {
      "id": 2,
      "subsystem": "UPS",
      "docRef": "Electrical & C&I Spec",
      "clause": "UPS sections",
      "description": "UPS battery backup duration has dual references of 2 hours and 3 hours in the specifications. Please clarify.",
      "proposal": "Bidder proposes to provide a uniform 3-hour battery backup for all critical C&I and Telecom UPS systems."
    },
    {
      "id": 3,
      "subsystem": "Network",
      "docRef": "2525-8540-80-R591-5948.pdf",
      "clause": "Page 1",
      "description": "Cybersecurity compliance is mandated, but boundary demarcation firewalls and network interface scopes between Telecom switches and the DCS control systems are not defined.",
      "proposal": "Bidder proposes to configure a demilitarized zone (DMZ) with a managed Level-3 firewall at the interface junction boundary."
    }
  ],
  "workflows": [
    {
      "step": 1,
      "name": "Document Pre-processing & Scope Identification",
      "desc": "Index all PDF volumes using PyMuPDF to extract text and tables. Filter documents containing keywords like 'telecom', 'paga', 'cctv', 'network', 'cables', 'security'."
    },
    {
      "step": 2,
      "name": "Subsystem Requirement Extraction",
      "desc": "Extract and structure requirements for each subsystem: CCTV storage days, camera count, PAGA dB levels, telephone line counts, fiber optic core specifications, and UPS backup times."
    },
    {
      "step": 3,
      "name": "Compliance & Conflict Auditing",
      "desc": "Audit extracted specs against standard rules: check for internal contradictions (e.g., one page asking for 30 days CCTV storage, another asking for 90 days), and cross-reference standards (e.g. IEC 62443, ATEX)."
    },
    {
      "step": 4,
      "name": "Technical Clarification (TQ) Generation",
      "desc": "Automatically compile a list of Technical Queries (TQs) for all vague, conflicting, or missing requirements to submit to the project owner."
    },
    {
      "step": 5,
      "name": "Wiki Dashboard Update",
      "desc": "Export structured wiki data to the master database, updating system architectures, cable schedules, and bill of materials."
    }
  ]
};
