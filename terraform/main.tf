terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"  # Change if your instance is in another region
  access_key="ASIATCTOZSMJI4UERNGS"
  secret_key="OjtbOTUc36OTqyG4iVYj4ULZUmExyN93IdFQpRuQ"
  token="IQoJb3JpZ2luX2VjEJL//////////wEaCXVzLXdlc3QtMiJGMEQCIGvTu5vnWnPLFTXC8oRH7lrnXs/ruSypZZKsb29AfwDrAiBkz0i3kNnPLp7TswmXOc8D1Co0/eF/VYpiXRRzIqJWKyq3Agj7//////////8BEAAaDDIxMTc1OTUwMjA5OCIMiAT06Ki7Y0GlEon6KosC2gngkv0p7SLsIo1qfH6nUNGUkkktxZJKY9JFrtfO07TuLA+UzsMY+/nyx7HxZFN/NmFmvFnnt5dJTAv3MO6jhkMaCVZsc1RTsEhFDs2vtfHfuewxK9TJbCqwhCLkClHd7DmAi7Rv503CERRYlmk1NUj92JC58K5GMhll+iXbd8pt40zUoejqwiiuP/OwP5TT0HljboXHehDc1LHzt4hmYmh66mlf63PMYvT19td+hidLQKhtp2MrTGGHrSfGJD1Hf3iNLvVNhan5II5BoYDm8cAA6+CBIYgPhtlH+SmAC6ZnxB6inePE/99ZUE4npZ+nOdebcZH/u/s/1+IWifeK2LYZyiyTEsaiZNRWMIXpvL8GOp4BB1dLfhYR1C3aw1lgbl4W4MycWTOFOngDBvNzmqB5jvAbt92boi4LyJDkttMb9x1pp57mcP7VifVEYaUJ/NWScSp76CEQcd4zzshuQuzJdq7XPtdAiVZndWykjSebujNxVM+qPdOMuQdbl1aJAJgDVor4IC8w7ctS6WSC+jss7U8j0AaP0pL7bphM6ZAxwr4te74f0l/a5zysDAzzINM="             # Force IMDSv2 complianc

  skip_metadata_api_check     = true
  skip_credentials_validation = true
}

# Fetch the existing EC2 instance
data "aws_instance" "foxtrot" {
  instance_id = "i-04e960b31e075b240"
}

# Run commands remotely via SSH
resource "null_resource" "deploy_foxtrot" {
  triggers = {
    always_run = timestamp()  # Ensures commands run on every apply
  }

  connection {
    type        = "ssh"
    host        = data.aws_instance.foxtrot.public_dns  # Uses Public DNS (ec2-35-169-25-122.compute-1.amazonaws.com)
    user        = "ubuntu"  # SSH user (Ubuntu AMI)
    private_key = file("foxtrot-key.pem")  # Path to your PEM key
  }

  provisioner "remote-exec" {
    inline = [
      "cd SENG3011-Foxtrot/src/",
      "pwd",
      ". venv/bin/activate",
      "nohup gunicorn -b 0.0.0.0:8000 --env ALPACA_SECRET_KEY=hknQ0XZEqfEyRpKEu4IygFOgVTse822UxRhzJzIQ --env ALPACA_PUBLIC_KEY=PKU19EIKMBGRHMAC1V7P --env FMP_API_KEY=t2PsBsAxGsEQ0if3nlEAfoBx4LV9PISG app:app &",
      "sudo systemctl stop apache2",
      "sudo systemctl start nginx",
      "sleep 5",
      "pgrep gunicorn || echo 'Gunicorn failed to start'"
    ]
  }
}

output "instance_public_dns" {
  value = data.aws_instance.foxtrot.public_dns
}