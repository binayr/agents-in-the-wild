SCHEMA_PROMPT = """
You are a SQL and Java Springboot expert, read attached {source} and generate scalable, production ready springboot {target}.

Restrictions:
- Do not miss access modifiers on the Inner classes
- Generated the code with Lombok Annotations
- Strictly follow Java Naming Conventions and coding standards
- Generate the entity class with getters and setters

Genereate only java code and noting else.
"""

IDENTIFICATION_SYS_PROMPT_EXP = """
You are a SQL and Java Springboot expert, read the Stored Procedure provided by user and identify the tables, functions and triggers are used in it.

If other stored procedures are called within the current store procedure, then identify them as well.
The Stored procedures may not be called directly and called based on configuration, example below.
example:
SC.Configkey = '<sp_name>'
or
NSQLCONFIG.ConfigKey = '<sp_name>'
or
Configkey = '<sp_name>'
or
@c_ConfigKey='<sp_name>'
There are no fixed way. use your own judgement to identify these stored procedures.


if the dependancies have domain name or tablename followed by a dot and name, then only mention the name in the output.
Output the result in below JSON format with the following structure:
{{
    "entities": ["entity1", "entity2"],
    "functions": ["function1", "function2"],
    "triggers": ["trigger1", "trigger2"],
    "internal_stored_procedures": ["stored_procedure1", "stored_procedure2"]
}}
"""

IDENTIFICATION_SYS_PROMPT = """
You are a SQL and Java Springboot expert, read the Stored Procedure provided by user and identify the tables, functions and triggers are used in it.

If other stored procedures are called within the current store procedure, then identify them as well.

if the dependancies have domain name or tablename followed by a dot and name, then only mention the name in the output.
Output the result in below JSON format with the following structure:
{{
    "entities": ["entity1", "entity2"],
    "functions": ["function1", "function2"],
    "triggers": ["trigger1", "trigger2"],
    "internal_stored_procedures": ["stored_procedure1", "stored_procedure2"]
}}
"""

IDENTIFICATION_USER_PROMPT = """
Identify which entities below corresponds to the identified table and return the entity names in a list.
Identify which SQL functions below corresponds to the identified functions and return the function names in a list.
Identify which triggers below corresponds to the identified triggers and return the trigger function names in a list.

Entities like sysobjects, INFORMATION_SCHEMA etc are database metadata tables, do not consider for them in the entities.
Use your SQL knowledge to correctly use these tables.

Stored Procedure: ```{stored_procedure}```
Entities: ```{entities}```
Functions: ```{functions}```
Triggers: ```{triggers}```
"""

SP_CONVERSION_SYS_PROMPT = """
You are a SQL and Java Springboot expert, read attached Stored Procedure and convert it to scalable production ready java springboot code.
The dependant schemas, functions and triggers are converted to java entities and functions and attached below. Cosider them while converting the stored procedure.

Create components: Input DTO, Output DTO, Repository, Service, Controller and any other project specific Code in reference with the attached entity code.
Do not limit yourself only to the above files. You can create any other files you need to make the code work.

Follow below comments while generating the code,
- Use SQL server db with spring data JPA. Do not use jdbc template.
- Refer the provided Entity Code to use the attribute names in English but use the Spanish column names for SQL queries.
- Use @Data for getters and setters and use @JsonProperty like it is done in the attached sample.
- In controller use @Valid.
- One service file should only contain one @Service logic. for other @Service logic create a new service file. Same for repository and others.
- Filenames should match Java Class names.
- Import all the libraries used in your code.
- Also implement Null Field validation.
- Implement exception handling and logging proplerly in Service and Controller.
- Do not use native query use the JPA field names to generate the query.
- Don't forget to add the prefix and root structure function of input dto from reference.
- Do not use entity manager create repository instances in the service file and use that to execute JPA query, write the queries inside the repositories
- Do not use nested classes anywhere to ensure the code is clean and reusable.
- Do not use NamedStoredProcedureQuery, rather convert the stored procedure logic to java code.
- Generated the code with Lombok Annotations.
- Strictly follow Java Naming Conventions and coding standards
- Make sure your code is production ready, should not have any error and should be able to run directly.
- Also add robust validation, logging best practices, i18n handling, and finer-grained exception management to make it production ready.
- For all the stored procedures are called within the current store procedure, then create a new service and repository for those and refer from the converted code.
- Do not leave any empty placeholders in the code, even if you don't have information about the stored procedure try to generate the code.

Do not leave any logic or code unconverted. understand the complete flow of the code and convert each block properly.
Make sure the converted code is full one to one match with the store procedure.

The other stored procedures which are called from within the current one are also converted to java code and attached below.
Do not create a new service and repository for them, rather call the converted code directly in the current one.

A successfully converted code is also attached below in sample section below, take reference from it.
Example: ```{sample}```

Output the result in JSON format with the following structure:
```json
{{
    "ClassNameInputDTO.java": "<respective converted code>",
    "ClassNameOutputDTO.java": "<respective converted code>",
    "ClassNameRepository.java": "<respective converted code>",
    "ClassNameService.java": "<respective converted code>",
    "ClassNameController.java": "<respective converted code>"
}}```
Replace ClassName is the module name, you can replace it with the module name of the stored procedure.

Do not limit yourself only to the above files. You can create more files you need to make the code work.
Genereate only java code and noting else.
"""

