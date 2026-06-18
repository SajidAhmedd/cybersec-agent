// =============================================================================
// CyberSecAgent - Neo4j Initialization Script
// Run this in Neo4j Browser or via cypher-shell
// =============================================================================

// Create constraints
CREATE CONSTRAINT expert_id IF NOT EXISTS FOR (e:Expert) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT cert_name IF NOT EXISTS FOR (c:Certification) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT threat_name IF NOT EXISTS FOR (t:Threat) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT service_name IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (p:Platform) REQUIRE p.name IS UNIQUE;

// Create indexes
CREATE INDEX expert_availability IF NOT EXISTS FOR (e:Expert) ON (e.availability);
CREATE INDEX skill_category IF NOT EXISTS FOR (s:Skill) ON (s.category);

// =============================================================================
// Create Skill Nodes
// =============================================================================

MERGE (s:Skill {name: 'incident_response'})
SET s.category = 'defensive', s.aliases = ['ir', 'breach_response'];

MERGE (s:Skill {name: 'digital_forensics'})
SET s.category = 'defensive', s.aliases = ['forensics', 'dfir'];

MERGE (s:Skill {name: 'malware_analysis'})
SET s.category = 'defensive', s.aliases = ['malware_reverse_engineering'];

MERGE (s:Skill {name: 'mobile_security'})
SET s.category = 'specialty', s.aliases = ['mobile_forensics'];

MERGE (s:Skill {name: 'ios_forensics'})
SET s.category = 'specialty', s.aliases = ['iphone_forensics', 'apple_forensics'];

MERGE (s:Skill {name: 'android_forensics'})
SET s.category = 'specialty', s.aliases = ['android_security'];

MERGE (s:Skill {name: 'cloud_security'})
SET s.category = 'specialty', s.aliases = ['aws_security', 'azure_security'];

MERGE (s:Skill {name: 'penetration_testing'})
SET s.category = 'offensive', s.aliases = ['pentest', 'ethical_hacking'];

MERGE (s:Skill {name: 'security_consulting'})
SET s.category = 'advisory', s.aliases = ['consulting'];

MERGE (s:Skill {name: 'ransomware_response'})
SET s.category = 'specialty', s.aliases = ['ransomware_recovery'];

// =============================================================================
// Create Threat Nodes
// =============================================================================

MERGE (t:Threat {name: 'mobile_compromise'})
SET t.severity = 'HIGH', t.category = 'device';

MERGE (t:Threat {name: 'ransomware'})
SET t.severity = 'CRITICAL', t.category = 'malware';

MERGE (t:Threat {name: 'phishing'})
SET t.severity = 'MEDIUM', t.category = 'social_engineering';

MERGE (t:Threat {name: 'data_breach'})
SET t.severity = 'HIGH', t.category = 'data';

MERGE (t:Threat {name: 'account_compromise'})
SET t.severity = 'HIGH', t.category = 'identity';

MERGE (t:Threat {name: 'malware_infection'})
SET t.severity = 'HIGH', t.category = 'malware';

// =============================================================================
// Create Service Nodes
// =============================================================================

MERGE (s:Service {name: 'incident_response'});
MERGE (s:Service {name: 'forensic_investigation'});
MERGE (s:Service {name: 'security_assessment'});
MERGE (s:Service {name: 'consultation'});
MERGE (s:Service {name: 'recovery_assistance'});

// =============================================================================
// Create Platform Nodes
// =============================================================================

MERGE (p:Platform {name: 'ios'});
MERGE (p:Platform {name: 'android'});
MERGE (p:Platform {name: 'windows'});
MERGE (p:Platform {name: 'macos'});
MERGE (p:Platform {name: 'linux'});
MERGE (p:Platform {name: 'aws'});
MERGE (p:Platform {name: 'azure'});

// =============================================================================
// Create Threat → Skill Relationships
// =============================================================================

MATCH (t:Threat {name: 'mobile_compromise'}), (s:Skill {name: 'mobile_security'})
MERGE (t)-[:REQUIRES {weight: 0.9}]->(s);

MATCH (t:Threat {name: 'mobile_compromise'}), (s:Skill {name: 'ios_forensics'})
MERGE (t)-[:REQUIRES {weight: 0.8}]->(s);

MATCH (t:Threat {name: 'mobile_compromise'}), (s:Skill {name: 'incident_response'})
MERGE (t)-[:REQUIRES {weight: 0.7}]->(s);

MATCH (t:Threat {name: 'ransomware'}), (s:Skill {name: 'ransomware_response'})
MERGE (t)-[:REQUIRES {weight: 0.95}]->(s);

