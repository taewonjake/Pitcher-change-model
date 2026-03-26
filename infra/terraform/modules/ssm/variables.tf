variable "secure_parameters" {
  type        = map(string)
  description = "SecureString parameters to create"
  default     = {}
}

variable "plain_parameters" {
  type        = map(string)
  description = "String parameters to create"
  default     = {}
}

