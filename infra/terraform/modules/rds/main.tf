resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "this" {
  identifier             = "${var.name_prefix}-postgres"
  engine                 = "postgres"
  engine_version         = var.engine_version
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = var.security_group_ids
  publicly_accessible    = false
  skip_final_snapshot    = true
  deletion_protection    = false
  multi_az               = false
}

