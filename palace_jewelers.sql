use palace_jewelers;
show tables;

create table Item (
SKU varchar(500) not null primary key,
pictures varchar(500) not null,
description varchar(500) not null,
price decimal(7,2) not null,
name varchar(500) not null,
quantity int not null,
sold_date date
);

create table Item_Tags (
sku varchar(500) not null primary key,
tags varchar(500) not null,
constraint fk_sku foreign key (sku) references item (sku)
);

create table Customer (
Customer_ID int primary key not null,
First_Name varchar(500) not null,
Last_Name varchar(500) not null,
phone int not null,
email varchar(500) not null
);

create table Employee (
Employee_ID int not null primary key,
First_Name varchar(500) not null,
Last_Name varchar(500) not null,
Position varchar(500) not null,
Email varchar(500) not null,
phone int not null
);

create table Repair_Order (
Repair_ID int primary key not null,
Employee_ID int not null,
Customer_ID int not null,
Subtotal decimal(7,2) not null,
Tax decimal(7,2) not null,
Total decimal(7,2) not null,
constraint fk_repair_Id foreign key (repair_id) references repair_item (repair_id)
);

create table Repair_Item (
Repair_ID int not null primary key,
customer_id int not null,
pictures varchar(500) not null,
description varchar(500) not null,
name varchar(500) not null
);

create table Order_Item (
Order_Number int primary key not null,
SKU varchar(500) not null
);

create table Sale (
Order_Number int primary key not null,
Customer_ID int not null,
Employee_ID int not null,
Subtotal decimal(7,2) not null,
Tax decimal(7,2) not null,
Total decimal(7,2) not null,
constraint fk_customerid foreign key (Customer_ID) references Customer (customer_id),
constraint fk_employeeid foreign key (employee_id) references Employee (employee_id),
constraint fk_order_number foreign key (Order_Number) references order_item (order_number)
);