import os
import json
import time
import re
import subprocess
import logging

from agents.element.IdentificationAgent import identification_agent
from agents.element.ConverterAgent import get_conversion_chain
from agents.element.EvaluationAgent import evaluation_agent
from agents.element.ImprovementAgent import sp_improvement_agent
from agents.element.POMAgent import pom_agent
from agents.element.DockerAgent import DockerAgent, DockerRuntimeConfig
from agents.element.CodeAnalysisAgent import code_analysis_agent, sp_analysis_agent
from agents.element.base_utils import read_sql_file, find_from_json, json_to_dict

from typing import Iterable, List, TypeVar

logger = logging.getLogger(__name__)


class SPConverter:
    """
    Stored Procedure Converter class that handles the conversion of SQL stored procedures
    to Java Spring Boot code using AI agents.

    This class orchestrates the entire conversion process including:
    1. Identifying dependencies (entities, functions, triggers)
    2. Converting SQL code to Java Spring Boot code
    3. Evaluating the quality of the conversion
    4. Improving the conversion if needed
    5. Exporting the final code to files
    """
    def __init__(self, name, recursion=False, iterations=2):
        """
        Initialize the SPConverter with the name of the SQL stored procedure file.

        Args:
            name: Name of the SQL stored procedure file to convert
        """
        # Initialize prompt templates for different stages of conversion
        # Generate a unique thread ID based on current timestamp
        self.thread_id = int(time.time())

        # Core properties
        self.name = name
        self.sp = None  # Will store the stored procedure content
        self.code = []  # Will store the generated Java code
        self.sample = ""  # Will store sample code for reference

        # Dependencies
        self.entities = []
        self.functions = []
        self.triggers = []
        self.dependencies = []
        self.recursion = recursion
        self.iterations = iterations

        # Initialize by reading the stored procedure, getting sample code, and preparing output directories
        self.read_sp()
        self.get_sample_code()
        self.prepare_output_folders()

    def read_sp(self) -> None:
        """
        Read the SQL stored procedure file content and store it in memory.
        Logs the size of the stored procedure content.
        """
        if not self.name.endswith(".sql"):
            self.name = f"{self.name}.sql"
        logger.info(f"Reading SP: ../source/StoredProcedure/{self.name}")
        sp = read_sql_file(f"../source/StoredProcedure/{self.name}")
        # logger.info(f"SP text: {sp}")
        tmp = {
            "name": self.name,
            "content": str(sp)
        }

        # logger.info(f"Trigger text length: {len(triggers)}")
        logger.info(f"SP text length: {len(tmp["content"])}")
        self.sp = tmp

    def get_sample_code(self) -> None:
        """
        Read all sample Java files from the sample directory to use as reference
        for the conversion process. Formats the samples with filename headers
        and markdown code blocks.
        """
        sample = ""
        directory = "../source/sample/"
        for filename in os.listdir(directory):
            if filename == ".DS_Store":
                continue
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                sample += f"\n{filename}\n```\n{content}```\n\n"
        self.sample = sample

    def prepare_output_folders(self) -> None:
        """
        Create the necessary output folders where the converted Java code will be stored.
        Each stored procedure gets its own dedicated directory.
        """
        # Create the destination folders
        if not os.path.exists(f"../out/SP/{self.name}"):
            os.makedirs(f"../out/SP/{self.name}")

    def prepare_dependencies(self) -> None:
        """
        Identify and gather the specific dependencies used by the stored procedure.
        Collects the actual Java code for each identified dependency from the metadata files.
        """
        logger.info(f"Starting dependancy identification for {self.name}")
        dependancies = self.identify_dependancies()
        # logger.info(dependancies)
        self.dependancies = dependancies

        logger.info(f"Identified Dependancies: {self.dependancies}")
        # Process entities dependencies
        entities = ""
        for e in self.dependancies.entities:
            entity = find_from_json(f"../metadata/entities.json", key="entity_name", value=f"{e}.java")
            if entity:
                entities += f"{entity['entity_name']}\n{entity['entity']}\n\n"
            else:
                logger.info(f"Error: Could not find entity {e}.java")
        self.entities = entities

        # Process functions dependencies
        functions = ""
        for f in self.dependancies.functions:
            function = find_from_json(f"../metadata/functions.json", key="java_function_name", value=f"{f}.java")
            if function:
                functions += f"{function['java_function_name']}\n{function['java_function']}\n\n"
            else:
                logger.info(f"Error: Could not find Function {f}.java")
        self.functions = functions

        # Process triggers dependencies
        triggers = ""
        for t in self.dependancies.triggers:
            trigger = find_from_json(f"../metadata/triggers.json", key="java_function_name", value=f"{t}.java")
            if trigger:
                triggers += f"{trigger['java_function_name']}\n{trigger['java_function']}\n\n"
            else:
                logger.info(f"Error: Could not find Trigger {t}.java")
        self.triggers = triggers

        ## Recursively run dependencies
        # process internal stored procedures dependencies
        if self.recursion:
            stored_procedures = ""
            for sp in self.dependancies.internal_stored_procedures:
                if not sp.endswith(".sql"):
                    sp = f"{sp}.sql"
                sps = find_from_json(f"../metadata/stored_procedure.json", key=f"{sp}")
                if sps:
                    logger.info(f"Found SP: {sp}")
                    stored_procedures += f"{sp}\n{sps}\n\n"
                else:
                    logger.info(f"Error: Could not find Stored Procedure {sp}.java")
                    tmp_run = SPConverter(sp, recursion=self.recursion, iterations=self.iterations)
                    tmp_run.run()
                del(sps)
            self.stored_procedures = stored_procedures

    def identify_dependancies(self) -> str:
        """
        Use an AI agent to identify which entities, functions, and triggers
        are used by the stored procedure being converted.

        Returns:
            str: JSON string containing the identified dependencies
        """
        try:
            config = {"configurable": {"thread_id": self.thread_id}}
            response = identification_agent.invoke({
                "stored_procedure": self.sp["content"],
                "entities": self.entities,
                "functions": self.functions,
                "triggers": self.triggers
            }, config)

            filename = self.sp["name"].replace(".sql", ".java")

            logger.info(f"exporting {filename}")

            return response
        except Exception as e:
            logger.info(f"Error processing: {e}")

    def convert_sp(self, target_framework: str | None = None) -> str:
        """
        Perform the initial conversion of the SQL stored procedure to Java Spring Boot code.
        Uses an AI agent with the primary conversion prompt template.

        Returns:
            str: JSON string containing the converted Java code
        """
        logger.info(f"Starting conversion for {self.name}")
        try:
            config = {"configurable": {"thread_id":  self.thread_id}}
            agent = get_conversion_chain(target_framework)
            response = agent.invoke({
                "stored_procedure": self.sp["content"],
                "entities": self.entities,
                "functions": self.functions,
                "triggers": self.triggers,
                "sample": self.sample,
                "internal_stored_procedures": self.dependancies.internal_stored_procedures
            }, config)
            # logger.info(response.code)
            # logger.info(response.content.keys())
            self.code = json_to_dict(response.content)
            return self.code
        except Exception as e:
            logger.info(f"Error processing: {e}")
            return ""

    def convert_sp_v2(self, imp) -> str:
        """
        Perform an improved conversion based on evaluation feedback.
        Uses an AI agent with the V2 conversion prompt template that includes
        improvement suggestions from the evaluation phase.

        Returns:
            str: JSON string containing the improved converted Java code
        """
        logger.info(f"Starting conversion for {self.name} with: {imp}")
        thread_id = int(time.time())
        try:
            config = {"configurable": {"thread_id":  thread_id}}
            response = sp_improvement_agent.invoke({
                "stored_procedure": self.sp["content"],
                "code": self.code,
                "sample": self.sample,
                "improvements": imp,
                "internal_stored_procedures": self.dependancies.internal_stored_procedures
            }, config)
            logger.debug(response.content)
            self.code = json_to_dict(response.content)
            return self.code
        except Exception as e:
            logger.info(f"Error processing: {e}, retrying ..")
            # Recursively call the function with the same improvement suggestion
            return self.convert_sp_v2(imp)


    def evaluate_sp(self) -> str:
        """
        Evaluate the quality of the converted Java code against the original SQL.
        Produces a score and improvement suggestions.

        Returns:
            str: JSON string containing evaluation results including score, improvements, and reasons
        """
        logger.info(f"Evaluating conversion for {self.name}")
        try:
            config = {"configurable": {"thread_id":  self.thread_id}}
            response = evaluation_agent.invoke({
                "input_code": self.sp["content"],
                "converted_code": self.code
            }, config)

            return response
        except Exception as e:
            logger.info(f"Error processing: {e}")
            return "{}"

    def create_pom(self) -> None:
        """
        """
        logger.info(f"Creating POM..")
        try:
            if not self.name.endswith(".sql"):
                self.name = f"{self.name}.sql"
            if not self.code:
                self.code = find_from_json(f"../metadata/stored_procedure.json", key=self.name)

            config = {"configurable": {"thread_id":  self.thread_id}}
            response = pom_agent.invoke({
                "code": self.code
            }, config)

            # Write pom.xml inside this SP's project folder
            project_dir = self._get_project_dir()
            os.makedirs(project_dir, exist_ok=True)
            pom_path = os.path.join(project_dir, "pom.xml")
            with open(pom_path, 'w') as file:
                file.write(response.code)
                logger.info(f"Exported pom.xml to {pom_path}")

            return response.code
        except Exception as e:
            logger.info(f"Error processing: {e}")
            return "{}"

    def export_code(self) -> None:
        """
        Export the final converted Java code to files in the output directory.
        Creates one file for each component of the converted code (DTOs, Service, etc).
        """
        logger.info(f"Exporting conversion for {self.name}")
        try:
            ## Export Code
            for filename, content in self.code.items():
                filepath = os.path.join(f"../out/SP/{self.name}", filename)
                with open(filepath, 'w') as file:
                    file.write(content)
                    logger.info(f"Exported {filename} to {filepath}")

            ## Export Evaluation
            with open(f"../out/SP/{self.name}/evaluation.json", 'w') as file:
                file.write(json.dumps(self.evaluation.dict(), indent=4))
                logger.info(f"Exported evaluation to ../out/SP/{self.name}/evaluation.json")

            ## Export Dependancies
            if not os.path.exists(f"../out/SP/{self.name}/dependancies.json"):
                with open(f"../out/SP/{self.name}/dependancies.json", 'w') as file:
                    file.write(json.dumps(self.dependancies.dict(), indent=4))
                    logger.info(f"Exported dependancies to ../out/SP/{self.name}/dependancies.json")
        except Exception as e:
            logger.info(f"Error exporting code: {e}")

    def _get_project_name(self) -> str:
        """Derive a stable project name from the SP filename without extension."""
        return self.name.replace(".sql", "")

    def _get_workspace_root(self) -> str:
        """Absolute path to the repository root (one level above app)."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _get_project_dir(self) -> str:
        """Absolute path to this SP's Maven project directory under out/SP/<name>."""
        return os.path.join(self._get_workspace_root(), "out", "SP", self._get_project_name())

    def arrange_exported_code(self) -> None:
        """
        Arrange exported Java files into a runnable Maven project structure:
        - Create src/main/java and src/main/resources folders
        - Place Java files under directories matching their package declarations
        - Add a default package if missing and move files accordingly
        - Generate a minimal Spring Boot Application class if absent
        - Create a basic application.properties if missing
        """
        try:
            project_dir = self._get_project_dir()
            src_main_java = os.path.join(project_dir, "src", "main", "java")
            src_main_resources = os.path.join(project_dir, "src", "main", "resources")
            os.makedirs(src_main_java, exist_ok=True)
            os.makedirs(src_main_resources, exist_ok=True)

            default_base_package = f"com.aicon.wms.sp.{self._get_project_name().lower()}"
            package_pattern = re.compile(r"^\s*package\s+([a-zA-Z0-9_.]+)\s*;\s*$", re.MULTILINE)

            seen_packages = set()
            file_written_paths = []

            # Use in-memory code map to write files in correct locations
            for filename, content in (self.code or {}).items():
                if not filename.endswith('.java'):
                    # Skip non-java artifacts here
                    continue

                package_match = package_pattern.search(content or "")
                if package_match:
                    package_name = package_match.group(1)
                    target_dir = os.path.join(src_main_java, *package_name.split('.'))
                    os.makedirs(target_dir, exist_ok=True)
                    target_path = os.path.join(target_dir, filename)
                else:
                    # Prepend default package
                    package_name = default_base_package
                    target_dir = os.path.join(src_main_java, *package_name.split('.'))
                    os.makedirs(target_dir, exist_ok=True)
                    content = f"package {package_name};\n\n" + (content or "")
                    target_path = os.path.join(target_dir, filename)

                seen_packages.add(package_name)

                with open(target_path, 'w') as f:
                    f.write(content)
                file_written_paths.append(target_path)
                logger.info(f"Arranged {filename} -> {target_path}")

            # Ensure a Spring Boot Application exists
            has_application_class = any(
                filename.endswith("Application.java") for filename in (self.code or {}).keys()
            )
            base_package = None
            if seen_packages:
                # Choose the shortest package as base (most general)
                base_package = sorted(seen_packages, key=lambda p: len(p))[0]
            else:
                base_package = default_base_package

            if not has_application_class:
                app_class_name = f"{self._get_project_name().title().replace('_', '').replace('-', '')}Application"
                app_package_dir = os.path.join(src_main_java, *base_package.split('.'))
                os.makedirs(app_package_dir, exist_ok=True)
                app_java_path = os.path.join(app_package_dir, f"{app_class_name}.java")
                app_java_content = (
                    f"package {base_package};\n\n"
                    "import org.springframework.boot.SpringApplication;\n"
                    "import org.springframework.boot.autoconfigure.SpringBootApplication;\n\n"
                    "@SpringBootApplication\n"
                    f"public class {app_class_name} {{\n"
                    "    public static void main(String[] args) {\n"
                    f"        SpringApplication.run({app_class_name}.class, args);\n"
                    "    }\n"
                    "}\n"
                )
                with open(app_java_path, 'w') as f:
                    f.write(app_java_content)
                logger.info(f"Created Spring Boot main class at {app_java_path}")

            # Ensure application.properties exists
            app_props_path = os.path.join(src_main_resources, 'application.properties')
            if not os.path.exists(app_props_path):
                with open(app_props_path, 'w') as f:
                    f.write(
                        "server.port=8080\n"
                        "spring.application.name=aicon-wms-sp\n"
                        "spring.main.web-application-type=servlet\n"
                        "spring.jpa.hibernate.ddl-auto=none\n"
                        "spring.jpa.open-in-view=false\n"
                        "logging.level.root=INFO\n"
                    )
                logger.info(f"Created default resources at {app_props_path}")
        except Exception as e:
            logger.info(f"Error arranging exported code: {e}")

    def get_runtime_config(self) -> DockerRuntimeConfig:
        """
        Determine container runtime configuration based on project artifacts.
        Defaults to Java/Spring Boot. Extend this to support other languages/frameworks.
        """
        project_dir = self._get_project_dir()
        image_tag = f"aicon-wms/{self._get_project_name().lower()}:latest"
        if os.path.exists(os.path.join(project_dir, 'pom.xml')):
            return DockerRuntimeConfig(
                language="java",
                framework="springboot",
                image_tag=image_tag,
                app_port=8080,
                env={},
            )
        # Fallback generic runtime
        return DockerRuntimeConfig(
            language="generic",
            framework=None,
            image_tag=image_tag,
            app_port=8080,
            env={},
        )

    def compile_converted_code(self) -> int:
        """
        Compile the generated Maven project with mvn -DskipTests package.
        Returns the process return code (0 = success).
        """
        project_dir = self._get_project_dir()
        mvn_cmd = ["mvn", "-q", "-DskipTests", "package"]
        try:
            logger.info(f"Compiling project with Maven in {project_dir} ...")
            completed = subprocess.run(
                mvn_cmd,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            logger.info(completed.stdout)
            if completed.returncode == 0:
                logger.info("Maven build successful.")
            else:
                logger.info(f"Maven build failed with exit code {completed.returncode}.")
            return completed.returncode
        except FileNotFoundError:
            logger.info("Maven (mvn) not found. Please install Maven and ensure it is on PATH.")
            return 127
        except Exception as e:
            logger.info(f"Error compiling project: {e}")
            return 1

    def run_converted_code(self) -> int:
        """
        Run the compiled application. Prefer executing the built jar; fallback to spring-boot:run.
        Returns the process return code when the process exits (blocking). If using spring-boot:run,
        the method will block until manually terminated.
        """
        project_dir = self._get_project_dir()
        try:
            # Find jar in target
            target_dir = os.path.join(project_dir, 'target')
            jar_path = None
            if os.path.isdir(target_dir):
                for fname in os.listdir(target_dir):
                    if fname.endswith('.jar') and fname.endswith('-sources.jar') is False and fname.endswith('-javadoc.jar') is False:
                        jar_path = os.path.join(target_dir, fname)
                        break

            if jar_path and os.path.exists(jar_path):
                cmd = ["java", "-jar", jar_path]
                logger.info(f"Running jar: {' '.join(cmd)}")
                completed = subprocess.run(cmd, cwd=project_dir)
                logger.info(f"Application exited with code {completed.returncode}")
                return completed.returncode
            else:
                # Fallback to spring-boot:run
                cmd = ["mvn", "-q", "-DskipTests", "spring-boot:run"]
                logger.info(f"Starting application with: {' '.join(cmd)} (this will block)...")
                completed = subprocess.run(cmd, cwd=project_dir)
                logger.info(f"Application exited with code {completed.returncode}")
                return completed.returncode
        except FileNotFoundError as e:
            logger.info(f"Runtime dependency missing: {e}")
            return 127
        except Exception as e:
            logger.info(f"Error running project: {e}")
            return 1

    def save_code(self) -> None:
        if not os.path.exists(f"../metadata/stored_procedure.json"):
            with open(f"../metadata/stored_procedure.json", 'w') as file:
                file.write(json.dumps({f"{self.name}": self.code}, indent=4))
                logger.info(f"Exported dependancies to ../metadata/stored_procedure.json")
        else:
            with open(f"../metadata/stored_procedure.json", 'r') as file:
                data = json.load(file)
                data[f"{self.name}"] = self.code
            with open(f"../metadata/stored_procedure.json", 'w') as file:
                file.write(json.dumps(data, indent=4))
                logger.info(f"Exported dependancies to ../metadata/stored_procedure.json")

    def runV1(self) -> None:
        """
        Execute the first version of the conversion process and evaluate the results.
        Logs the evaluation metrics for analysis.
        """
        logger.info("----------------------- Running V1 -----------------------")
        # For now default to Java/Spring Boot. In future this can be driven via config.
        self.convert_sp(target_framework="flask")
        score = self.evaluate_sp()
        self.evaluation = score
        logger.info("Evaluation V1:")
        logger.info(f"Conversion Score: {self.evaluation.score}%")
        logger.debug(f"Improvements: {self.evaluation.improvements}")
        logger.info(f"Reason: {self.evaluation.reason}")

    def runV2(self) -> None:
        """
        Execute an improved version of the conversion process based on evaluation feedback.
        Used when the initial conversion doesn't meet quality standards.
        Logs the updated evaluation metrics.
        """
        logger.info("----------------------- Running V2 -----------------------")

        # for imp in self.evaluation.improvements[::2]:
        for group_index, group in enumerate(chunked(self.evaluation.improvements, 2), start=1):
            imp = "\n- ".join(group)
            self.convert_sp_v2(imp)
        score = self.evaluate_sp()
        self.evaluation = score
        logger.info("Evaluation V2:")
        logger.info(f"Conversion Score: {self.evaluation.score}%")
        logger.debug(f"Improvements: {self.evaluation.improvements}")
        logger.info(f"Reason: {self.evaluation.reason}")

    def run(self) -> None:
        """
        Main execution method that orchestrates the entire conversion workflow.
        Follows these steps:
        1. Identify and prepare dependencies
        2. Run initial conversion
        3. If quality score is below threshold, run improved conversion
        4. Export the final code
        5. Arrange code into a Maven project and compile it (inside Docker)
        """
        ## Identify Dependant Entities, Functions and Triggers
        self.prepare_dependencies()

        ## Run conversion version 1
        self.runV1()

        for i in range(self.iterations):
            ## Run conversion version 2 if score is less than 90
            if self.evaluation.score < 90:
                logger.info(f"Re-running with V2 with iteration {i+1}")
                self.runV2()

        ## Export the converted code
        self.export_code()
        self.save_code()

        ## Arrange exported code and build/run via Docker for portability
        self.arrange_exported_code()
        self.create_pom()

        project_dir = self._get_project_dir()
        docker_agent = DockerAgent()
        runtime_cfg = self.get_runtime_config()

        docker_agent.ensure_dockerignore(project_dir)
        docker_agent.ensure_dockerfile(project_dir, runtime_cfg)
        build_rc, build_out = docker_agent.build_image(project_dir, runtime_cfg)
        # Persist build logs for debugging
        try:
            with open(os.path.join(project_dir, "docker_build.log"), "w") as f:
                f.write(build_out or "")
        except Exception:
            pass
        if build_rc != 0:
            logger.info("Docker build failed. Attempting auto-fix...")
            if docker_agent.attempt_auto_fix(project_dir, runtime_cfg, build_out):
                build_rc, build_out = docker_agent.build_image(project_dir, runtime_cfg)
                try:
                    with open(os.path.join(project_dir, "docker_build_retry.log"), "w") as f:
                        f.write(build_out or "")
                except Exception:
                    pass
        if build_rc == 0:
            run_rc, container_id, run_out = docker_agent.run_container(runtime_cfg, host_port=8080, detach=True)
            # Save container id and first run output for debugging
            try:
                with open(os.path.join(project_dir, "docker_run.log"), "w") as f:
                    f.write(run_out or "")
                    if container_id:
                        f.write(f"\ncontainer_id={container_id}\n")
            except Exception:
                pass


def analyseSP(sp_name):
    """
    Analyze the stored procedure using the SP analysis agent.
    This function is used to get a detailed explanation of the stored procedure.

    Args:
        sp_name: Name of the SQL stored procedure file to analyze
    """
    try:
        sp = read_sql_file(f"../source/StoredProcedure/{sp_name}")
        response = sp_analysis_agent.invoke({
            "stored_procedure": str(sp)
        })
        logger.info(response.explanation)

        if not os.path.exists(f"out/{sp_name}/"):
            os.makedirs(f"out/{sp_name}/")

        with open(f"out/{sp_name}/SPSpecifications.md", "w") as f:
            f.write(response.explanation)
    except Exception as e:
        logger.info(f"Error processing: {e}")


def analyseCode(sp_name):
    """
    Analyze the Java code using the code analysis agent.
    This function is used to get a detailed explanation of the Java code.

    Args:
        code_name: Name of the Java code file to analyze
    """
    try:
        code = find_from_json(f"../metadata/stored_procedure.json", key=sp_name)
        response = code_analysis_agent.invoke({
            "stored_procedure": code
        })
        logger.info(response.explanation)

        if not os.path.exists(f"out/{sp_name}/"):
            os.makedirs(f"out/{sp_name}/")

        with open(f"out/{sp_name}/CodeSpecifications.md", "w") as f:
            f.write(response.explanation)
    except Exception as e:
        logger.info(f"Error processing: {e}")


def improve_existing_solution(sp_name):
    """
    Improve the existing solution using the improvement agent.
    This function is used to get suggestions for improving the Java code.

    Args:
        sp_name: Name of the SQL stored procedure file to improve
    """
    try:
        sp = read_sql_file(f"../source/StoredProcedure/{sp_name}")
        code = find_from_json(f"../metadata/stored_procedure.json", key=sp_name)

        sample = ""
        directory = "../source/sample/"
        for filename in os.listdir(directory):
            if filename == ".DS_Store":
                continue
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                sample += f"\n{filename}\n```\n{content}```\n\n"

        with open(f"out/SP/{sp_name}/dependancies.json") as f:
            improvements = json.load(f.read())
            improvements = improvements["improvements"]
        logger.info(improvements)

        code = find_from_json(f"../metadata/stored_procedure.json", key=sp_name)
        response = sp_improvement_agent.invoke({
            "stored_procedure": sp,
            "code": code,
            "sample": sample,
            "improvements": improvements
        })
        logger.debug(response.content)
        code = json_to_dict(response.content)

        if not os.path.exists(f"../metadata/stored_procedureV3.json"):
            with open(f"../metadata/stored_procedureV3.json", 'w') as file:
                file.write(json.dumps({f"{sp_name}": code}, indent=4))
                logger.info(f"Exported dependancies to ../metadata/stored_procedureV3.json")
        else:
            with open(f"../metadata/stored_procedure.json", 'r') as file:
                data = json.load(file)
                data[f"{sp_name}"] = code
            with open(f"../metadata/stored_procedure.json", 'w') as file:
                file.write(json.dumps(data, indent=4))
                logger.info(f"Exported dependancies to ../metadata/stored_procedureV3.json")

        return code
    except Exception as e:
        logger.info(f"Error processing: {e}")



T = TypeVar("T")
def chunked(items: List[T], chunk_size: int) -> Iterable[List[T]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    for start_index in range(0, len(items), chunk_size):
        yield items[start_index:start_index + chunk_size]


## TODO:
# 1. Function selection ✅
# 2. SP identification and selection ✅
# 3. score improvement ✅
# 4. export evaluation ✅
# 5. SP registration, discovery and usage ✅
# 6. Prompt History ✅
# 7. Agentic ✅
# 8. SP/code analysis ✅
