-- 智能旧衣回收箱 - 数据库初始化脚本
-- 此脚本在 MySQL 容器首次启动时自动执行

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 确保使用正确的数据库
USE clothing_recycle;

-- 设置时区
SET time_zone = '+08:00';

-- 授权（Docker 环境）
GRANT ALL PRIVILEGES ON clothing_recycle.* TO 'recycle'@'%';
FLUSH PRIVILEGES;

-- 提示信息
SELECT '数据库初始化完成' AS message;

