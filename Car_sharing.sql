CREATE DATABASE car_sharing;
USE car_sharing;
show tables;

-- Registration table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY, 
    username VARCHAR(50) NOT NULL,        
    password VARCHAR(255) NOT NULL, 
    role ENUM('Admin','User'),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

ALTER TABLE users MODIFY COLUMN role ENUM('Admin', 'User') DEFAULT 'User';


SET SQL_SAFE_UPDATES=0;
select * from users;
select * from user_info;
 
select username, role, count(*)
 from users 
 group by 
 username, role
 having count(*)>1;
 
Create TABLE user_info(
	user_id int,
	FOREIGN KEY (user_id) REFERENCES users (user_id),
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(15),             
    address_line1 VARCHAR(255) NOT NULL,   
    address_line2 VARCHAR(255),           
    city VARCHAR(100) NOT NULL,         
    state VARCHAR(100) NOT NULL,       
    country VARCHAR(100) NOT NULL,         
    gender ENUM('Male', 'Female') NOT NULL, 
    birthday DATE NOT NULL,               
    role ENUM('admin', 'user') NOT NULL,  
    profile_picture BLOB,                  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP 
);
alter table user_info modify column  profile_picture VARCHAR(255);
delete from user_info where user_id=10;

desc user_info;
select * from user_info;

-- Create CarTypes Table
CREATE TABLE CarTypes (
    type_id INT PRIMARY KEY AUTO_INCREMENT,
    type_name VARCHAR(255) NOT NULL,
    image varchar(255) NOT NULL,
    type_description VARCHAR(255)
);
alter table CarTypes add column image varchar(255);
select * from CarTypes;
SELECT * FROM CarTypes LIMIT 5 OFFSET 0;
alter table CarTypes modify type_description text;
update companies set user_id = 17;

ALTER TABLE carTypes
ADD COLUMN user_id INT,
ADD CONSTRAINT fk_user
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
    ON DELETE CASCADE; -- Ensures that if the user is deleted, the car type associated with them is also deleted
ALTER TABLE Cartypes DROP FOREIGN KEY fk_user;


-- Create Companies Table
CREATE TABLE Companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(255) NOT NULL,
    company_description VARCHAR(255),
    image varchar(255)
);

ALTER TABLE Companies
ADD COLUMN user_id INT,
ADD CONSTRAINT fk_user_id
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
    ON DELETE CASCADE; -- Ensures that if the user is deleted, the company associated with them is also deleted
alter table Companies modify company_description text;
desc companies;
select * from Companies;

-- Create Bookings Table
CREATE TABLE Bookings (
    booking_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    car_number INT,
    pickup_date DATE NOT NULL,
    dropoff_date DATE NOT NULL,
    pickup_address VARCHAR(255) NOT NULL,
    dropoff_address VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (car_number) REFERENCES add_car(car_number)
);
desc bookings;
select * from bookings;
update bookings set booking_status = 'Booked' where booking_status = 'pending';
ALTER TABLE Bookings
ADD COLUMN booking_status VARCHAR(50) DEFAULT 'Pending'; -- or whatever status you prefer


CREATE TABLE add_car(
	car_number int primary key  AUTO_INCREMENT,
    car_owner_id int,
    car_name varchar(100),
    from_location varchar(500),
    to_location varchar(100),
    type_id int,
    company_id int,
    car_type varchar(500),
    company_name varchar(500),
    price_per_day decimal(10,5),
    stock int,
    car_img varchar(500),
    description text,
    FOREIGN KEY (car_owner_id) REFERENCES Users(user_id),
	FOREIGN KEY (type_id) REFERENCES CarTypes(type_id),
    FOREIGN KEY (company_id) REFERENCES Companies(company_id));
    


select * from add_car;
update add_car set price_per_day = 5999 where car_number=19;
delete from add_car where car_number=15;
SELECT car_img FROM add_car;


show tables;
