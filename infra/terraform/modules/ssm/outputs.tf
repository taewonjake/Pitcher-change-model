output "secure_parameter_names" {
  value = keys(var.secure_parameters)
}

output "plain_parameter_names" {
  value = keys(var.plain_parameters)
}

