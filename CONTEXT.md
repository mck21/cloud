# Contexto para Desarrollo de Templates CloudFormation

Este documento define las reglas, estructura y convenciones para desarrollar templates de AWS CloudFormation en este proyecto.

## Estructura del Archivo YAML

Los templates deben seguir esta estructura con comentarios específicos que incluyen enlaces a la documentación oficial de AWS.

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: Descripción breve del stack en español

# PARAMETERS
# Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html
Parameters:
  # Definir parámetros aquí
  ExampleParam:
    Type: String
    Description: Descripción en español

# CONDITIONS
# Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/conditions-section-structure.html
Conditions:
  # Definir condiciones lógica aquí

# RULES (Opcional)
# Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/rules-section-structure.html
Rules:
  # Definir reglas de validación

Resources:

  # GRUPO DE RECURSOS (e.g. VPC)
  # Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-vpc.html
  MyResource:
    Type: AWS::EC2::VPC
    Properties:
      # ...

# OUTPUTS
# Docs: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/outputs-section-structure.html
Outputs:
  ResourceId:
    Description: Descripción del output en español
    Value: !Ref MyResource
```

## Convenciones de Naming y Lenguaje

*   **Identificadores Lógicos (Logical IDs)**: Usar **Inglés** y PascalCase (e.g., `PublicSubnet`, `Environment`, `WebServer`).
*   **Descripciones**: Usar **Español**.
*   **Evitar caracteres especiales**: No usar la letra `ñ`, sustituir por `ny`.
*   **Grupos de Seguridad**: Usar el prefijo `GS-` para el nombre (Tag Name) o referencias donde aplique, para evitar errores con `sg-`.

## Configuración Específica para EC2

Para todas las instancias EC2, usar obligatoriamente los siguientes valores predeterminados:

*   **AMI ID**: `ami-0532be01f26a3de55`
*   **Key Name**: `vockey`
*   **Instance Type**: `t3.micro`

## Comandos CLI Útiles (Reference)

Incluir estos comandos comentados al final del archivo template para facilitar su uso.

```bash
# Comando para crear la pila:
# aws cloudformation create-stack --stack-name <NombreStack> --template-body file://<NombreArchivo>.yml --parameters ParameterKey=<Key>,ParameterValue=<Value>

# Comando para deploy (actualizar o crear si no existe, requiere CAPABILITY_NAMED_IAM si hay IAM resources):
# aws cloudformation deploy --stack-name <NombreStack> --template-file <NombreArchivo>.yml

# Comando para eliminar la pila:
# aws cloudformation delete-stack --stack-name <NombreStack>

# Comando para listar las pilas:
# aws cloudformation list-stacks

# Comando para actualizar la pila:
# aws cloudformation update-stack --stack-name <NombreStack> --template-body file://<NombreArchivo>.yml --parameters ...
```
