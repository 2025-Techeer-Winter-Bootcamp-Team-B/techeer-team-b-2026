CREATE TABLE `FAVORITE_LOCATIONS` (
	`favorite_id`	int	NOT NULL	COMMENT 'PK',
	`account_id`	int	NOT NULL	COMMENT 'FK',
	`region_id`	int	NOT NULL	COMMENT 'FK',
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '소프트 삭제'
);

CREATE TABLE `MY_PROPERTIES` (
	`property_id`	int	NOT NULL	COMMENT 'PK',
	`account_id`	int	NOT NULL	COMMENT 'PK',
	`apt_id`	int	NOT NULL	COMMENT 'PK',
	`nickname`	varchar(50)	NOT NULL	COMMENT '예: 우리집, 투자용',
	`exclusive_area`	decimal(6, 2)	NOT NULL	COMMENT '전용면적 (㎡)',
	`current_market_price`	int	NULL	COMMENT '단위 : 만원',
	`risk_checked_at`	timestamp	NULL,
	`memo`	text	NULL,
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '소프트 삭제'
);

CREATE TABLE `APART_DETAILS` (
	`apt_detail_id`	int	NOT NULL	COMMENT 'PK',
	`apt_id`	int	NOT NULL	COMMENT 'PK',
	`road_address`	varchar(200)	NOT NULL	COMMENT '카카오 API',
	`jibun_address`	varchar(200)	NOT NULL	COMMENT '카카오 API',
	`zip_code`	char(5)	NULL	COMMENT '카카오 API',
	`code_sale_nm`	varchar(20)	NULL	COMMENT '분양/임대 등, 기본정보',
	`code_heat_nm`	varchar(20)	NULL	COMMENT '지역난방/개별난방 등, 기본정보',
	`total_household_cnt`	int	NOT NULL	COMMENT '기본정보',
	`total_building_cnt`	int	NULL	COMMENT '기본정보',
	`highest_floor`	int	NULL	COMMENT '기본정보',
	`use_approval_date`	date	NULL	COMMENT '기본정보',
	`total_parking_cnt`	int	NULL	COMMENT '상세정보',
	`builder_name`	varchar(100)	NULL	COMMENT '상세정보',
	`developer_name`	varchar(100)	NULL	COMMENT '상세정보',
	`manage_type`	varchar(20)	NULL	COMMENT '자치관리/위탁관리 등, 상세정보',
	`hallway_type`	varchar(20)	NULL	COMMENT '계단식/복도식/혼합식, 상세정보',
	`subway_time`	varchar(100)	NULL	COMMENT '상세정보',
	`subway_line`	varchar(100)	NULL	COMMENT '상세정보',
	`subway_station`	varchar(100)	NULL	COMMENT '상세정보',
	`educationFacility`	varchar(100)	NULL	COMMENT '상세정보',
	`geometry`	geometry(Point, 4326)	NULL,
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '소프트 삭제'
);

CREATE TABLE `STATES` (
	`region_id`	int	NOT NULL	COMMENT 'PK',
	`region_name`	varchar(20)	NOT NULL	COMMENT '시군구명 (예: 강남구, 해운대구)',
	`region_code`	char(10)	NOT NULL	COMMENT '시도코드 2자리 + 시군구 3자리 + 동코드 5자리',
	`city_name`	varchar(40)	NOT NULL,
	`created_at`	timestamp	NULL	DEFAULT (CURRENT_TIMESTAMP)	COMMENT '레코드 생성 일시',
	`updated_at`	timestamp	NULL	DEFAULT (CURRENT_TIMESTAMP)	COMMENT '레코드 수정 일시',
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '삭제 여부 (소프트 삭제)'
);

CREATE TABLE `FAVORITE_APARTMENTS` (
	`favorite_id`	int	NOT NULL	COMMENT 'PK',
	`apt_id`	int	NOT NULL	COMMENT 'FK',
	`account_id`	int	NULL	COMMENT 'FK',
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '(소프트 삭제)'
);

CREATE TABLE `SALES` (
	`trans_id`	int	NOT NULL	COMMENT 'PK',
	`apt_id`	int	NOT NULL	COMMENT 'FK',
	`build_year`	VARCHAR(255)	NULL,
	`trans_type`	varchar(10)	NOT NULL,
	`trans_price`	int	NULL,
	`exclusive_area`	decimal(7, 2)	NOT NULL,
	`floor`	int	NOT NULL,
	`building_num`	varchar(10)	NULL,
	`contract_date`	date	NULL,
	`is_canceled`	tinyint(1)	NOT NULL,
	`cancel_date`	date	NULL,
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL
);

