locals {
  foundation = data.terraform_remote_state.foundation.outputs

  postgres_env = {
    POSTGRES_SERVER   = local.foundation.db_host
    POSTGRES_PORT     = tostring(local.foundation.db_port)
    POSTGRES_USER     = local.foundation.db_username
    POSTGRES_PASSWORD = local.foundation.db_password
    POSTGRES_DB       = local.foundation.db_name
  }
}

resource "aws_lambda_layer_version" "card" {
  layer_name          = "${var.project}-card-deps"
  filename            = "${path.module}/../dist/layer.zip"
  source_code_hash    = filebase64sha256("${path.module}/../dist/layer.zip")
  compatible_runtimes = ["python3.13"]
  # built on whatever machine ran build.sh — see build.sh's PYTHON_BIN
  # comment if that machine isn't x86_64.
  compatible_architectures = ["x86_64"]
}

resource "aws_lambda_function" "card" {
  for_each = var.card_routes

  function_name = "${var.project}-card-${each.key}"
  role          = local.foundation.card_lambda_role_arn
  runtime       = "python3.13"
  architectures = ["x86_64"]
  handler       = "main.handler"
  timeout       = 10
  memory_size   = 256
  layers        = [aws_lambda_layer_version.card.arn]

  filename         = "${path.module}/../dist/functions/${each.key}.zip"
  source_code_hash = filebase64sha256("${path.module}/../dist/functions/${each.key}.zip")


  environment {
    variables = merge(local.postgres_env, {
      JWT_PUBLIC_KEY_SECRET_ARN = local.foundation.jwt_public_key_secret_arn
    })
  }
}
