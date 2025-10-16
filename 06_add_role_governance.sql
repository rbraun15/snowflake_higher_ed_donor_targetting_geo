
--------------------------
--  CREATE ROLE
--------------------------

 
------------------------------------------------------------------
-- Create HE_ADVANCEMENT_INTERN_ROLE, grant permissions, and test the role
------------------------------------------------------------------
SET role_name = 'HE_ADVANCEMENT_INTERN_ROLE';
SET db_name = 'HIGHER_ED_DEMO';
/* other roles
INSTITUTIONAL_RESEARCH_ROLE
FINANCIAL_AID_OFFICER_ROLE
*/

 
use database HIGHER_ED_DEMO;
use role ACCOUNTADMIN;

--Create ACADEMIC_ADVISOR_ROLE role for viewing and contacting students
create or replace role IDENTIFIER($role_name);

-- my user name is admin
grant role IDENTIFIER($role_name) to user admin; 
grant usage on database IDENTIFIER($db_name) to role IDENTIFIER($role_name);
grant usage on schema ALUMNI_TARGETING to ROLE IDENTIFIER($role_name);
grant usage on warehouse XS_WH to ROLE IDENTIFIER($role_name);
grant select on all tables in schema ALUMNI_TARGETING to ROLE IDENTIFIER($role_name);
use role IDENTIFIER($role_name);
select * from ALUMNI_TARGETING.ALUMNI_DONORS limit 5;


--------------------------
-- Create Masking Policies for strings, float numerics, and rounding age
--------------------------
use database HIGHER_ED_DEMO;
use role ACCOUNTADMIN;
create schema security;


-- MASK STRINGS
create or replace masking policy security.mask_string_simple as
  (val string) returns string ->
  case
    when current_role() in ('DATASCI', 'SYSADMIN', 'ACCOUNTADMIN', 'SNOWFLAKE_INTELLIGENCE_ADMIN_RL') then val
      else '**masked**'  -- Masked for all other roles
    end;

-- MASK DATES
 
    CREATE OR REPLACE MASKING POLICY security.mask_date_simple AS (val DATE) RETURNS DATE ->
  CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'DATA_ANALYST', 'SECURITY_ADMIN', 'SNOWFLAKE_INTELLIGENCE_ADMIN_RL') THEN val -- Roles that can see the actual date
    ELSE '9999-12-31'::DATE -- Static date for all other roles
  END;


  -- MASK NUMBERS
create or replace masking policy security.mask_number_simple as
  (val number) returns number ->
  case
    when current_role() in ('DATASCI', 'SYSADMIN', 'ACCOUNTADMIN', 'SNOWFLAKE_INTELLIGENCE_ADMIN_RL') then val
      else '00'  -- Masked for all other roles
    end;


-------------------------
-- Apply Masking Policies for strings, float numerics, and rounding age
-------------------------
alter table HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS modify
column LAST_NAME set masking policy security.mask_string_simple;


alter table HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS modify
column FULL_NAME set masking policy security.mask_string_simple;

alter table HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS modify
column EMAIL set masking policy security.mask_string_simple;


 
ALTER TABLE HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS
MODIFY
    COLUMN AGE SET MASKING POLICY security.mask_number_simple,
    COLUMN ANNUAL_DONATION_AMOUNT SET MASKING POLICY security.mask_number_simple,
    COLUMN CUMULATIVE_DONATION_AMOUNT SET MASKING POLICY security.mask_number_simple;

-------------------------
-- Remove Masking Policies if needed
-------------------------
 
alter table  HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS modify column LAST_NAME unset masking policy;
-- alter table  DEMO_HIGHER_ED.RAW.SIS_STUDENTS modify column ADDRESS_FULL unset masking policy;

alter table  HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS modify column FULL_NAME unset masking policy;
alter table  HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS modify column EMAIL unset masking policy;

 
ALTER TABLE HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS
MODIFY
    COLUMN AGE UNSET MASKING POLICY,
    COLUMN ANNUAL_DONATION_AMOUNT UNSET MASKING POLICY,
    COLUMN CUMULATIVE_DONATION_AMOUNT UNSET MASKING POLICY;




-------------------------
-- Create Row Access Policy
-------------------------
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE ROW ACCESS POLICY PUBLIC.DONOR_LEVEL_ROW_ACCESS_POLICY
AS (major STRING) RETURNS BOOLEAN ->
CASE
    WHEN CURRENT_ROLE() = 'HE_ADVANCEMENT_INTERN_ROLE' THEN major =  'Annual Donor'
    WHEN CURRENT_ROLE() = 'ACADEMIC_ADVISOR_MGR_ROLE' THEN TRUE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN TRUE
    WHEN CURRENT_ROLE() = 'SNOWFLAKE_INTELLIGENCE_ADMIN_RL' THEN TRUE
    ELSE FALSE
END;


-------------------------
-- Apply Row Access Policy
-------------------------
ALTER TABLE HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS
ADD ROW ACCESS POLICY PUBLIC.DONOR_LEVEL_ROW_ACCESS_POLICY ON (DONOR_SEGMENT);

-------------------------
-- DROP Row Access Policy if Necessary
-------------------------
ALTER TABLE HIGHER_ED_DEMO.ALUMNI_TARGETING.ALUMNI_DONORS
DROP ROW ACCESS POLICY PUBLIC.DONOR_LEVEL_ROW_ACCESS_POLICY ;

