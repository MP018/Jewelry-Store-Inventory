use palace_jewelers;

show tables;

describe item;

CREATE TABLE `item` (
    `pictures` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
    `description` varchar(500) DEFAULT NULL,
    `price` decimal(7, 2) DEFAULT NULL,
    `name` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
    `type` varchar(255) DEFAULT NULL,
    `metal` varchar(255) DEFAULT NULL,
    `quantity` int DEFAULT NULL,
    `soldDate` date DEFAULT NULL,
    `seller` varchar(255) DEFAULT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci