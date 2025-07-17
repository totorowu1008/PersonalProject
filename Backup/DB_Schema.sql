-- -----------------------------------------------------
-- 資料庫 `line_bot_recommend`
-- -----------------------------------------------------
CREATE DATABASE IF NOT EXISTS `line_bot_recommend` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `line_bot_recommend`;

-- -----------------------------------------------------
-- 資料表 `users`
-- 儲存 LINE 使用者的基本資料
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `line_user_id` VARCHAR(50) NOT NULL COMMENT 'LINE 使用者的唯一 ID',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `line_user_id_UNIQUE` (`line_user_id` ASC))
ENGINE = InnoDB
COMMENT = '儲存 LINE 使用者的基本資料';


-- -----------------------------------------------------
-- 資料表 `payment_options`
-- 儲存所有可選的支付工具（信用卡和行動支付）
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `payment_options` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(45) NOT NULL COMMENT '支付工具名稱 (e.g., LINE Pay, 玉山 UBear 卡)',
  `type` ENUM('mobile', 'credit_card') NOT NULL COMMENT '類型：mobile (行動支付), credit_card (信用卡)',
  `open_url` VARCHAR(255) NULL COMMENT '行動支付的開啟連結 (Deeplink)',
  `apply_url` VARCHAR(255) NULL COMMENT '信用卡的申辦連結',
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC))
ENGINE = InnoDB
COMMENT = '所有可選的支付工具';


-- -----------------------------------------------------
-- 資料表 `user_payment_methods`
-- 儲存使用者擁有的支付工具 (多對多關係)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `user_payment_methods` (
  `user_id` INT NOT NULL,
  `payment_option_id` INT NOT NULL,
  PRIMARY KEY (`user_id`, `payment_option_id`),
  INDEX `fk_users_has_payment_options_payment_options1_idx` (`payment_option_id` ASC),
  INDEX `fk_users_has_payment_options_users_idx` (`user_id` ASC),
  CONSTRAINT `fk_users_has_payment_options_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_users_has_payment_options_payment_options1`
    FOREIGN KEY (`payment_option_id`)
    REFERENCES `payment_options` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB
COMMENT = '使用者擁有的支付方式';


-- -----------------------------------------------------
-- 資料表 `transactions`
-- 儲存每一次的消費推薦紀錄
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `transactions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `category` VARCHAR(45) NOT NULL COMMENT '消費類別',
  `amount` INT NOT NULL COMMENT '預估金額',
  `transaction_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消費時間',
  `recommended_options` TEXT NULL COMMENT 'Gemini 推薦的支付選項 (JSON 格式)',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `fk_transactions_users1_idx` (`user_id` ASC),
  CONSTRAINT `fk_transactions_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
COMMENT = '消費推薦紀錄';

-- -----------------------------------------------------
-- 插入預設的支付選項
-- -----------------------------------------------------
INSERT INTO `payment_options` (`name`, `type`, `open_url`, `apply_url`) VALUES
('LINE Pay', 'mobile', 'line://app/1544822146-r13l2pYq', NULL),
('街口支付', 'mobile', 'jkos://', NULL),
('Apple Pay', 'mobile', NULL, NULL),
('Google Pay', 'mobile', NULL, NULL),
('台灣 Pay', 'mobile', 'twmp://', NULL),
('玉山 UBear 卡', 'credit_card', NULL, 'https://www.esunbank.com/zh-tw/personal/credit-card/card/brand-card/u-bear-card'),
('國泰 CUBE 卡', 'credit_card', NULL, 'https://www.cathaybk.com.tw/cathaybk/personal/product/credit-card/cards/cube/'),
('富邦 J 卡', 'credit_card', NULL, 'https://www.fubon.com/banking/personal/credit_card/all_card/omiyage/omiyage.htm'),
('台新 GoGo 卡', 'credit_card', NULL, 'https://www.taishinbank.com.tw/TSB/personal/credit/card/introduction/overview/cg021/'),
('中信 LINE Pay 卡', 'credit_card', NULL, 'https://www.ctbcbank.com/content/dam/product/creditcard/brand/linepay/index.html');