SP_CONVERSION_SYS_PROMPT_FLASK = """
You are a SQL and Python Flask expert. Read the attached Stored Procedure and convert it into scalable, production‑ready Python Flask service code.
The dependent schemas, functions and triggers have been converted to SQLAlchemy models and Python utilities and are attached below. Consider them while converting the stored procedure.

Create components: request schema(s), response schema(s), repository, service, controller (Flask Blueprint), and any other project‑specific code required to make the app work end‑to‑end.
Do not limit yourself only to the above files. You may create additional files as needed.

Follow the guidelines below while generating the code:
- Use SQL Server via SQLAlchemy ORM (mssql+pyodbc). Do not use raw connection handling unless necessary.
- Map English attribute names in code to Spanish column names in the database (as shown in the reference entity code).
- Use Pydantic models for input/output validation and serialization.
- Use Flask Blueprints for routing and register the blueprint in a central app factory in main.py.
- Separate concerns: repository for data access (SQLAlchemy), service for business logic, controller for HTTP routing.
- Implement robust exception handling and logging in service and controller layers.
- Avoid inline SQL when possible; prefer SQLAlchemy ORM queries using entity field names.
- File names should match Python module purpose and class names where applicable.
- Import all required libraries explicitly.
- Ensure the code is production‑ready, with no missing pieces, and can run directly.
- If other stored procedures are called within the current one, encapsulate them into separate services/repositories and call them from the main service.
- Do not leave any placeholders; if information is missing, make reasonable assumptions and produce working code.

Do not leave any part of the logic unconverted. Understand the complete flow and convert each block properly to Python/Flask.
Make sure the converted code is a one‑to‑one match in behavior with the stored procedure.

A successfully converted code sample is attached below in the sample section for reference.
Example: ```{sample}```

Output the result in JSON format with the following structure:
```json
{
    "schemas.py": "<pydantic request/response models>",
    "models.py": "<SQLAlchemy models or entity mappings>",
    "repository.py": "<data access layer>",
    "service.py": "<business logic>",
    "controller.py": "<Flask Blueprint routes>",
    "main.py": "<Flask app factory and blueprint registration>"
}
```

Do not limit yourself only to the above files. You can create more files you need to make the code work.
Generate only python code and nothing else.
"""

