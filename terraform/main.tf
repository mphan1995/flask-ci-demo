resource "aws_vpc" "jenkins_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "jenkins-vpc" }
}

resource "aws_subnet" "jenkins_subnet" {
  vpc_id                  = aws_vpc.jenkins_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"
  tags = { Name = "jenkins-subnet" }
}

resource "aws_internet_gateway" "jenkins_gw" {
  vpc_id = aws_vpc.jenkins_vpc.id
}

resource "aws_route_table" "jenkins_rt" {
  vpc_id = aws_vpc.jenkins_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.jenkins_gw.id
  }
}

resource "aws_route_table_association" "jenkins_assoc" {
  subnet_id      = aws_subnet.jenkins_subnet.id
  route_table_id = aws_route_table.jenkins_rt.id
}

resource "aws_security_group" "jenkins_sg" {
  name        = "jenkins-sg"
  description = "Allow Jenkins and SSH"
  vpc_id      = aws_vpc.jenkins_vpc.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Jenkins UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "tls_private_key" "jenkins_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "jenkins_keypair" {
  key_name   = "lt-devops-key"
  public_key = tls_private_key.jenkins_key.public_key_openssh
}

resource "local_file" "jenkins_private_key" {
  content  = tls_private_key.jenkins_key.private_key_pem
  filename = "${path.module}/lt-devops-key.pem"
}

resource "aws_instance" "jenkins_ec2" {
  ami                         = "ami-0c7217cdde317cfec" # Ubuntu 22.04
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.jenkins_subnet.id
  vpc_security_group_ids      = [aws_security_group.jenkins_sg.id]
  key_name                    = aws_key_pair.jenkins_keypair.key_name
  associate_public_ip_address = true

  tags = { Name = "jenkins-ec2" }
}

output "jenkins_public_ip" {
  value = aws_instance.jenkins_ec2.public_ip
}
