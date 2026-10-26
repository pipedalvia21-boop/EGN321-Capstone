BEGIN TRANSACTION;
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    data_file TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'live'
);
INSERT INTO "runs" VALUES(1,'2026-10-26T01:22:28Z','/home/claude/egn321-capstone/growvest_economics/data/tiers_simulated.json','live');
INSERT INTO "runs" VALUES(2,'2026-10-26T01:22:31Z','/home/claude/egn321-capstone/growvest_economics/data/tiers_simulated.json','recovered');
CREATE TABLE tier_results (
    run_id INTEGER NOT NULL REFERENCES runs(id),
    tier TEXT NOT NULL,
    price_usd REAL, payment_fee_usd REAL, gross_margin_usd REAL,
    margin_pct REAL, ltv_usd REAL, cac_payback_months REAL, ltv_to_cac REAL
);
INSERT INTO "tier_results" VALUES(1,'free',0.0,0.0,-0.7,NULL,-4.666666666666667,NULL,-0.3888888888888889);
INSERT INTO "tier_results" VALUES(1,'pro',29.0,1.141,23.159,0.79858620689655169,385.98333333333335,3.6702793730299237,4.5409803921568628);
INSERT INTO "tier_results" VALUES(1,'premium',79.0,2.5909999999999998,65.909,0.83429113924050635,1647.7250000000001,2.4275895552959379,10.29828125);
INSERT INTO "tier_results" VALUES(2,'pro',29.0,1.141,23.159,0.79858620689655169,385.98333333333335,3.6702793730299237,4.5409803921568628);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('runs',2);
COMMIT;