# --------------------
# VPC 
# --------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = "major-project-vpc"
  cidr = var.cidr_block

  azs            = [var.availability_zone]
  public_subnets = var.public_subnets

  enable_nat_gateway = false
  enable_vpn_gateway = false

  tags = {
    Terraform   = "true"
    Environment = "dev"
  }
}

# --------------------
# EC2 instances (using the ec2-instance module)
# --------------------
resource "aws_instance" "ubuntu" {
  count = var.instance_count

  ami           = var.ami_id
  instance_type = var.instance_type

  subnet_id              = module.vpc.public_subnets[0]
  vpc_security_group_ids = [module.project-sg.security_group_id]

  associate_public_ip_address = true
  key_name                    = aws_key_pair.deployed_key.key_name

  tags = {
    Name        = "ubuntu-${count.index}"
    Environment = "dev"
  }
}

output "ec2_public_dns" {
  description = "Map of instance name -> public DNS name"
  value = {
    for idx, inst in aws_instance.ubuntu : format("ubuntu-%d", idx) => inst.public_dns
  }
}

# --------------------
# Security Group: Allow All Traffic 
# --------------------
module "project-sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "allow-all-sg"
  description = "Security group that allows all inbound and outbound traffic"
  vpc_id      = module.vpc.vpc_id

  ingress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = "0.0.0.0/0"
      description = "Allow all inbound"
    }
  ]

  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = "0.0.0.0/0"
      description = "Allow all outbound"
    }
  ]

  tags = {
    Name        = "allow-all-traffic"
    Environment = "dev"
  }
}

# Upload local public key to AWS
resource "aws_key_pair" "deployed_key" {
  key_name   = "project-key"
  public_key = file("${path.module}/public")
}

