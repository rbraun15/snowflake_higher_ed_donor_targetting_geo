-- Higher Education Alumni Targeting Demo - Generate Event Venue Data
-- This script generates realistic event venues in the Greenville, SC area

USE DATABASE HIGHER_ED_DEMO;
USE SCHEMA ALUMNI_TARGETING;

-- Create venue data based on real Greenville area locations
INSERT INTO EVENT_VENUES (
    VENUE_ID,
    VENUE_NAME,
    VENUE_TYPE,
    ADDRESS_ID,
    STREET_ADDRESS,
    CITY,
    STATE,
    ZIP_CODE,
    LATITUDE,
    LONGITUDE,
    CAPACITY,
    PRICE_RANGE,
    RATING,
    PHONE,
    WEBSITE,
    DESCRIPTION,
    H3_LEVEL_7,
    H3_LEVEL_8,
    H3_LEVEL_9
)
WITH venue_seed_data AS (
    SELECT * FROM VALUES
    -- Hotels and Event Centers
    ('VENUE_001', 'The Westin Poinsett Greenville', 'Hotel', '100 South Main Street', 'Greenville', 'SC', '29601', 34.8526, -82.3940, 250, '$$$$', 4.2, '(864) 421-9700', 'www.westinpoinsettgreenville.com', 'Historic luxury hotel in downtown Greenville with elegant ballrooms and event spaces.'),
    ('VENUE_002', 'Greenville Convention Center', 'Convention Center', '1 Exposition Avenue', 'Greenville', 'SC', '29607', 34.8794, -82.3606, 1500, '$$$', 4.0, '(864) 233-2562', 'www.greenvilleconventioncenter.com', 'Large convention center perfect for major alumni gatherings and conferences.'),
    ('VENUE_003', 'Hyatt Regency Greenville', 'Hotel', '220 North Main Street', 'Greenville', 'SC', '29601', 34.8544, -82.3936, 300, '$$$', 4.1, '(864) 235-1234', 'www.hyatt.com', 'Modern hotel with sophisticated event spaces overlooking the Reedy River.'),
    ('VENUE_004', 'The Loom Events', 'Event Center', '809 Augusta Street', 'Greenville', 'SC', '29605', 34.8365, -82.3865, 180, '$$', 4.3, '(864) 412-5333', 'www.theloomevents.com', 'Historic textile mill converted into a unique event space with industrial charm.'),
    
    -- Upscale Restaurants
    ('VENUE_005', 'The Lazy Goat', 'Restaurant', '170 River Street', 'Greenville', 'SC', '29601', 34.8520, -82.3972, 120, '$$$', 4.4, '(864) 679-5299', 'www.thelazygoat.com', 'Mediterranean restaurant with stunning river views and private dining options.'),
    ('VENUE_006', 'Halls Chophouse', 'Restaurant', '434 South Main Street', 'Greenville', 'SC', '29601', 34.8487, -82.3939, 200, '$$$$', 4.5, '(864) 298-8160', 'www.hallschophouse.com', 'Premier steakhouse with elegant private dining rooms perfect for alumni events.'),
    ('VENUE_007', 'Soby''s', 'Restaurant', '207 South Main Street', 'Greenville', 'SC', '29601', 34.8508, -82.3940, 150, '$$$', 4.2, '(864) 232-7007', 'www.sobys.com', 'Upscale New South cuisine restaurant with versatile event spaces.'),
    ('VENUE_008', 'Larkin''s Cabaret', 'Restaurant/Entertainment', '310 South Main Street', 'Greenville', 'SC', '29601', 34.8496, -82.3940, 100, '$$', 4.0, '(864) 235-8994', 'www.larkinscabaret.com', 'Jazz club and restaurant offering intimate settings for smaller alumni gatherings.'),
    
    -- Country Clubs and Golf Courses
    ('VENUE_009', 'Greenville Country Club', 'Country Club', '201 Inverness Avenue', 'Greenville', 'SC', '29607', 34.8912, -82.3489, 300, '$$$$', 4.6, '(864) 235-3500', 'www.greenvillecountryclub.com', 'Prestigious country club with championship golf course and elegant clubhouse.'),
    ('VENUE_010', 'Thornblade Club', 'Country Club', '100 Thornblade Way', 'Greer', 'SC', '29650', 34.9487, -82.2876, 250, '$$$$', 4.7, '(864) 848-7874', 'www.thornbladeclub.com', 'Exclusive golf and tennis club with exceptional dining and event facilities.'),
    ('VENUE_011', 'Chanticleer Golf Club', 'Golf Club', '700 Chanticleer Drive', 'Greenville', 'SC', '29607', 34.8756, -82.3212, 200, '$$$', 4.3, '(864) 294-3484', 'www.chanticleergolf.com', 'Scenic golf club with beautiful event spaces overlooking the course.'),
    
    -- Unique Venues
    ('VENUE_012', 'The Peace Center', 'Arts Center', '300 South Main Street', 'Greenville', 'SC', '29601', 34.8493, -82.3942, 400, '$$$', 4.8, '(864) 467-3000', 'www.peacecenter.org', 'Premier performing arts center with elegant spaces for sophisticated alumni events.'),
    ('VENUE_013', 'BMW Zentrum Museum', 'Museum', '1200 Highway 101 South', 'Greer', 'SC', '29651', 34.9023, -82.2145, 300, '$$$', 4.5, '(864) 802-3463', 'www.bmwusfactory.com', 'Modern automotive museum offering unique venues for corporate alumni events.'),
    ('VENUE_014', 'Falls Park Pavilion', 'Outdoor Venue', '601 South Main Street', 'Greenville', 'SC', '29601', 34.8473, -82.3968, 500, '$$', 4.9, '(864) 467-4355', 'www.fallspark.com', 'Beautiful outdoor pavilion in Falls Park perfect for casual alumni gatherings.'),
    ('VENUE_015', 'Campbell''s Covered Bridge', 'Historic Venue', '4000 Campbell Bridge Road', 'Greer', 'SC', '29650', 34.9876, -82.2543, 80, '$$', 4.2, '(864) 848-2000', 'www.campbellsbridge.com', 'Historic covered bridge venue offering rustic charm for intimate alumni events.'),
    
    -- Additional Restaurant Options
    ('VENUE_016', 'High Cotton', 'Restaurant', '550 South Main Street', 'Greenville', 'SC', '29601', 34.8470, -82.3937, 180, '$$$$', 4.3, '(864) 233-7758', 'www.highcotton-restaurant.com', 'Southern fine dining restaurant with private event capabilities.'),
    ('VENUE_017', 'Trappe Door', 'Restaurant', '1001 Boundary Street', 'Greenville', 'SC', '29605', 34.8289, -82.3645, 100, '$$', 4.1, '(864) 451-1742', 'www.trappedoor.com', 'Belgian gastropub with cozy atmosphere perfect for casual alumni meetups.'),
    ('VENUE_018', 'Cielo', 'Restaurant', '1 Augusta Street', 'Greenville', 'SC', '29601', 34.8534, -82.3876, 120, '$$$', 4.0, '(864) 232-3266', 'www.cielogreenville.com', 'Rooftop restaurant with panoramic city views ideal for cocktail receptions.'),
    ('VENUE_019', 'The Barn at Rock Creek', 'Event Venue', '1215 Rock Creek Road', 'Greer', 'SC', '29651', 34.9234, -82.2098, 200, '$$', 4.4, '(864) 877-3500', 'www.barnarockcreek.com', 'Rustic barn venue perfect for casual outdoor alumni events.'),
    ('VENUE_020', 'Furman University', 'University Venue', '3300 Poinsett Highway', 'Greenville', 'SC', '29613', 34.9234, -82.4387, 400, '$$', 4.6, '(864) 294-2000', 'www.furman.edu', 'Beautiful university campus with multiple venues for educational alumni programs.')
    
    AS venue_data (venue_id, venue_name, venue_type, street_address, city, state, zip_code, latitude, longitude, capacity, price_range, rating, phone, website, description)
)
SELECT
    venue_id,
    venue_name,
    venue_type,
    'ADDR_' || venue_id AS address_id,  -- Simulated address ID
    street_address,
    city,
    state,
    zip_code,
    latitude,
    longitude,
    capacity,
    price_range,
    rating,
    phone,
    website,
    description,
    H3_LATLNG_TO_CELL_STRING(latitude, longitude, 7) AS H3_LEVEL_7,
    H3_LATLNG_TO_CELL_STRING(latitude, longitude, 8) AS H3_LEVEL_8,
    H3_LATLNG_TO_CELL_STRING(latitude, longitude, 9) AS H3_LEVEL_9
FROM venue_seed_data; 