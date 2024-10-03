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

use palace_jewelers;
show tables;

create table repair (
picture varchar(500),
description varchar(500),
price decimal(7,2),
name varchar(500),
type varchar(500),
metal varchar(500),
worker varchar(500)
);

create table customer (
id int primary key not null auto_increment,
first_name varchar(500) not null,
last_name varchar(500) not null,
phone int,
email varchar(500)
);

