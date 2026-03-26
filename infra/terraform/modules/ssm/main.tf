resource "aws_ssm_parameter" "secure_string" {
  for_each = var.secure_parameters

  name  = each.key
  type  = "SecureString"
  value = each.value
}

resource "aws_ssm_parameter" "string" {
  for_each = var.plain_parameters

  name  = each.key
  type  = "String"
  value = each.value
}

