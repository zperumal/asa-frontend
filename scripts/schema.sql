
CREATE DATABASE ASAFrontend; 


CREATE TABLE `ASAFrontend`.`tbl_user` (
  `user_id` BIGINT  AUTO_INCREMENT,
  `user_name` VARCHAR(200) NULL,
  `user_username` VARCHAR(200) NULL,
  `user_password` VARCHAR(200) NULL,
  PRIMARY KEY (`user_id`)); 

use ASAFrontend;
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `createUser`(
    IN p_name VARCHAR(200),
    IN p_username VARCHAR(200),
    IN p_password VARCHAR(200)
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


CREATE TABLE `ASAFrontend`.`output_data` (
  `job_id` BIGINT  AUTO_INCREMENT,
   `user_id` BIGINT,
  `job_name` VARCHAR(200) NULL,
  `job_type` VARCHAR(200) NULL,
  `state` VARCHAR(200) NULL,
  `seed` VARCHAR(200) NULL,
  `increment` VARCHAR(200) NULL,
  `rounds` VARCHAR(200) NULL,
  `ballots` VARCHAR(200) NULL,
  `data` VARCHAR(200) NULL,
  PRIMARY KEY (`job_id`)); 

use ASAFrontend;
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `addJob`(
    IN p_job_id VARCHAR(200),
    IN p_user_id VARCHAR(200),
    IN p_job_name VARCHAR(200),
    IN p_job_type VARCHAR(200),
    IN p_state VARCHAR(200),
    IN p_seed VARCHAR(200),
    IN p_increment VARCHAR(200),
    IN p_rounds VARCHAR(200),
    IN p_ballots VARCHAR(200),
    IN p_job_data VARCHAR(200)
    
)
BEGIN
    insert into output_data
        (
            job_id,
            user_id,
            job_name,
            job_type,
            state,
            seed,
            increment,
            rounds,
            ballots,
            job_data
        )
	values
        (
            p_job_id,
            p_user_id,
            p_job_name,
            p_job_type,
            p_state,
            p_seed,
            p_increment,
            p_rounds,
            p_ballots,
            p_job_data
        );

END$$
DELIMITER ;


use ASAFrontend;
DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `updateJob`(
    IN p_job_id VARCHAR(200),
    IN p_status VARCHAR(200),
    IN p_rounds VARCHAR(200),
    IN p_ballots VARCHAR(200)
    
)
BEGIN
    UPDATE output_data
	SET
            status = p_status,
            rounds = p_rounds,
            ballots = p_ballots
        
	WHERE job_id = p_job_id;
END$$
DELIMITER ;