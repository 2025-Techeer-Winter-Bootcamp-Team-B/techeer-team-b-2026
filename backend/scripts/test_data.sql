-- ============================================================
-- 테스트 아파트 데이터 (더미 데이터)
-- DB 설계 및 API 테스트용
-- ============================================================

-- 기존 데이터 삭제 (선택사항)
-- TRUNCATE TABLE apartments RESTART IDENTITY;

-- 서울 주요 아파트 더미 데이터 삽입
INSERT INTO apartments (apt_name, address, sigungu_code, sigungu_name, dong_name, total_units, build_year, latitude, longitude) VALUES 
-- 강남구
('Raemian Gangnam First', 'Seoul Gangnam-gu Yeoksam-dong 123-45', '11680', 'Gangnam-gu', 'Yeoksam-dong', 500, 2020, 37.5012, 127.0396),
('Raemian Daechi Palace', 'Seoul Gangnam-gu Daechi-dong 333-44', '11680', 'Gangnam-gu', 'Daechi-dong', 900, 2015, 37.4947, 127.0635),
('Hillstate Gangnam', 'Seoul Gangnam-gu Daechi-dong 456-78', '11680', 'Gangnam-gu', 'Daechi-dong', 600, 2018, 37.4989, 127.0572),
('Tower Palace', 'Seoul Gangnam-gu Dogok-dong 467', '11680', 'Gangnam-gu', 'Dogok-dong', 2800, 2004, 37.4891, 127.0446),
('Samsung Raemian', 'Seoul Gangnam-gu Samsung-dong 155', '11680', 'Gangnam-gu', 'Samsung-dong', 1200, 2010, 37.5145, 127.0598),

-- 서초구
('Raemian Seocho STG', 'Seoul Seocho-gu Seocho-dong 234-56', '11650', 'Seocho-gu', 'Seocho-dong', 800, 2019, 37.4837, 127.0324),
('Xi Seocho', 'Seoul Seocho-gu Banpo-dong 567-89', '11650', 'Seocho-gu', 'Banpo-dong', 450, 2022, 37.5056, 126.9882),
('Acro River Park', 'Seoul Seocho-gu Banpo-dong 111-22', '11650', 'Seocho-gu', 'Banpo-dong', 1500, 2016, 37.5078, 126.9908),
('Banpo Xi', 'Seoul Seocho-gu Banpo-dong 222-33', '11650', 'Seocho-gu', 'Banpo-dong', 2000, 2018, 37.5034, 126.9925),
('Raemian Firstige', 'Seoul Seocho-gu Banpo-dong 18-2', '11650', 'Seocho-gu', 'Banpo-dong', 1800, 2009, 37.5089, 126.9867),

-- 송파구
('Raemian Songpa Parkview', 'Seoul Songpa-gu Jamsil-dong 345-67', '11710', 'Songpa-gu', 'Jamsil-dong', 1200, 2021, 37.5133, 127.0813),
('Lotte Castle Gold', 'Seoul Songpa-gu Jamsil-dong 40', '11710', 'Songpa-gu', 'Jamsil-dong', 3200, 2008, 37.5112, 127.0845),
('Jamsil Elut', 'Seoul Songpa-gu Jamsil-dong 178', '11710', 'Songpa-gu', 'Jamsil-dong', 2500, 2007, 37.5098, 127.0789),
('Parkrio', 'Seoul Songpa-gu Jamsil-dong 19', '11710', 'Songpa-gu', 'Jamsil-dong', 6800, 2008, 37.5156, 127.0778),
('Heliopolis', 'Seoul Songpa-gu Songpa-dong 123', '11710', 'Songpa-gu', 'Songpa-dong', 1500, 2015, 37.5023, 127.1123),

-- 마포구  
('Prugio Mapo', 'Seoul Mapo-gu Gongdeok-dong 678-90', '11440', 'Mapo-gu', 'Gongdeok-dong', 350, 2017, 37.5445, 126.9512),
('Mapo Raemian Prugio', 'Seoul Mapo-gu Ahyeon-dong 387', '11440', 'Mapo-gu', 'Ahyeon-dong', 4200, 2014, 37.5523, 126.9567),
('Mapo Xi Tower', 'Seoul Mapo-gu Dohwa-dong 168', '11440', 'Mapo-gu', 'Dohwa-dong', 600, 2019, 37.5398, 126.9478),

-- 강동구
('The Sharp Gangdong', 'Seoul Gangdong-gu Cheonho-dong 789-01', '11740', 'Gangdong-gu', 'Cheonho-dong', 700, 2020, 37.5389, 127.1245),
('Gangdong Raemian Firstage', 'Seoul Gangdong-gu Gilldong 45', '11740', 'Gangdong-gu', 'Gil-dong', 1100, 2012, 37.5312, 127.1456),

-- 용산구
('Yongsan Prugio Summit', 'Seoul Yongsan-gu Hannam-dong 810', '11170', 'Yongsan-gu', 'Hannam-dong', 600, 2015, 37.5345, 126.9978),
('Hannam The Hill', 'Seoul Yongsan-gu Hannam-dong 747', '11170', 'Yongsan-gu', 'Hannam-dong', 600, 2011, 37.5378, 127.0023),

-- 성동구
('Acro Seoul Forest', 'Seoul Seongdong-gu Seongsu-dong 656', '11200', 'Seongdong-gu', 'Seongsu-dong', 280, 2020, 37.5456, 127.0456),
('Trimage', 'Seoul Seongdong-gu Seongsu-dong 78', '11200', 'Seongdong-gu', 'Seongsu-dong', 800, 2017, 37.5423, 127.0512),

-- 영등포구
('Yeouido Xi', 'Seoul Yeongdeungpo-gu Yeouido-dong 45', '11560', 'Yeongdeungpo-gu', 'Yeouido-dong', 700, 2018, 37.5234, 126.9234)

ON CONFLICT DO NOTHING;

SELECT COUNT(*) as total_count FROM apartments;
