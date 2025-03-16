terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0.0"
}

# Set the AWS provider to use the region where account is currently active
provider "aws" {
  region = "us-east-1"
}

# Security group for EC2
resource "aws_security_group" "ec2_sg" {
  name        = "flask-app-ec2-sg"
  description = "Allow traffic for Flask app"

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Flask app port
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# Security group for RDS
resource "aws_security_group" "rds_sg" {
  name        = "flask-app-rds-sg"
  description = "Allow PostgreSQL traffic"

  # PostgreSQL access from EC2 security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS PostgreSQL instance to match your Flask app
resource "aws_db_instance" "postgres_rds" {
  identifier             = "flask-app-postgres"
  allocated_storage      = 20
  engine                 = "postgres"  # Changed from MySQL to PostgreSQL to match
  engine_version         = "14.17"
  instance_class         = "db.t3.micro"
  db_name                = "postgres"  # Default database name
  username               = "postgres"  # Match the username in your Flask app
  password               = "your-password"  # Update to match your app's password
  parameter_group_name   = "default.postgres14"
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  publicly_accessible    = true  # For easier access during development
}

# Get latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# EC2 instance for Flask app
# Installing Python, Flask and sets up application
resource "aws_instance" "flask_app" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t2.micro"
  security_groups = [aws_security_group.ec2_sg.name]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y python3 python3-pip git
              pip3 install flask psycopg2-binary werkzeug

              # Create directory for app
              mkdir -p /home/ec2-user/flask-app

              # Create main.py for your Flask app
              cat > /home/ec2-user/flask-app/main.py << 'EOL'
              from flask import Flask, request, jsonify, session
              import psycopg2
              from werkzeug.security import generate_password_hash, check_password_hash

              app = Flask(__name__)
              app.config['SECRET_KEY'] = 'your_secret_key'

              db_config = {
                  'dbname': 'postgres',
                  'user': 'postgres',
                  'password': 'your-password',
                  'host': '${aws_db_instance.postgres_rds.address}',
                  'port': 5432
              }

              def get_db_connection():
                  conn = psycopg2.connect(**db_config)
                  return conn

              @app.route('/')
              def home():
                  return "Hello, Flask!"

              if __name__ == '__main__':
                  app.run(host='0.0.0.0', port=5000, debug=True)
              EOL

              # Run the Flask app on startup
              echo "cd /home/ec2-user/flask-app && python3 main.py &" >> /etc/rc.local
              chmod +x /etc/rc.local
              /etc/rc.local
              EOF

  tags = {
    Name = "flask-app-ec2"
  }
}

# Output the public IP and RDS endpoint
output "flask_app_ip" {
  value = aws_instance.flask_app.public_ip
}

output "db_endpoint" {
  value = aws_db_instance.postgres_rds.endpoint
}