MATCH (t:Threat {name: 'ransomware'}), (s:Skill {name: 'incident_response'})
MERGE (t)-[:REQUIRES {weight: 0.85}]->(s);

MATCH (t:Threat {name: 'ransomware'}), (s:Skill {name: 'malware_analysis'})
MERGE (t)-[:REQUIRES {weight: 0.7}]->(s);

MATCH (t:Threat {name: 'data_breach'}), (s:Skill {name: 'digital_forensics'})
MERGE (t)-[:REQUIRES {weight: 0.9}]->(s);

MATCH (t:Threat {name: 'data_breach'}), (s:Skill {name: 'incident_response'})
MERGE (t)-[:REQUIRES {weight: 0.85}]->(s);

// =============================================================================
// Create Sample Expert Nodes
// =============================================================================

MERGE (e:Expert {id: 1})
SET e.name = 'Priya Sharma',
    e.title = 'Mobile Security Specialist',
    e.location = 'Mumbai, India',
    e.availability = true,
    e.is_active = true,
    e.handles_urgent = true,
    e.rating = 4.9;

MERGE (e:Expert {id: 2})
SET e.name = 'Alex Chen',
    e.title = 'Incident Response Lead',
    e.location = 'San Francisco, USA',
    e.availability = true,
    e.is_active = true,
    e.handles_urgent = true,
    e.rating = 4.8;

MERGE (e:Expert {id: 3})
SET e.name = 'Sarah Johnson',
    e.title = 'Cybersecurity Consultant',
    e.location = 'London, UK',
    e.availability = true,
    e.is_active = true,
    e.handles_urgent = false,
    e.rating = 4.95;

// =============================================================================
// Create Expert → Skill Relationships
// =============================================================================

MATCH (e:Expert {id: 1}), (s:Skill {name: 'mobile_security'})
MERGE (e)-[:HAS_SKILL {weight: 0.95, years: 8}]->(s);

MATCH (e:Expert {id: 1}), (s:Skill {name: 'ios_forensics'})
MERGE (e)-[:HAS_SKILL {weight: 0.9, years: 6}]->(s);

MATCH (e:Expert {id: 1}), (s:Skill {name: 'incident_response'})
MERGE (e)-[:HAS_SKILL {weight: 0.8, years: 5}]->(s);

MATCH (e:Expert {id: 2}), (s:Skill {name: 'incident_response'})
MERGE (e)-[:HAS_SKILL {weight: 0.95, years: 12}]->(s);

MATCH (e:Expert {id: 2}), (s:Skill {name: 'digital_forensics'})
MERGE (e)-[:HAS_SKILL {weight: 0.9, years: 10}]->(s);

MATCH (e:Expert {id: 2}), (s:Skill {name: 'malware_analysis'})
MERGE (e)-[:HAS_SKILL {weight: 0.85, years: 8}]->(s);

MATCH (e:Expert {id: 3}), (s:Skill {name: 'security_consulting'})
MERGE (e)-[:HAS_SKILL {weight: 0.9, years: 6}]->(s);

MATCH (e:Expert {id: 3}), (s:Skill {name: 'incident_response'})
MERGE (e)-[:HAS_SKILL {weight: 0.75, years: 4}]->(s);

// =============================================================================
// Create Expert → Platform Relationships
// =============================================================================

MATCH (e:Expert {id: 1}), (p:Platform {name: 'ios'})
MERGE (e)-[:WORKS_ON {weight: 0.9}]->(p);

MATCH (e:Expert {id: 1}), (p:Platform {name: 'android'})
MERGE (e)-[:WORKS_ON {weight: 0.85}]->(p);

MATCH (e:Expert {id: 2}), (p:Platform {name: 'windows'})
MERGE (e)-[:WORKS_ON {weight: 0.9}]->(p);

MATCH (e:Expert {id: 2}), (p:Platform {name: 'linux'})
MERGE (e)-[:WORKS_ON {weight: 0.85}]->(p);

// =============================================================================
// Create Expert → Service Relationships
// =============================================================================

MATCH (e:Expert {id: 1}), (s:Service {name: 'incident_response'})
MERGE (e)-[:OFFERS {weight: 0.9}]->(s);

MATCH (e:Expert {id: 2}), (s:Service {name: 'incident_response'})
MERGE (e)-[:OFFERS {weight: 0.95}]->(s);

MATCH (e:Expert {id: 2}), (s:Service {name: 'forensic_investigation'})
MERGE (e)-[:OFFERS {weight: 0.9}]->(s);

MATCH (e:Expert {id: 3}), (s:Service {name: 'consultation'})
MERGE (e)-[:OFFERS {weight: 0.9}]->(s);

// Done!
RETURN 'Neo4j graph initialized successfully!' AS status;