CREATE TABLE `HOUSE_SCORES` (
	`index_id`	int	NOT NULL	COMMENT 'PK',
	`region_id`	int	NOT NULL	COMMENT 'FK',
	`base_ym`	char(6)	NOT NULL	COMMENT '해당 하는 달',
	`index_value`	decimal(8, 2)	NOT NULL	COMMENT '2017.11=100 기준',
	`index_change_rate`	decimal(5, 2)	NULL,
	`index_type`	varchar(10)	NOT NULL	DEFAULT 'APT'	COMMENT 'APT=아파트, HOUSE=단독주택, ALL=전체',
	`data_source`	varchar(50)	NOT NULL	DEFAULT 'KB부동산',
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '소프트 삭제'
);

CREATE TABLE `APARTMENTS` (
	`apt_id`	int	NOT NULL	COMMENT 'PK',
	`region_id`	int	NOT NULL	COMMENT 'FK',
	`apt_name`	varchar(100)	NOT NULL	COMMENT '아파트 단지명',
	`kapt_code`	varchar(20)	NOT NULL	COMMENT '국토부 단지코드',
	`is_available`	VARCHAR(255)	NULL	COMMENT 'Default=0, 거래 내역 있으면 1',
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '소프트 삭제'
);

CREATE TABLE `ACCOUNTS` (
	`account_id`	int	NULL	COMMENT 'PK',
	`clerk_user_id`	VARCHAR(255)	NULL,
	`created_at`	timestamp	NULL,
	`email`	VARCHAR(255)	NULL	COMMENT '캐시 저장용',
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL	DEFAULT 0	COMMENT '소프트 삭제',
	`is_admin`	VARCHAR(255)	NULL
);

CREATE TABLE `RENTS` (
	`trans_id`	int	NOT NULL	COMMENT 'PK',
	`apt_id`	int	NOT NULL	COMMENT 'FK',
	`build_year`	VARCHAR(255)	NULL,
	`contract_type`	tinyint(1)	NULL	COMMENT '신규 or 갱신',
	`deposit_price`	int	NULL,
	`monthly_rent`	int	NULL,
	`exclusive_area`	decimal(7, 2)	NOT NULL,
	`floor`	int	NOT NULL,
	`apt_seq`	varchar(10)	NULL,
	`deal_date`	date	NOT NULL,
	`contract_date`	date	NULL,
	`created_at`	timestamp	NULL,
	`updated_at`	timestamp	NULL,
	`is_deleted`	tinyint(1)	NULL
);

ALTER TABLE `FAVORITE_LOCATIONS` ADD CONSTRAINT `PK_FAVORITE_LOCATIONS` PRIMARY KEY (
	`favorite_id`
);

ALTER TABLE `MY_PROPERTIES` ADD CONSTRAINT `PK_MY_PROPERTIES` PRIMARY KEY (
	`property_id`
);

ALTER TABLE `APART_DETAILS` ADD CONSTRAINT `PK_APART_DETAILS` PRIMARY KEY (
	`apt_detail_id`
);

ALTER TABLE `STATES` ADD CONSTRAINT `PK_STATES` PRIMARY KEY (
	`region_id`
);

ALTER TABLE `FAVORITE_APARTMENTS` ADD CONSTRAINT `PK_FAVORITE_APARTMENTS` PRIMARY KEY (
	`favorite_id`
);

ALTER TABLE `SALES` ADD CONSTRAINT `PK_SALES` PRIMARY KEY (
	`trans_id`
);

ALTER TABLE `HOUSE_SCORES` ADD CONSTRAINT `PK_HOUSE_SCORES` PRIMARY KEY (
	`index_id`
);

ALTER TABLE `APARTMENTS` ADD CONSTRAINT `PK_APARTMENTS` PRIMARY KEY (
	`apt_id`
);

ALTER TABLE `ACCOUNTS` ADD CONSTRAINT `PK_ACCOUNTS` PRIMARY KEY (
	`account_id`
);

ALTER TABLE `RENTS` ADD CONSTRAINT `PK_RENTS` PRIMARY KEY (
	`trans_id`
);

