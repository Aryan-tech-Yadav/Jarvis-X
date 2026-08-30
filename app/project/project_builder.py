from app.project.project_planner import ProjectPlanner
from app.project.project_generator import ProjectGenerator
from app.project.project_designer import ProjectDesigner
from app.project.project_writer import ProjectWriter
from app.project.project_fixer import ProjectFixer
from app.agent.file_manager import FileManager
from app.project.project_tester import ProjectTester
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
    
    def __init__(self):
        self.planner = ProjectPlanner()
        self.generator = ProjectGenerator()
        self.designer = ProjectDesigner()
        self.writer = ProjectWriter()
        self.fixer = ProjectFixer()
        self.tester = ProjectTester()
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
        """Build project from template."""
        project_name = project_name or augmented.get("template_name", "template_project")
        if base_path is None:
            base_path = os.path.join("workspace", project_name)

        if os.path.exists(base_path):
            shutil.rmtree(base_path)
        os.makedirs(base_path, exist_ok=True)

        files = augmented.get("files", {})
        for filename, content in files.items():
            file_path = os.path.join(base_path, filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Generate requirements if tech stack available
        tech_stack = augmented.get("tech_stack", {})
        frameworks = tech_stack.get("frameworks", [])
        if frameworks and "requirements.txt" not in files:
            req_path = os.path.join(base_path, "requirements.txt")
            with open(req_path, "w", encoding="utf-8") as f:
                f.write("\n".join(frameworks) + "\n")
            Logger.success(f"Requirements generated: {req_path}")

        # Generate README if not present
        if "README.md" not in files:
            readme_path = os.path.join(base_path, "README.md")
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"# {project_name}\n\n{augmented.get('template_name', 'Template project')}\n")
            Logger.success(f"README generated: {readme_path}")

        return base_path
    
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
            