terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0.0"
}



resource "aws_db_instance" "example_rds" {
  identifier             = "my-terraform-rds"
  allocated_storage      = 20
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t2.micro"
  username               = "admin"
  password               = "SuperSecurePassword123"
  parameter_group_name   = "default.mysql8.0"
  skip_final_snapshot    = true
}


# setting the region
provider "aws" {
  region = "us-west-2"
}

#resource "aws_s3_bucket" "example_bucket" {
  # Must be globally unique across all AWS
  #bucket = "my-unique-s3-bucket-12345"
  #acl    = "private"
#}

