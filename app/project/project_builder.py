from app.project.project_planner import ProjectPlanner
from app.project.project_generator import ProjectGenerator
from app.project.project_designer import ProjectDesigner
from app.project.project_writer import ProjectWriter
from app.project.project_fixer import ProjectFixer
from app.agent.file_manager import FileManager
from app.project.project_tester import ProjectTester
from app.project.project_static_validator import ProjectStaticValidator
from app.project.project_runner import ProjectRunner
from app.project.project_runtime_fixer import ProjectRuntimeFixer
from app.project.project_validator import ProjectValidator
from app.project.project_retry import ProjectRetry
from app.context.context_manager import ContextManager
from app.project.project_dependency_manager import ProjectDependencyManager
from app.project.project_readme_generator import ProjectReadmeGenerator
from app.project.project_repair_manager import ProjectRepairManager
from app.core.logger import Logger
import os
import shutil

class ProjectBuilder:
    
    def __init__(self, use_reconnaissance=False):
        self.planner = ProjectPlanner(
            use_reconnaissance=use_reconnaissance
        )
        self.generator = ProjectGenerator()
        self.designer = ProjectDesigner()
        self.writer = ProjectWriter()
        self.fixer = ProjectFixer()
        self.tester = ProjectTester()
        self.static_tester = ProjectStaticValidator()
        self.runner = ProjectRunner()
        self.runtime_fixer = ProjectRuntimeFixer()
        self.validator = ProjectValidator()
        self.retry = ProjectRetry()
        self.context = ContextManager()
        self.dependencies = ProjectDependencyManager()
        self.readme = ProjectReadmeGenerator()
        self.repair = ProjectRepairManager()
        self.files = FileManager()
        
    def build(self, prompt, project_name=None, base_path=None, folders=None):
        from app.engineering.project_type_detector import ProjectTypeDetector
        from app.knowledge.template_store import TemplateRetriever, TemplateAugmentedGenerator

        detector = ProjectTypeDetector()
        retriever = TemplateRetriever()
        generator = TemplateAugmentedGenerator(retriever)

        detection = detector.detect(prompt)
        tech_stack = detection.tech_stack

        Logger.info(f"[ProjectBuilder] Detected: {detection.project_type.value} | Template: {tech_stack.template_id}")

        # Try template-augmented generation first
        augmented = generator.generate_with_context(prompt, detection.project_type.value)
        if augmented.get("augmented") and augmented.get("files"):
            return self._build_from_template(augmented, project_name, base_path)

        # Standard generation
        project = self.planner.plan(prompt, project_name=project_name, folders=folders)
        if not project:
            project = {
                "project_name": project_name or "unnamed_project",
                "folders": folders or ["src", "tests"],
                "files": [{"name": "main.py", "content": ""}],
            }

        base_path = self.generator.create_project(project, base_path=base_path)
        generated_files = self.generate_files(project, base_path)

        passed = False
        output = ""
        for attempt in self.retry.attempts():
            static_passed = False
            static_message = ""

            # Initial validation plus at most two repair attempts.
            for repair_attempt in range(3):
                static_passed, static_message = (
                    self.static_tester.validate_project(base_path)
                )
                Logger.info(f"STATIC VALIDATION: {static_message}")

                if static_passed:
                    break

                Logger.warning(
                    f"Static validation failed (attempt {repair_attempt + 1}/3)."
                )

                if repair_attempt == 2:
                    break

                repair_lines = []
                for line in static_message.splitlines():
                    if line.startswith("Syntax/read error in "):
                        location, detail = line.split(": ", 1)
                        file_name = location.removeprefix(
                            "Syntax/read error in "
                        ).strip()
                        if file_name.endswith(".py"):
                            repair_lines.append(
                                f"Syntax error in {file_name}: {detail}"
                            )
                        continue

                    if ": " not in line:
                        continue

                    location, detail = line.split(": ", 1)
                    file_name = location.rsplit(":", 1)[0]
                    if file_name.endswith(".py"):
                        repair_lines.append(
                            f"Invalid import in {file_name}: {detail}"
                        )

                if not repair_lines:
                    Logger.warning(
                        "No repairable file references found; stopping auto-repair."
                    )
                    break

                repaired_files = self.repair.repair(
                    project,
                    base_path,
                    "\n".join(repair_lines),
                )
                if not repaired_files:
                    Logger.warning("Auto-repair produced no accepted file changes.")
                    break

                Logger.info(
                    f"Static auto-repair changed: {', '.join(repaired_files)}"
                )

            if not static_passed:
                passed = False
                output = static_message
                Logger.error(
                    "Static validation failed; refusing to execute generated project."
                )
                break

            passed, output = self.runner.run(base_path)
            Logger.info("RUN RESULT" if attempt == 0 else f"RETRY {attempt} RESULT")
            if output:
                Logger.info(output)

            if passed:
                break

            Logger.error("Runtime Error Detected")
            runtime_file = self._find_runtime_file(generated_files, output)
            if not runtime_file or attempt == self.retry.max_attempts - 1:
                break

            file_info, code, file_path = runtime_file
            fixed_code = self.runtime_fixer.fix(
                project,
                file_info,
                code,
                output,
            )

            if not fixed_code:
                break

            fix_passed, fix_message = self.tester.test(file_info, fixed_code)
            if not fix_passed:
                Logger.warning(f"Runtime fix rejected for {file_info['name']}: {fix_message}")
                break

            Logger.success("Runtime Fix Generated")
            self.files.overwrite_file(file_path, fixed_code)
            generated_files[generated_files.index(runtime_file)] = (
                file_info,
                fixed_code,
                file_path,
            )

        if not passed:
            Logger.error("Still Failed")

        requirements_path = self.dependencies.generate_requirements(base_path)
        Logger.success(f"Requirements generated: {requirements_path}")

        readme_path = self.readme.generate(project, base_path)
        Logger.success(f"README generated: {readme_path}")

        valid, validation_message = self.validator.validate(project, base_path)
        Logger.info("VALIDATION RESULT")
        Logger.info(validation_message)

        if not valid:
            repaired_files = self.repair.repair(project, base_path, validation_message)
            if repaired_files:
                Logger.success(f"Repaired: {', '.join(repaired_files)}")
                valid, validation_message = self.validator.validate(project, base_path)
                Logger.info("VALIDATION AFTER REPAIR")
                Logger.info(validation_message)

        return base_path

    def _build_from_template(self, augmented, project_name=None, base_path=None):
        """Build a template project after validating all output paths."""
        project_name = project_name or augmented.get(
            "template_name", "template_project"
        )
        if base_path is None:
            base_path = os.path.join("workspace", project_name)

        requested_root = os.path.abspath(base_path)
        if os.path.islink(requested_root):
            raise ValueError("Template project path cannot be a symlink")
        root = os.path.realpath(requested_root)

        files = augmented.get("files", {})
        if not isinstance(files, dict):
            raise ValueError("Template files must be a mapping")

        # Validate ALL paths before replacing an existing project.
        validated_files = []
        for filename, content in files.items():
            try:
                relative = os.fspath(filename)
            except TypeError as exc:
                raise ValueError("Template filenames must be path strings") from exc

            if not isinstance(relative, str) or not relative:
                raise ValueError("Template filenames must be non-empty strings")
            if os.path.isabs(relative):
                raise ValueError("Absolute template file paths are not allowed")
            if not isinstance(content, str):
                raise ValueError(
                    f"Template content for {relative!r} must be text"
                )

            file_path = os.path.realpath(os.path.join(root, relative))
            try:
                inside_root = os.path.commonpath([root, file_path]) == root
            except ValueError:
                inside_root = False

            if not inside_root or file_path == root:
                raise ValueError("Template file path escapes the project")

            validated_files.append((file_path, content))

        # Only replace the existing directory after path preflight succeeds.
        os.makedirs(os.path.dirname(root), exist_ok=True)

        if os.path.islink(requested_root):
            raise ValueError("Template project path cannot be a symlink")

        if os.path.exists(root):
            if not os.path.isdir(root):
                raise ValueError("Template project path must be a directory")
            shutil.rmtree(root)

        os.makedirs(root, exist_ok=True)

        for file_path, content in validated_files:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(content)

        tech_stack = augmented.get("tech_stack", {})
        frameworks = tech_stack.get("frameworks", [])
        if frameworks and "requirements.txt" not in files:
            with open(os.path.join(root, "requirements.txt"), "w",
                      encoding="utf-8") as handle:
                handle.write("\n".join(frameworks) + "\n")

        if "README.md" not in files:
            with open(os.path.join(root, "README.md"), "w",
                      encoding="utf-8") as handle:
                handle.write(
                    f"# {project_name}\n\n"
                    f"{augmented.get('template_name', 'Template project')}\n"
                )

        passed, message = self.static_tester.validate_project(root)
        Logger.info(f"TEMPLATE STATIC VALIDATION: {message}")

        if not passed:
            raise ValueError(
                f"Template project failed static validation: {message}"
            )

        return root

    def generate_files(self, project, base_path):
        generated_files = []

        for file_info in project["files"]:
            design = self.designer.design(project, file_info)
            if design is None:
                continue
            context = self.context.get_context(project, file_info, base_path)
            code = self.writer.write_file(project, file_info, design, context)
            if not code:
                continue
            
            fixed_code = self.fixer.fix(project, file_info, code)
            if fixed_code:
                code = fixed_code
                
            passed, message = self.tester.test( file_info, code)
            
            Logger.info(f"{file_info['name']}: {message}")
            
            if not passed:
                Logger.warning(f"Skipping {file_info['name']}: {message}")
                continue
            
            file_path = os.path.join(base_path, file_info["name"])
            self.files.overwrite_file(file_path, code)
            generated_files.append((file_info, code, file_path))

        return generated_files

    def _find_runtime_file(self, generated_files, runtime_error):
        for file_info, code, file_path in generated_files:
            if file_info["name"] in runtime_error:
                return file_info, code, file_path

        return generated_files[0] if generated_files else None
            