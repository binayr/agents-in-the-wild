import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Optional


logger = logging.getLogger(__name__)
@dataclass
class DockerRuntimeConfig:
    """
    Generic runtime configuration to containerize and run any project.
    - language: primary language (e.g., 'java', 'python', 'node')
    - framework: framework hint (e.g., 'springboot', 'fastapi', 'express')
    - image_tag: tag for the built image
    - app_port: container application port (exposed)
    - env: environment variables to pass
    - build_args: docker build args
    - dockerfile_name: custom Dockerfile name if not 'Dockerfile'
    """
    language: str
    framework: Optional[str] = None
    image_tag: str = "aicon-wms/app:latest"
    app_port: int = 8080
    env: Dict[str, str] = field(default_factory=dict)
    build_args: Dict[str, str] = field(default_factory=dict)
    dockerfile_name: str = "Dockerfile"


class DockerAgent:
    def __init__(self) -> None:
        pass

    def ensure_dockerfile(self, project_dir: str, cfg: DockerRuntimeConfig) -> str:
        """
        Create a Dockerfile if not present, based on language/framework.
        Returns the path to the Dockerfile.
        """
        dockerfile_path = os.path.join(project_dir, cfg.dockerfile_name)
        if os.path.exists(dockerfile_path):
            logger.info(f"Dockerfile already exists at {dockerfile_path}")
            return dockerfile_path

        os.makedirs(project_dir, exist_ok=True)

        if cfg.language.lower() == 'java' and (cfg.framework or '').lower() == 'springboot':
            content = self._dockerfile_java_springboot()
        else:
            # Minimal generic Dockerfile that can be adapted later
            content = self._dockerfile_generic()

        with open(dockerfile_path, 'w') as f:
            f.write(content)
        logger.info(f"Created Dockerfile at {dockerfile_path}")
        return dockerfile_path

    def ensure_dockerignore(self, project_dir: str) -> str:
        dockerignore_path = os.path.join(project_dir, '.dockerignore')
        if os.path.exists(dockerignore_path):
            return dockerignore_path
        content = (
            "target\n"
            "out\n"
            "node_modules\n"
            "**/__pycache__\n"
            "**/.pytest_cache\n"
            "**/.mypy_cache\n"
            "**/.DS_Store\n"
            ".git\n"
            ".idea\n"
        )
        with open(dockerignore_path, 'w') as f:
            f.write(content)
        return dockerignore_path

    def build_image(self, project_dir: str, cfg: DockerRuntimeConfig) -> tuple[int, str]:
        cmd = ["docker", "build", "-t", cfg.image_tag, "-f", cfg.dockerfile_name, "."]
        for k, v in (cfg.build_args or {}).items():
            cmd.insert(-1, "--build-arg")
            cmd.insert(-1, f"{k}={v}")
        try:
            logger.info(f"Building docker image: {' '.join(cmd)} in {project_dir}")
            completed = subprocess.run(cmd, cwd=project_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            logger.info(completed.stdout)
            return completed.returncode, completed.stdout
        except FileNotFoundError:
            logger.info("Docker not found. Please install Docker Desktop and ensure 'docker' is on PATH.")
            return 127, "docker not found"
        except Exception as e:
            logger.info(f"Error building image: {e}")
            return 1, str(e)

    def run_container(self, cfg: DockerRuntimeConfig, host_port: Optional[int] = None, detach: bool = True) -> tuple[int, Optional[str], str]:
        host_port = host_port or cfg.app_port
        cmd = [
            "docker", "run",
            "-p", f"{host_port}:{cfg.app_port}",
        ]
        for k, v in (cfg.env or {}).items():
            cmd.extend(["-e", f"{k}={v}"])
        if detach:
            cmd.append("-d")
        cmd.append(cfg.image_tag)
        try:
            logger.info(f"Running docker container: {' '.join(cmd)}")
            completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output = completed.stdout or ""
            logger.info(output)
            container_id = None
            if detach and completed.returncode == 0:
                container_id = output.strip().splitlines()[-1].strip()
            return completed.returncode, container_id, output
        except FileNotFoundError:
            logger.info("Docker not found. Please install Docker Desktop and ensure 'docker' is on PATH.")
            return 127, None, "docker not found"
        except Exception as e:
            logger.info(f"Error running container: {e}")
            return 1, None, str(e)

    def _dockerfile_java_springboot(self) -> str:
        return (
            "# syntax=docker/dockerfile:1\n"
            "FROM maven:3.8.6-eclipse-temurin-17 AS build\n"
            "WORKDIR /workspace\n"
            "COPY pom.xml .\n"
            "COPY src ./src\n"
            "RUN --mount=type=cache,target=/root/.m2 mvn -q -DskipTests package\n"
            "\n"
            "FROM eclipse-temurin:17-jre\n"
            "WORKDIR /app\n"
            "COPY --from=build /workspace/target/*.jar app.jar\n"
            "EXPOSE 8080\n"
            "ENTRYPOINT [\"java\", \"-jar\", \"/app/app.jar\"]\n"
        )

    def _dockerfile_generic(self) -> str:
        # Placeholder generic image; users should replace per runtime
        return (
            "FROM alpine:3.20\n"
            "WORKDIR /app\n"
            "COPY . .\n"
            "CMD [\"sh\", \"-c\", \"echo 'Container started. Replace Dockerfile with runtime-specific build.' && sleep infinity\"]\n"
        )

    def _dockerfile_java_springboot_fallback(self) -> str:
        # More permissive Dockerfile copying the entire context; helpful when build fails due to missing files
        return (
            "# syntax=docker/dockerfile:1\n"
            "FROM maven:3.9.6-eclipse-temurin-17 AS build\n"
            "WORKDIR /workspace\n"
            "COPY . .\n"
            "RUN --mount=type=cache,target=/root/.m2 mvn -q -U -DskipTests package\n"
            "\n"
            "FROM eclipse-temurin:17-jre\n"
            "WORKDIR /app\n"
            "COPY --from=build /workspace/target/*.jar app.jar\n"
            "EXPOSE 8080\n"
            "ENTRYPOINT [\"java\", \"-jar\", \"/app/app.jar\"]\n"
        )

    def attempt_auto_fix(self, project_dir: str, cfg: DockerRuntimeConfig, build_output: str) -> bool:
        """
        Attempt simple automatic fixes for common Docker build issues and rewrite Dockerfile when needed.
        Returns True if a fix was applied and a rebuild should be attempted.
        """
        dockerfile_path = os.path.join(project_dir, cfg.dockerfile_name)
        # Heuristics
        applied_fix = False
        lower = (build_output or "").lower()

        # If jar not found or target missing, fallback to broader COPY and newer Maven image
        if ("no such file or directory" in lower and ("target/" in lower or "/workspace/target" in lower)) or ("copy failed" in lower):
            if cfg.language.lower() == 'java' and (cfg.framework or '').lower() == 'springboot':
                with open(dockerfile_path, 'w') as f:
                    f.write(self._dockerfile_java_springboot_fallback())
                logger.info("Rewrote Dockerfile to fallback Spring Boot multi-stage build.")
                applied_fix = True

        # If still no fix determined, ensure a minimal Dockerfile exists
        if not applied_fix and not os.path.exists(dockerfile_path):
            self.ensure_dockerfile(project_dir, cfg)
            applied_fix = True

        # Ensure .dockerignore for slimmer contexts
        self.ensure_dockerignore(project_dir)
        return applied_fix

    def container_logs(self, container_id: str) -> tuple[int, str]:
        try:
            completed = subprocess.run(["docker", "logs", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return completed.returncode, completed.stdout or ""
        except Exception as e:
            return 1, str(e)

    def is_container_running(self, container_id: str) -> bool:
        try:
            completed = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container_id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            return completed.returncode == 0 and (completed.stdout or "").strip().lower() == "true"
        except Exception:
            return False

