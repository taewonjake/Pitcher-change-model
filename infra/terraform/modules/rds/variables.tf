variable "name_prefix" {
  type        = string
  description = "Resource name prefix"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnet ids for RDS"
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group ids for RDS"
}

variable "engine_version" {
  type        = string
  default     = "15.8"
  description = "PostgreSQL engine version"
}

variable "instance_class" {
  type        = string
  default     = "db.t3.micro"
  description = "RDS instance class"
}

variable "allocated_storage" {
  type        = number
  default     = 20
  description = "Allocated storage in GB"
}

variable "db_name" {
  type        = string
  description = "Database name"
}

variable "db_username" {
  type        = string
  description = "Master username"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Master password"
}

