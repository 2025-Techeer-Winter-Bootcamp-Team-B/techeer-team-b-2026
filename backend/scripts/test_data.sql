-- 테스트 아파트 데이터 삽입
INSERT INTO apartments (apt_name, address, sigungu_code, sigungu_name, dong_name, total_units, build_year) VALUES 
('Raemian Gangnam First', 'Seoul Gangnam-gu Yeoksam-dong 123-45', '11680', 'Gangnam-gu', 'Yeoksam-dong', 500, 2020),
('Raemian Seocho STG', 'Seoul Seocho-gu Seocho-dong 234-56', '11650', 'Seocho-gu', 'Seocho-dong', 800, 2019),
('Raemian Songpa Parkview', 'Seoul Songpa-gu Jamsil-dong 345-67', '11710', 'Songpa-gu', 'Jamsil-dong', 1200, 2021),
('Hillstate Gangnam', 'Seoul Gangnam-gu Daechi-dong 456-78', '11680', 'Gangnam-gu', 'Daechi-dong', 600, 2018),
('Xi Seocho', 'Seoul Seocho-gu Banpo-dong 567-89', '11650', 'Seocho-gu', 'Banpo-dong', 450, 2022),
('Prugio Mapo', 'Seoul Mapo-gu Gongdeok-dong 678-90', '11440', 'Mapo-gu', 'Gongdeok-dong', 350, 2017),
('The Sharp Gangdong', 'Seoul Gangdong-gu Cheonho-dong 789-01', '11740', 'Gangdong-gu', 'Cheonho-dong', 700, 2020),
('Acro River Park', 'Seoul Seocho-gu Banpo-dong 111-22', '11650', 'Seocho-gu', 'Banpo-dong', 1500, 2016),
('Banpo Xi', 'Seoul Seocho-gu Banpo-dong 222-33', '11650', 'Seocho-gu', 'Banpo-dong', 2000, 2018),
('Raemian Daechi Palace', 'Seoul Gangnam-gu Daechi-dong 333-44', '11680', 'Gangnam-gu', 'Daechi-dong', 900, 2015)
ON CONFLICT DO NOTHING;

SELECT COUNT(*) as total_count FROM apartments;
