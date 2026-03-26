variable "bucket_name" {
  type        = string
  description = "S3 bucket name"
}

variable "versioning_enabled" {
  type        = bool
  description = "Enable object versioning"
  default     = false
}

