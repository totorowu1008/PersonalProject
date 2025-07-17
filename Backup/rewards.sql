-- phpMyAdmin SQL Dump
-- version 4.9.1
-- https://www.phpmyadmin.net/
--
-- 主機： localhost
-- 產生時間： 
-- 伺服器版本： 8.0.17
-- PHP 版本： 7.3.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 資料庫： `rewards`
--

-- --------------------------------------------------------

--
-- 資料表結構 `payment_options`
--

CREATE TABLE `payment_options` (
  `id` int(11) NOT NULL,
  `name` varchar(45) NOT NULL COMMENT '支付工具名稱 (e.g., LINE Pay, 玉山 UBear 卡)',
  `type` enum('mobile','credit_card') NOT NULL COMMENT '類型：mobile (行動支付), credit_card (信用卡)',
  `rank` tinyint(2) NOT NULL,
  `open_url` varchar(255) DEFAULT NULL COMMENT '行動支付的開啟連結 (Deeplink)',
  `apply_url` varchar(255) DEFAULT NULL COMMENT '信用卡的申辦連結'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='所有可選的支付工具';

--
-- 傾印資料表的資料 `payment_options`
--

INSERT INTO `payment_options` (`id`, `name`, `type`, `rank`, `open_url`, `apply_url`) VALUES
(1, 'LINE Pay', 'mobile', 1, 'line://app/1544822146-r13l2pYq', NULL),
(2, '街口支付', 'mobile', 7, 'https://links.jkopay.com/openapp', NULL),
(3, 'Apple Pay', 'mobile', 2, NULL, NULL),
(4, 'Google Pay', 'mobile', 3, NULL, NULL),
(5, '台灣 Pay', 'mobile', 5, 'twmp://', NULL),
(6, '玉山 UBear 卡', 'credit_card', 0, NULL, 'https://www.esunbank.com/zh-tw/personal/credit-card/card/brand-card/u-bear-card'),
(7, '國泰 CUBE 卡', 'credit_card', 0, NULL, 'https://www.cathaybk.com.tw/cathaybk/personal/product/credit-card/cards/cube/'),
(8, '富邦 J 卡', 'credit_card', 0, NULL, 'https://www.fubon.com/banking/personal/credit_card/all_card/omiyage/omiyage.htm'),
(9, '台新 GoGo 卡', 'credit_card', 0, NULL, 'https://www.taishinbank.com.tw/TSB/personal/credit/card/introduction/overview/cg021/'),
(10, '中信 LINE Pay 卡', 'credit_card', 0, NULL, 'https://www.ctbcbank.com/content/dam/product/creditcard/brand/linepay/index.html'),
(11, 'Samsung Pay', 'mobile', 10, '', NULL),
(12, '永豐 大戶 卡', 'credit_card', 0, NULL, ''),
(13, '一卡通Money', 'mobile', 6, '', NULL),
(14, '悠遊付', 'mobile', 9, '', NULL),
(15, '全支付', 'mobile', 8, '', NULL),
(16, 'PX Pay', 'mobile', 4, '', NULL),
(17, 'Pi 拍錢包', 'mobile', 11, '', NULL);

-- --------------------------------------------------------

--
-- 資料表結構 `transactions`
--

CREATE TABLE `transactions` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `category` varchar(45) NOT NULL COMMENT '消費類別',
  `amount` int(11) NOT NULL COMMENT '預估金額',
  `transaction_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消費時間',
  `recommended_options` text COMMENT 'Gemini 推薦的支付選項 (JSON 格式)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='消費推薦紀錄';

--
-- 傾印資料表的資料 `transactions`
--

INSERT INTO `transactions` (`id`, `user_id`, `category`, `amount`, `transaction_time`, `recommended_options`, `created_at`) VALUES
(1, 1, '餐飲', 2500, '2025-07-09 11:45:43', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": []}, \"new_tools_recommendation\": {\"title\": \"若申辦新工具，可考慮：\", \"recommendations\": [{\"name\": \"中信 LINE Pay 卡\", \"reason\": \"一般消費回饋率高，且許多餐廳有LINE Pay合作優惠，2500元消費可享有較高回饋\"}, {\"name\": \"玉山 UBear 卡\", \"reason\": \"指定通路（包含部分餐廳）享有高回饋，若常使用特定餐廳，回饋更佳。需確認是否有合作餐廳\"}, {\"name\": \"富邦 J 卡\", \"reason\": \"一般消費回饋率不錯，且部分通路有額外加碼活動，可留意是否有餐飲相關優惠\"}]}}', '2025-07-09 11:45:43'),
(2, 1, '餐飲', 2500, '2025-07-11 12:29:39', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"reason\": \"餐廳消費若透過街口支付綁定此卡，可觸發數位通路最高 3.8% 回饋，預估消費 2500 元可享約 95 元回饋。\"}, {\"name\": \"街口支付\", \"reason\": \"餐廳普遍接受度高，建議綁定台新GOGO卡以觸發其數位通路高回饋，街口支付本身也可能提供點數或合作店家優惠。\"}, {\"name\": \"玉山UBear卡\", \"reason\": \"餐廳消費可享基本 1% 回饋，作為備用支付工具。\"}]}}', '2025-07-11 12:29:39'),
(3, 1, '餐飲', 2500, '2025-07-11 12:43:16', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": [{\"name\": \"街口支付\", \"reason\": \"街口支付在餐飲通路經常推出專屬優惠活動或滿額折抵，實際回饋可能優於單純信用卡回饋，建議結帳前留意是否有當期活動。\"}, {\"name\": \"玉山UBear卡\", \"reason\": \"一般消費享1%現金回饋無上限，餐飲消費穩定獲得回饋，是您現有卡片中用於餐廳消費較佳的選擇。\"}, {\"name\": \"台新GOGO卡\", \"reason\": \"一般消費享0.5%回饋，雖然對於餐飲通路的回饋率較低，但仍可作為備用支付工具。其高回饋主要集中在指定數位通路消費。\"}]}}', '2025-07-11 12:43:16'),
(4, 1, '餐飲', 2500, '2025-07-11 12:50:28', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": [{\"name\": \"街口支付\", \"reason\": \"餐廳消費類別，街口支付常有合作店家提供額外優惠（如街口幣回饋或折抵），實際回饋率有機會超越信用卡，建議您優先確認欲消費餐廳是否有配合活動。\"}, {\"name\": \"台新GOGO卡\", \"reason\": \"若透過指定行動支付（如街口支付綁定GOGO卡或Apple Pay/Google Pay）消費，GOGO卡可享指定數位通路或行動支付加碼回饋，其回饋率會優於玉山UBear卡的一般消費回饋。\"}, {\"name\": \"玉山UBear卡\", \"reason\": \"玉山UBear卡主要高回饋集中在網購類別，本次餐廳消費屬於一般消費，僅能獲得基本回饋1%，因此排序較後。\"}]}}', '2025-07-11 12:50:28'),
(5, 1, '餐飲', 2500, '2025-07-11 12:54:11', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"reason\": \"綁定指定行動支付（如街口支付）於餐廳消費，可享最高3.8%回饋，是您現有工具中回饋率最高者，非常適合本次餐廳消費。\"}, {\"name\": \"街口支付\", \"reason\": \"在眾多餐廳廣泛被接受，本身提供基本回饋點數，且可作為平台綁定台新GOGO卡以發揮最大效益。若餐廳支援，是便利且有潛力獲得高回饋的支付方式。\"}, {\"name\": \"玉山UBear卡\", \"reason\": \"提供一般消費1%現金回饋，在未能使用其他高回饋方式（如指定行動支付）時，仍能穩定獲得基本回饋，作為備用選項。\"}]}}', '2025-07-11 12:54:11'),
(6, 1, '餐飲', 2500, '2025-07-11 12:56:28', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"reason\": \"綁定街口支付並於餐廳消費，可享最高3.8%回饋（需符合自動扣繳等指定條件），為目前回饋最高的選項。\"}, {\"name\": \"玉山UBear卡\", \"reason\": \"享一般消費1%現金回饋，適用於多數餐廳消費，是穩定且無指定通路限制的回饋選擇。\"}, {\"name\": \"街口支付\", \"reason\": \"在台灣餐廳的普及率高，提供支付便利性。若未綁定高回饋信用卡或有當期合作店家活動，仍是常用的支付方式。\"}]}}', '2025-07-11 12:56:28'),
(7, 1, '餐飲', 2500, '2025-07-12 00:08:31', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"reason\": \"數位/行動支付（如綁定街口支付或Apple Pay/Google Pay）享高達3%回饋，適用於餐廳消費。\"}, {\"name\": \"街口支付\", \"reason\": \"合作餐廳常有獨家優惠或街口幣回饋，且支付便利性高，可綁定台新GOGO卡疊加優惠。\"}, {\"name\": \"玉山UBear卡\", \"reason\": \"一般消費享1%回饋，若餐廳消費不適用於其他高回饋通路，此卡提供穩定基礎回饋。\"}]}}', '2025-07-12 00:08:31'),
(8, 1, '餐飲', 2500, '2025-07-12 00:16:25', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"reason\": \"搭配Apple Pay/Google Pay等行動支付，於餐廳消費享最高3.8%回饋（需符合精選通路與指定支付條件），回饋率高。\"}, {\"name\": \"街口支付\", \"reason\": \"街口支付常有合作餐廳的獨家優惠或綁定指定銀行卡片的加碼回饋（例如綁定特定銀行信用卡），建議消費前可查詢當期活動，有機會獲得高於信用卡一般消費的回饋。\"}, {\"name\": \"玉山UBear卡\", \"reason\": \"若餐廳消費可視為網路購物（例如透過餐廳官網線上訂餐、預付等），有機會享3.8%回饋；若為一般店內刷卡消費，則為1%回饋，仍優於部分卡片。\"}]}}', '2025-07-12 00:16:25'),
(9, 1, '餐飲', 2500, '2025-07-12 00:37:38', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"預估回饋比例\": \"3.8%\", \"預估回饋金\": \"新台幣 95 元\"}, {\"name\": \"玉山UBear卡\", \"預估回饋比例\": \"1%\", \"預估回饋金\": \"新台幣 25 元\"}, {\"name\": \"街口支付\", \"預估回饋比例\": \"1%\", \"預估回饋金\": \"新台幣 25 元\"}]}}', '2025-07-12 00:37:38'),
(10, 1, '餐飲', 2500, '2025-07-12 00:50:11', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡 (行動支付適用)\", \"預估回饋比例\": \"3.5%\", \"預估回饋金\": \"新台幣 87.5 元\"}, {\"name\": \"玉山UBear卡 (一般消費)\", \"預估回饋比例\": \"1%\", \"預估回饋金\": \"新台幣 25 元\"}, {\"name\": \"街口支付 (街口幣回饋)\", \"預估回饋比例\": \"1%\", \"預估回饋金\": \"新台幣 25 元\"}]}}', '2025-07-12 00:50:11'),
(11, 1, '餐飲', 2500, '2025-07-12 00:52:04', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"預估回饋比例\": \"3%\", \"預估回饋金\": \"75 新台幣\"}, {\"name\": \"玉山UBear卡\", \"預估回饋比例\": \"1%\", \"預估回饋金\": \"25 新台幣\"}, {\"name\": \"街口支付\", \"預估回饋比例\": \"0.5%\", \"預估回饋金\": \"13 新台幣\"}]}}', '2025-07-12 00:52:04'),
(12, 1, '餐飲', 2500, '2025-07-12 01:01:30', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡 (綁定街口支付或其他行動支付)\", \"percent\": \"3.5%\", \"cashback\": \"88元\"}, {\"name\": \"玉山UBear卡 (綁定街口支付)\", \"percent\": \"3%\", \"cashback\": \"75元\"}, {\"name\": \"街口支付 (基礎回饋)\", \"percent\": \"1%\", \"cashback\": \"25元\"}]}}', '2025-07-12 01:01:30'),
(13, 1, '餐飲', 3000, '2025-07-12 01:38:40', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"綁定Richart帳戶自動扣繳並登入Richart APP後，透過行動支付（如街口支付、Apple Pay、Google Pay等）於餐廳消費，可享3.8%高額回饋，此筆金額在每月回饋上限內。\"}, {\"name\": \"玉山UBear卡\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"透過指定行動支付（如Apple Pay、Google Pay、LINE Pay等）於餐廳消費，可享3.8%高額回饋，此筆金額在每月回饋上限內。\"}, {\"name\": \"玉山UBear卡\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"若餐廳無法使用行動支付，直接刷卡消費仍可享有基本1%回饋。\"}]}}', '2025-07-12 01:38:40'),
(14, 1, '餐飲', 3000, '2025-07-12 01:47:34', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡 (綁定行動支付)\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"台新GOGO卡於指定數位通路（包含Apple Pay、Google Pay、街口支付等）消費享3.8%回饋（需設定Richart帳戶自動扣繳且使用電子帳單）。若餐廳可使用行動支付，綁定GOGO卡將是最佳選擇，此筆2500元消費在加碼上限內。\"}, {\"name\": \"玉山UBear卡\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"玉山UBear卡一般消費享1%回饋。若餐廳不支援行動支付，或您習慣實體卡刷卡，UBear卡仍可提供基本回饋。\"}, {\"name\": \"街口支付\", \"percent\": \"0.5%\", \"cashback\": \"12.5元\", \"reason\": \"街口支付在許多餐廳普及，若您偏好使用行動支付且未將高回饋信用卡綁定於街口，其仍提供基本街口幣回饋，方便性高。\"}]}}', '2025-07-12 01:47:34'),
(15, 1, '餐飲', 2000, '2025-07-12 01:49:56', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"玉山UBear卡\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"餐廳消費屬於一般消費，可享1%現金回饋，是您現有卡片中最高的。\"}, {\"name\": \"台新GOGO卡\", \"percent\": \"0.5%\", \"cashback\": \"13元\", \"reason\": \"餐廳實體消費可享0.5%基本回饋，作為備用選項。\"}]}}', '2025-07-12 01:49:56'),
(16, 1, '餐飲', 2000, '2025-07-12 01:52:43', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"綁定街口支付並透過其掃碼支付，可享台新GOGO卡數位通路高回饋。需符合Richart帳戶自動扣繳與使用數位帳單等活動條件。\"}, {\"name\": \"玉山UBear卡\", \"percent\": \"1.0%\", \"cashback\": \"25元\", \"reason\": \"若餐廳不支援街口支付或偏好實體刷卡，玉山UBear卡提供一般消費1%回饋。\"}, {\"name\": \"街口支付\", \"percent\": \"0.0%\", \"cashback\": \"0元\", \"reason\": \"若未綁定台新GOGO卡或無街口App特定活動，單獨使用街口支付本身的回饋通常較低或無。建議優先搭配台新GOGO卡使用以獲得最佳回饋。\"}]}}', '2025-07-12 01:52:43'),
(17, 1, '餐飲', 2000, '2025-07-12 01:55:39', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡 (透過街口支付)\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"台新GOGO卡針對指定行動支付（含街口支付）提供3.8%高回饋，建議結帳時詢問店家是否接受街口支付並以此卡付款。\"}, {\"name\": \"玉山UBear卡\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"若餐廳無法使用行動支付，玉山UBear卡提供一般消費1%回饋，作為替代選擇。\"}, {\"name\": \"街口支付\", \"percent\": \"0.5%\", \"cashback\": \"13元\", \"reason\": \"若無合適信用卡可綁定或上述卡片不適用，街口支付本身偶有基礎點數或合作店家優惠，但回饋率通常不高，主要優勢為便利性及特定活動。\"}]}}', '2025-07-12 01:55:39'),
(18, 1, '餐飲', 3000, '2025-07-12 01:59:48', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"玉山 UBear 卡 (搭配街口支付使用)\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"UBear卡於網路消費享3.8%現金回饋（每月上限200元刷卡金，本次消費可完全覆蓋）。若餐廳消費透過街口支付且該筆交易被銀行判定為網路交易，可享此高回饋。\"}, {\"name\": \"台新 GOGO 卡 (搭配街口支付使用)\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"GOGO卡針對指定數位通路（含街口支付）提供最高3.8%加碼回饋（需滿足任務條件，如設定Richart自動扣繳卡費及電子帳單，每月上限300元刷卡金，本次消費可完全覆蓋）。\"}, {\"name\": \"台新 GOGO 卡 (直接刷卡)\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"若餐廳不支援街口支付，或您不希望透過行動支付，直接刷台新GOGO卡可獲得基礎一般消費回饋。\"}]}}', '2025-07-12 01:59:48'),
(19, 1, '餐飲', 2000, '2025-07-12 02:22:04', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GoGo卡 (搭配街口支付)\", \"percent\": \"3%\", \"cashback\": \"75元\", \"reason\": \"台新GoGo卡針對精選行動支付（包含街口支付）提供高回饋，此筆消費可享3%回饋 (基本0.5%+精選加碼2.5%)，若Richart帳戶條件符合可達3.8%。\"}, {\"name\": \"玉山Ubear卡\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"實體餐廳消費若無法使用行動支付，玉山Ubear卡提供一般消費1%基本回饋，可作為備選。\"}, {\"name\": \"街口支付 (僅街口幣回饋)\", \"percent\": \"0.5%\", \"cashback\": \"12.5元\", \"reason\": \"街口支付本身常態回饋為街口幣，比例較低，建議搭配高回饋信用卡使用以獲取更高回饋。\"}]}}', '2025-07-12 02:22:04'),
(20, 1, '購物', 3000, '2025-07-12 02:24:10', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡 (透過街口支付)\", \"percent\": \"3.8%\", \"cashback\": \"95元\", \"reason\": \"台新GOGO卡綁定街口支付可享指定行動支付高回饋，限額內非常划算。請注意需符合Richart帳戶自動扣繳等活動條件。\"}, {\"name\": \"玉山UBear卡\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"此卡提供一般消費1%回饋，作為餐廳消費的基礎選項，不論是否透過行動支付。\"}, {\"name\": \"台新GOGO卡 (直接刷卡)\", \"percent\": \"1%\", \"cashback\": \"25元\", \"reason\": \"若您選擇直接刷卡消費，此卡仍提供1%基本回饋。（需符合Richart帳戶自動扣繳等活動條件）\"}]}}', '2025-07-12 02:24:10'),
(21, 1, '娛樂', 3000, '2025-07-12 08:31:43', '{\"existing_tools_recommendation\": {\"title\": \"使用您現有的工具，推薦如下(請注意高%數的限額)：\", \"recommendations\": [{\"name\": \"台新GOGO卡 (綁定LINE Pay/街口支付)\", \"percent\": \"3.8%\", \"cashback\": \"114元\", \"reason\": \"若娛樂消費可使用LINE Pay或街口支付，且符合台新GOGO卡數位精選通路條件，可享3.8%回饋。(上限300元/期，刷約8100元封頂)\"}, {\"name\": \"國泰Cube卡 (切換至「集精選」)\", \"percent\": \"3%\", \"cashback\": \"90元\", \"reason\": \"若本次娛樂消費為指定電影院 (如威秀、國賓、秀泰、新光影城)，切換至「集精選」方案可享3%小樹點回饋。\"}, {\"name\": \"玉山UBear卡\", \"percent\": \"3%\", \"cashback\": \"90元\", \"reason\": \"若本次娛樂消費為網路交易 (如線上購票、遊戲儲值)，可享3%網路消費回饋。(上限200元/月，刷約7000元封頂)\"}]}}', '2025-07-12 08:31:43');

-- --------------------------------------------------------

--
-- 資料表結構 `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `line_user_id` varchar(50) NOT NULL COMMENT 'LINE 使用者的唯一 ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='儲存 LINE 使用者的基本資料';

--
-- 傾印資料表的資料 `users`
--

INSERT INTO `users` (`id`, `line_user_id`, `created_at`) VALUES
(1, 'Ue211b597e4cf6e76b2006235523d7281', '2025-07-09 11:44:25');

-- --------------------------------------------------------

--
-- 資料表結構 `user_payment_methods`
--

CREATE TABLE `user_payment_methods` (
  `user_id` int(11) NOT NULL,
  `payment_option_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='使用者擁有的支付方式';

--
-- 已傾印資料表的索引
--

--
-- 資料表索引 `payment_options`
--
ALTER TABLE `payment_options`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name_UNIQUE` (`name`);

--
-- 資料表索引 `transactions`
--
ALTER TABLE `transactions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_transactions_users1_idx` (`user_id`);

--
-- 資料表索引 `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `line_user_id_UNIQUE` (`line_user_id`);

--
-- 資料表索引 `user_payment_methods`
--
ALTER TABLE `user_payment_methods`
  ADD PRIMARY KEY (`user_id`,`payment_option_id`),
  ADD KEY `fk_users_has_payment_options_payment_options1_idx` (`payment_option_id`),
  ADD KEY `fk_users_has_payment_options_users_idx` (`user_id`);

--
-- 在傾印的資料表使用自動遞增(AUTO_INCREMENT)
--

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `payment_options`
--
ALTER TABLE `payment_options`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `transactions`
--
ALTER TABLE `transactions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- 使用資料表自動遞增(AUTO_INCREMENT) `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- 已傾印資料表的限制式
--

--
-- 資料表的限制式 `transactions`
--
ALTER TABLE `transactions`
  ADD CONSTRAINT `fk_transactions_users1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- 資料表的限制式 `user_payment_methods`
--
ALTER TABLE `user_payment_methods`
  ADD CONSTRAINT `fk_users_has_payment_options_payment_options1` FOREIGN KEY (`payment_option_id`) REFERENCES `payment_options` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_users_has_payment_options_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