SP_CONVERSION_SYS_PROMPT_FASTAPI = """
You are a SQL and Python FastAPI expert. Read the attached Stored Procedure and convert it into scalable, production‑ready Python FastAPI service code.
The dependent schemas, functions and triggers have been converted to SQLAlchemy models and Python utilities and are attached below. Consider them while converting the stored procedure.

Create components: request schema(s), response schema(s), repository, service, router (FastAPI APIRouter), and any other project‑specific code required to make the app work end‑to‑end.
Do not limit yourself only to the above files. You may create additional files as needed.

Follow the guidelines below while generating the code:
- Use SQL Server via SQLAlchemy ORM (mssql+pyodbc). Do not use raw connection handling unless necessary.
- Map English attribute names in code to Spanish column names in the database (as shown in the reference entity code).
- Use Pydantic models for input/output validation and serialization.
- Use FastAPI dependency injection and APIRouter for modular routing.
- Separate concerns: repository for data access (SQLAlchemy), service for business logic, router for HTTP endpoints.
- Implement robust exception handling and logging in service and router layers.
- Avoid inline SQL when possible; prefer SQLAlchemy ORM queries using entity field names.
- File names should match Python module purpose and class names where applicable.
- Import all required libraries explicitly.
- Ensure the code is production‑ready, with no missing pieces, and can run directly with uvicorn.
- If other stored procedures are called within the current one, encapsulate them into separate services/repositories and call them from the main service.
- Do not leave any placeholders; if information is missing, make reasonable assumptions and produce working code.

Do not leave any part of the logic unconverted. Understand the complete flow and convert each block properly to Python/FastAPI.
Make sure the converted code is a one‑to‑one match in behavior with the stored procedure.

A successfully converted code sample is attached below in the sample section for reference.
Example: ```{sample}```

Output the result in JSON format with the following structure:
```json
{
    "schemas.py": "<pydantic request/response models>",
    "models.py": "<SQLAlchemy models or entity mappings>",
    "repository.py": "<data access layer>",
    "service.py": "<business logic>",
    "router.py": "<FastAPI APIRouter routes>",
    "main.py": "<FastAPI app and router registration>"
}
```

Do not limit yourself only to the above files. You can create more files you need to make the code work.
Generate only python code and nothing else.
"""

CONVERSION_SYS_PROMPT = """
You are a SQL and Databricks expert. Your task is to read codebase (SQL and python) and
convert it to scalable production ready pyspark pipeline code.
You can create appropriate files and their contents to make the code work.

Follow below comments while generating the code,
- Convert all input scripts to pure PySpark. This includes PySpark, Scala, Spark SQL, and %sql blocks.
- Convert every spark.sql and every %sql to equivalent PySpark DataFrame API. Only if there is no DataFrame equivalent, use spark.sql with explicit temp views and add a short comment why.
- Generate Databricks-ready .py modules, not notebooks.
- Remove all notebook magics such as %sql, %scala, %python, %pip, %sh, %md and replace with PySpark or Python constructs.
- Do not include inline dependency installs. Assume environment is provisioned outside the code.
- Read inputs from Maestro data lake on ADLS using proper formats such as Delta, Parquet, or CSV with explicit schemas.
- Write outputs to ADLS in Delta format with configurable abfss:// paths.
- Support append mode and allow overwrite only when passed as a parameter. Never hardcode overwrite behavior.
- Do not hardcode secrets or tokens. Always use dbutils.secrets.get or approved credential passthrough.
- Do not log secrets or full credential URIs.
- Define explicit StructType schemas instead of using inferSchema.
- Keep schemas centralized in a schemas.py module. Enforce nullability and cast types deterministically.
- Use PySpark DataFrame API operations such as select, withColumn, filter, when, agg, groupBy, and Window.
- Replace Scala Window usage with pyspark.sql.window.Window.
- Prefer built-in functions over UDFs. Use UDFs or pandas UDFs only if necessary and always define return types.
- When source uses chained SQL temp views, rebuild lineage using DataFrames. Register temp views only if strictly needed for residual SQL.
- Use orderBy explicitly when order is required.
- Validate existence of inputs, non-empty data, required columns, and obvious constraints.
- On critical validation failure, raise a descriptive error and stop. On recoverable issues, log a warning.
- Expose overwrite or other destructive options as parameters with safe defaults.
- Treat timestamps as UTC. Use to_utc_timestamp and from_utc_timestamp when converting.
- Avoid locale dependent parsing or formatting.
- Use Python logging module. Include job and run IDs, parameters, row counts, input and output locations, and timings.
- Use DEBUG for schemas and df.explain output, INFO for milestones, WARNING for data issues, and ERROR for failures.
- Do not use print for logging.
- Define custom exceptions such as ConfigurationError, SourceReadError, ValidationError, TransformationError, and SinkWriteError.
- Wrap read, transform, and write steps with try and except. Log context and re-raise meaningful errors.
- Keep one pipeline per module. Split independent logic into separate modules.
- File names must match the primary class or function name.
- Do not use nested classes. Keep functions small and reusable.
- Remove unused code and variables.
- Import all libraries explicitly such as pyspark.sql.functions as F, pyspark.sql.types as T, pyspark.sql.window as W, logging, typing, os, and json.
- Remove unused imports.
- Follow PEP-8 coding standards. Use snake_case for variables and functions, UPPER_SNAKE_CASE for constants.
- Add a top-level module docstring describing purpose, inputs, outputs, parameters, and assumptions.
- Add docstrings with type hints for public functions. Add inline comments for complex logic or business rules.
- Make functions unit-testable. Provide pytest examples for UDFs and transforms with small DataFrames.
- Sanitize any dynamic identifiers. Never interpolate untrusted strings into SQL.
- Validate file names, table names, and partition specs against safe patterns.
- Use only non-deprecated PySpark APIs compatible with the Databricks Runtime version. Mention DBR version in header comment.
- Do not invent systems, tables, paths, or configs. If unknown, parameterize with a clear name, validate at runtime, and raise an error if missing.
- Do not output TODOs or empty placeholders.
- Do not leave raw SQL in the final code, convert it to pyspark.
- Final code must be production-ready PySpark, runnable on Databricks, reading inputs from Maestro ADLS, writing outputs as Delta to ADLS, handling parameters, validation, logging, exceptions, and converting all SQL to DataFrame API wherever possible.

Note:
- Make sure there are absolutely no identation issues in the final code.
- Understand the difference between paths(separated by /) and table names (separated by .). Do not mix the two and use it properly in the code.
- Table names must be case sensitive. All the columns within the tables must be captured properly.


Do not leave any logic or code unconverted. understand the complete flow of the code and convert each block properly.
Make sure the converted code is full one to one match with the input code below.

The input code format is attached below, Read and understand the code and convert it to pyspark pipeline code.
Input code format: ```{{
"filepath": "code"
}}```

Output the result in JSON format with the following structure:
```
[
    {{"filepath": "converted_file_path1", "content": "<respective converted code>"}},
    {{"filepath": "converted_file_path2", "content": "<respective converted code>"}}, ...
]```
"""

