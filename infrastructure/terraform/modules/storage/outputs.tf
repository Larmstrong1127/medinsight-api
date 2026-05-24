output "documents_bucket" { value = aws_s3_bucket.documents.bucket }
output "cloudtrail_bucket" { value = aws_s3_bucket.cloudtrail.bucket }
output "documents_table" { value = aws_dynamodb_table.documents.name }
output "audit_table" { value = aws_dynamodb_table.audit.name }
