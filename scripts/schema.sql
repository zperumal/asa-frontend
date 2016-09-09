
CREATE DATABASE ASAFrontend; 


CREATE TABLE `ASAFrontend`.`tbl_user` (
  `user_id` BIGINT  AUTO_INCREMENT,
  `user_name` VARCHAR(45) NULL,
  `user_username` VARCHAR(45) NULL,
  `user_password` VARCHAR(200) NULL,
  PRIMARY KEY (`user_id`)); 

use ASAFrontend;
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `createUser`(
    IN p_name VARCHAR(20),
    IN p_username VARCHAR(20),
    IN p_password VARCHAR(80)
)
BEGIN
    if ( select exists (select 1 from tbl_user where user_username = p_username) ) THEN
     
        select 'Username Exists !!';
     
    ELSE
     
        insert into tbl_user
        (
            user_name,
            user_username,
            user_password
        )
        values
        (
            p_name,
            p_username,
            p_password
        );
     
    END IF;
END$$
DELIMITER ;