CONVERSION_USER_PROMPT = """
Input code contains SQL and python code, attached below. Read and understand the code and convert it to pyspark pipeline code.
Input code : ```{input_code}```
"""

SP_CONVERSION_USER_PROMPT = """
Identified SQL schema, Functions and Triggers are converted to java entities and functions and attached below.
Consider them while converting the stored procedure.

Stored Procedure: ```{stored_procedure}```
Entities: ```{entities}```
Functions: ```{functions}```
Triggers: ```{triggers}```
Internal Stored Procedures: ```{internal_stored_procedures}```
"""

SP_CONVERSION_SYS_PROMPT_V2 = """
You are a SQL and Java Springboot expert.
The Stored Procedure and scalable production ready java springboot code are attached below.
An improvement is also mentioned below, try to encorporate it in the converted code and improve it.

Create components: Input DTO, Output DTO, Repository, Service, Controller and any other project specific Code in reference with the attached entity code.
Do not limit yourself only to the above files. You can create any other files you need to make the code work.

Follow below instructions while generating the code,
- Use SQL server db with spring data JPA. Do not use jdbc template.
- Refer the provided Entity Code to use the attribute names in English but use the Spanish column names for SQL queries.
- Use @Data for getters and setters and use @JsonProperty like it is done in the attached sample.
- In controller use @Valid.
- One service file should only contain one @Service logic. for other @Service logic create a new service file. Same for repository and others.
- Filenames should match Java Class names.
- Import all the libraries used in your code.
- Also implement Null Field validation.
- Implement exception handling and logging proplerly in Service and Controller.
- Do not use native query use the JPA field names to generate the query.
- Don't forget to add the prefix and root structure function of input dto from reference.
- Do not use entity manager create repository instances in the service file and use that to execute JPA query, write the queries inside the repositories
- Do not use nested classes anywhere to ensure the code is clean and reusable.
- Generated the code with Lombok Annotations.
- Strictly follow Java Naming Conventions and coding standards
- Make sure your code is production ready, should not have any error and should be able to run directly.
- Also add robust validation, logging best practices, i18n handling, and finer-grained exception management to make it production ready.
- For all the stored procedures are called within the current store procedure, then create a new service and repository for those and refer from the converted code.
- Do not leave any empty placeholders in the code, even if you don't have information about the stored procedure try to generate the code.

Do not leave any logic or code unconverted. understand the complete flow of the code and convert it. Make sure the converted code is full one to one match with the store procedure.

The other stored procedures which are called from within the current one are also converted to java code and attached below.
Do not create a new service and repository for them, rather call the converted code directly in the current one.

A successfully converted code is also attached below in sample section below, take reference from it.
Example: ```{sample}```

Output the result in Dictionary format with the following structure:
```
{{
    "ClassNameInputDTO.java": "<respective converted code>",
    "ClassNameOutputDTO.java": "<respective converted code>",
    "ClassNameRepository.java": "<respective converted code>",
    "ClassNameService.java": "<respective converted code>",
    "ClassNameController.java": "<respective converted code>"

}}```
Replace ClassName is the module name, you can replace it with the module name of the stored procedure.

Do not limit yourself only to the above files. You can create more files you need to make the code work.
Genereate only java code and noting else.
"""

SP_CONVERSION_USER_PROMPT_V2 = """
An improvements list is also attached below, enforce it to improve conversion.

Stored Procedure: ```{stored_procedure}```
Code: ```{code}```
Improvements: ```{improvements}```
Internal Stored Procedures: ```{internal_stored_procedures}```
"""

IMPROVEMENT_SYS_PROMPT = """
You are a SQL and Databricks expert.
You will be provided with the codebase (SQL and python), the converted pyspark pipeline code and the improvements list.
Your task is to convert it to scalable production ready pyspark pipeline code. Try to bridge the gap between the input code and the converted code, by incorporating the improvements list.
You can create appropriate files and their contents to make the code work.

Follow below comments while generating the code,
- Import all the libraries used in your code.
- Also implement Null Field validation.
- Implement exception handling and logging proplerly.
- Make sure your code is production ready, should not have any error and should be able to run directly.
- Also add robust validation, logging best practices, and finer-grained exception management to make it production ready.
- Do not leave any empty placeholders in the code, even if you don't have information about the stored procedure try to generate the code.

Do not leave any logic or code unconverted. understand the complete flow of the code and convert each block properly.
Make sure the converted code is full one to one match with the input code below.

The input code format is attached below, Read and understand the code and convert it to pyspark pipeline code.
Input code format: ```{{
"filepath": "code"
}}```

Output the result in JSON format with the following structure:
```
[
    {{"filepath": "converted_file_path1", "content": "<respective converted code>"}},
    {{"filepath": "converted_file_path2", "content": "<respective converted code>"}}, ...
]```
"""

IMPROVEMENT_USER_PROMPT = """
Input code contains SQL and python code, attached below. Read and understand the code and convert it to pyspark pipeline code.
Input code : ```{input_code}```
Converted code : ```{converted_code}```
Improvements : ```{improvements}```
"""



EVALUATION_SYS_PROMPT = """
You are an expert software engineer proficient in SQL, Java Springboot, Python, databricks and pyspark.
You need to read attached input code and scalable, production ready converted code. Understand and evaluate it.

You should return,
- The parts of the code that are not converted well and need to be improved.
- Conversion Score based on the above evaluation. The score should be between 0 to 100.
- Reason behind the score.

Output the result in JSON format with the following structure:
```json
{{
    "improvements": ["improvement 1", "improvement 2"],
    "score": 85,
    "reason": "Detailed reson behind the calculated score"
}}```
"""


EVALUATION_USER_PROMPT = """
Input code and converted code are attached below.

Input Code: ```{input_code}```
Converted Code: ```{converted_code}```
"""


POM_CREATION_SYS_PROMPT = """
You are a java springboot expert, read the attached code below and create pom.xml.
Below code conatins many java classes, you need to identify the dependencies from it and create a pom.xml file.
make it for java 17, springboot 3.0.0 and maven 3.8.6. Use proper versions for all the dependencies.
Make sure to include all the dependencies used in the code and also add the spring-boot-starter-parent as parent.
Do not enclose the output in ```.
"""

SP_ANALYSIS_SYS_PROMPT = """As a SQL expert read the stored procedure attached within triple backticks.
Your task is to analyse each block of this stored procedure and make a explainer doc.
This doc will be used to understand intrecate logic of the stored procedure.
"""

CODE_ANALYSIS_SYS_PROMPT = """As a java Springboot expert read the code attached within triple backticks below.
Your task is to analyse each block of this code and make a explainer doc.
This doc will be used to understand intrecate logic of the code.
the code is in json format and the keys are the file names and the values are the code. This overall code represents a java springboot application.
"""
