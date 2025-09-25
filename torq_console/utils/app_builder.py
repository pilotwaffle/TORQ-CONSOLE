"""
App/Website Building Toolkit for TORQ Console.

Provides comprehensive tools for building modern web applications and websites
with support for React, Vue, Node.js, databases, and deployment automation.
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess
import shutil


class ProjectType(Enum):
    """Supported project types."""
    REACT_APP = "react"
    VUE_APP = "vue"
    NODE_API = "node-api"
    EXPRESS_API = "express-api"
    STATIC_SITE = "static"
    FULL_STACK = "fullstack"
    NEXTJS_APP = "nextjs"
    VITE_APP = "vite"


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"


@dataclass
class ProjectConfig:
    """Configuration for a new project."""
    name: str
    type: ProjectType
    path: str
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    database: Optional[DatabaseType] = None
    features: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)


@dataclass
class ComponentSpec:
    """Specification for a UI component."""
    name: str
    type: str  # functional, class, page, layout
    props: Dict[str, str] = field(default_factory=dict)
    state: Dict[str, str] = field(default_factory=dict)
    hooks: List[str] = field(default_factory=list)
    styling: str = "css"  # css, scss, styled-components, tailwind
    tests: bool = True


class AppBuilderToolkit:
    """
    Comprehensive app and website building toolkit.

    Features:
    - Project scaffolding for multiple frameworks
    - Component generation with best practices
    - Database schema management
    - API endpoint generation
    - Docker containerization
    - CI/CD pipeline setup
    - Code quality tools integration
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Framework templates and configurations
        self.framework_configs = {
            ProjectType.REACT_APP: {
                'create_command': 'npx create-react-app',
                'dev_command': 'npm start',
                'build_command': 'npm run build',
                'test_command': 'npm test',
                'default_port': 3000
            },
            ProjectType.VUE_APP: {
                'create_command': 'npx @vue/cli create',
                'dev_command': 'npm run serve',
                'build_command': 'npm run build',
                'test_command': 'npm run test:unit',
                'default_port': 8080
            },
            ProjectType.NEXTJS_APP: {
                'create_command': 'npx create-next-app',
                'dev_command': 'npm run dev',
                'build_command': 'npm run build',
                'test_command': 'npm test',
                'default_port': 3000
            },
            ProjectType.VITE_APP: {
                'create_command': 'npm create vite@latest',
                'dev_command': 'npm run dev',
                'build_command': 'npm run build',
                'test_command': 'npm test',
                'default_port': 5173
            }
        }

        # Component templates
        self.component_templates = {
            'react_functional': self._react_functional_template,
            'react_class': self._react_class_template,
            'vue_composition': self._vue_composition_template,
            'vue_options': self._vue_options_template
        }

    async def create_project(self, config: ProjectConfig) -> Dict[str, Any]:
        """
        Create a new app/website project with full scaffolding.

        Args:
            config: Project configuration

        Returns:
            Project creation result with details
        """
        start_time = datetime.now()

        try:
            project_path = Path(config.path) / config.name

            # Check if project directory already exists
            if project_path.exists():
                return {
                    'success': False,
                    'error': f'Project directory already exists: {project_path}',
                    'project_path': str(project_path)
                }

            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)

            # Initialize project based on type
            init_result = await self._initialize_project(config, project_path)
            if not init_result['success']:
                return init_result

            # Add additional features and configurations
            if config.database:
                await self._setup_database_integration(project_path, config.database)

            if config.features:
                await self._add_project_features(project_path, config)

            # Setup development tools
            await self._setup_dev_tools(project_path, config)

            # Generate documentation
            await self._generate_project_docs(project_path, config)

            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                'success': True,
                'project_name': config.name,
                'project_type': config.type.value,
                'project_path': str(project_path),
                'framework_config': self.framework_configs.get(config.type, {}),
                'database': config.database.value if config.database else None,
                'features': config.features,
                'setup_time_seconds': round(processing_time, 2),
                'next_steps': [
                    f"cd {project_path}",
                    "npm install",
                    "npm run dev"
                ]
            }

        except Exception as e:
            self.logger.error(f"Project creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'project_name': config.name
            }

    async def generate_component(
        self,
        project_path: str,
        component_spec: ComponentSpec,
        framework: str = "react"
    ) -> Dict[str, Any]:
        """
        Generate a new UI component with tests and documentation.

        Args:
            project_path: Path to the project
            component_spec: Component specification
            framework: Target framework (react, vue, etc.)

        Returns:
            Component generation result
        """
        try:
            project_root = Path(project_path)
            components_dir = project_root / "src" / "components"
            components_dir.mkdir(parents=True, exist_ok=True)

            component_dir = components_dir / component_spec.name
            component_dir.mkdir(exist_ok=True)

            # Generate component file
            template_key = f"{framework}_{component_spec.type}"
            if template_key in self.component_templates:
                component_code = await self.component_templates[template_key](component_spec)

                # Determine file extension
                extension = '.jsx' if framework == 'react' else '.vue'
                component_file = component_dir / f"{component_spec.name}{extension}"

                with open(component_file, 'w', encoding='utf-8') as f:
                    f.write(component_code)

                generated_files = [str(component_file)]

                # Generate test file
                if component_spec.tests:
                    test_file = await self._generate_component_test(
                        component_dir, component_spec, framework
                    )
                    if test_file:
                        generated_files.append(test_file)

                # Generate story file (Storybook)
                story_file = await self._generate_component_story(
                    component_dir, component_spec, framework
                )
                if story_file:
                    generated_files.append(story_file)

                # Generate CSS file
                if component_spec.styling in ['css', 'scss']:
                    css_extension = '.scss' if component_spec.styling == 'scss' else '.css'
                    css_file = component_dir / f"{component_spec.name}{css_extension}"

                    css_content = await self._generate_component_styles(component_spec)
                    with open(css_file, 'w', encoding='utf-8') as f:
                        f.write(css_content)

                    generated_files.append(str(css_file))

                return {
                    'success': True,
                    'component_name': component_spec.name,
                    'component_type': component_spec.type,
                    'framework': framework,
                    'component_path': str(component_dir),
                    'generated_files': generated_files,
                    'styling': component_spec.styling,
                    'has_tests': component_spec.tests
                }
            else:
                return {
                    'success': False,
                    'error': f'Unsupported component template: {template_key}',
                    'component_name': component_spec.name
                }

        except Exception as e:
            self.logger.error(f"Component generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'component_name': component_spec.name
            }

    async def generate_api_endpoint(
        self,
        project_path: str,
        endpoint_name: str,
        method: str = "GET",
        database_table: Optional[str] = None,
        auth_required: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a REST API endpoint with CRUD operations.

        Args:
            project_path: Path to the project
            endpoint_name: Name of the endpoint (e.g., 'users', 'posts')
            method: HTTP method (GET, POST, PUT, DELETE, ALL)
            database_table: Optional database table name
            auth_required: Whether authentication is required

        Returns:
            API endpoint generation result
        """
        try:
            project_root = Path(project_path)
            api_dir = project_root / "src" / "api" / "routes"
            api_dir.mkdir(parents=True, exist_ok=True)

            # Generate route file
            route_file = api_dir / f"{endpoint_name}.js"

            route_code = await self._generate_express_route(
                endpoint_name, method, database_table, auth_required
            )

            with open(route_file, 'w', encoding='utf-8') as f:
                f.write(route_code)

            # Generate controller file
            controllers_dir = project_root / "src" / "api" / "controllers"
            controllers_dir.mkdir(parents=True, exist_ok=True)

            controller_file = controllers_dir / f"{endpoint_name}Controller.js"
            controller_code = await self._generate_express_controller(
                endpoint_name, database_table
            )

            with open(controller_file, 'w', encoding='utf-8') as f:
                f.write(controller_code)

            # Generate model file if database table specified
            model_file = None
            if database_table:
                models_dir = project_root / "src" / "models"
                models_dir.mkdir(parents=True, exist_ok=True)

                model_file = models_dir / f"{endpoint_name}Model.js"
                model_code = await self._generate_database_model(endpoint_name, database_table)

                with open(model_file, 'w', encoding='utf-8') as f:
                    f.write(model_code)

            # Generate test file
            tests_dir = project_root / "tests" / "api"
            tests_dir.mkdir(parents=True, exist_ok=True)

            test_file = tests_dir / f"{endpoint_name}.test.js"
            test_code = await self._generate_api_tests(endpoint_name, method, auth_required)

            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)

            generated_files = [str(route_file), str(controller_file), str(test_file)]
            if model_file:
                generated_files.append(str(model_file))

            return {
                'success': True,
                'endpoint_name': endpoint_name,
                'method': method,
                'route_path': f"/api/{endpoint_name}",
                'generated_files': generated_files,
                'auth_required': auth_required,
                'database_integration': bool(database_table)
            }

        except Exception as e:
            self.logger.error(f"API endpoint generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'endpoint_name': endpoint_name
            }

    async def setup_database_schema(
        self,
        project_path: str,
        schema_name: str,
        database_type: DatabaseType,
        tables: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Setup database schema with migrations and models.

        Args:
            project_path: Path to the project
            schema_name: Name of the database schema
            database_type: Type of database
            tables: List of table definitions

        Returns:
            Database setup result
        """
        try:
            project_root = Path(project_path)
            db_dir = project_root / "database"
            migrations_dir = db_dir / "migrations"
            schemas_dir = db_dir / "schemas"

            db_dir.mkdir(exist_ok=True)
            migrations_dir.mkdir(exist_ok=True)
            schemas_dir.mkdir(exist_ok=True)

            generated_files = []

            # Generate database configuration
            config_file = db_dir / "config.js"
            config_code = await self._generate_database_config(database_type, schema_name)

            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_code)
            generated_files.append(str(config_file))

            # Generate migrations for each table
            for i, table in enumerate(tables):
                migration_file = migrations_dir / f"{str(i+1).zfill(3)}_{table['name']}.sql"
                migration_code = await self._generate_migration_sql(table, database_type)

                with open(migration_file, 'w', encoding='utf-8') as f:
                    f.write(migration_code)
                generated_files.append(str(migration_file))

                # Generate model for each table
                model_file = project_root / "src" / "models" / f"{table['name']}.js"
                model_file.parent.mkdir(parents=True, exist_ok=True)

                model_code = await self._generate_orm_model(table, database_type)
                with open(model_file, 'w', encoding='utf-8') as f:
                    f.write(model_code)
                generated_files.append(str(model_file))

            # Generate database initialization script
            init_file = db_dir / "init.js"
            init_code = await self._generate_database_init(database_type, tables)

            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(init_code)
            generated_files.append(str(init_file))

            return {
                'success': True,
                'schema_name': schema_name,
                'database_type': database_type.value,
                'tables_count': len(tables),
                'generated_files': generated_files,
                'migration_files': len(tables),
                'next_steps': [
                    "npm install database dependencies",
                    f"Run migrations: node database/init.js",
                    "Update environment variables with database credentials"
                ]
            }

        except Exception as e:
            self.logger.error(f"Database schema setup failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'schema_name': schema_name
            }

    async def containerize_project(
        self,
        project_path: str,
        include_database: bool = True,
        production_ready: bool = False
    ) -> Dict[str, Any]:
        """
        Create Docker configuration for the project.

        Args:
            project_path: Path to the project
            include_database: Whether to include database in Docker setup
            production_ready: Whether to optimize for production

        Returns:
            Containerization result
        """
        try:
            project_root = Path(project_path)

            # Generate Dockerfile
            dockerfile_content = await self._generate_dockerfile(project_root, production_ready)
            dockerfile_path = project_root / "Dockerfile"

            with open(dockerfile_path, 'w', encoding='utf-8') as f:
                f.write(dockerfile_content)

            # Generate docker-compose.yml
            compose_content = await self._generate_docker_compose(project_root, include_database)
            compose_path = project_root / "docker-compose.yml"

            with open(compose_path, 'w', encoding='utf-8') as f:
                f.write(compose_content)

            # Generate .dockerignore
            dockerignore_content = await self._generate_dockerignore()
            dockerignore_path = project_root / ".dockerignore"

            with open(dockerignore_path, 'w', encoding='utf-8') as f:
                f.write(dockerignore_content)

            # Generate environment files
            env_example_path = project_root / ".env.example"
            env_content = await self._generate_env_template(include_database)

            with open(env_example_path, 'w', encoding='utf-8') as f:
                f.write(env_content)

            generated_files = [
                str(dockerfile_path),
                str(compose_path),
                str(dockerignore_path),
                str(env_example_path)
            ]

            return {
                'success': True,
                'project_path': str(project_root),
                'generated_files': generated_files,
                'includes_database': include_database,
                'production_ready': production_ready,
                'docker_commands': [
                    "docker-compose build",
                    "docker-compose up -d",
                    "docker-compose logs -f"
                ]
            }

        except Exception as e:
            self.logger.error(f"Project containerization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'project_path': str(project_path)
            }

    # Private implementation methods
    async def _initialize_project(self, config: ProjectConfig, project_path: Path) -> Dict[str, Any]:
        """Initialize project based on type."""
        try:
            framework_config = self.framework_configs.get(config.type)
            if not framework_config:
                return {'success': False, 'error': f'Unsupported project type: {config.type.value}'}

            # Generate package.json
            package_json = {
                "name": config.name,
                "version": config.version,
                "description": config.description,
                "author": config.author,
                "private": True,
                "scripts": {
                    "dev": framework_config['dev_command'].replace('npm run ', ''),
                    "build": framework_config['build_command'].replace('npm run ', ''),
                    "test": framework_config['test_command'].replace('npm run ', ''),
                    "start": "node server.js"
                },
                "dependencies": {},
                "devDependencies": {}
            }

            # Add framework-specific dependencies
            if config.type == ProjectType.REACT_APP:
                package_json["dependencies"].update({
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-scripts": "5.0.1"
                })
            elif config.type == ProjectType.VUE_APP:
                package_json["dependencies"].update({
                    "vue": "^3.3.0",
                    "@vue/cli-service": "^5.0.0"
                })
            elif config.type == ProjectType.NEXTJS_APP:
                package_json["dependencies"].update({
                    "next": "^14.0.0",
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0"
                })

            # Add custom dependencies
            for dep in config.dependencies:
                package_json["dependencies"][dep] = "latest"

            for dev_dep in config.dev_dependencies:
                package_json["devDependencies"][dev_dep] = "latest"

            # Write package.json
            with open(project_path / "package.json", 'w', encoding='utf-8') as f:
                json.dump(package_json, f, indent=2)

            # Create basic project structure
            await self._create_project_structure(project_path, config.type)

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _create_project_structure(self, project_path: Path, project_type: ProjectType):
        """Create basic project directory structure."""
        directories = [
            "src",
            "src/components",
            "src/pages",
            "src/utils",
            "src/api",
            "src/api/routes",
            "src/api/controllers",
            "src/models",
            "tests",
            "public",
            "docs"
        ]

        for directory in directories:
            (project_path / directory).mkdir(parents=True, exist_ok=True)

        # Create basic index files
        if project_type == ProjectType.REACT_APP:
            # Create src/App.js
            app_content = '''import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to {project_name}</h1>
        <p>Built with TORQ Console App Builder</p>
      </header>
    </div>
  );
}

export default App;'''.replace('{project_name}', project_path.name)

            with open(project_path / "src" / "App.js", 'w', encoding='utf-8') as f:
                f.write(app_content)

        # Create basic README
        readme_content = f'''# {project_path.name}

Generated with TORQ Console App Builder

## Getting Started

```bash
npm install
npm run dev
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run test` - Run tests

## Project Structure

- `src/` - Source code
- `src/components/` - Reusable components
- `src/pages/` - Page components
- `src/api/` - API routes and controllers
- `tests/` - Test files
- `docs/` - Documentation
'''

        with open(project_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)

    async def _setup_database_integration(self, project_path: Path, database_type: DatabaseType):
        """Setup database integration for the project."""
        # Add database-specific dependencies to package.json
        package_json_path = project_path / "package.json"

        if package_json_path.exists():
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)

            # Add database dependencies
            if database_type == DatabaseType.POSTGRESQL:
                package_data["dependencies"]["pg"] = "^8.11.0"
                package_data["devDependencies"]["@types/pg"] = "^8.10.0"
            elif database_type == DatabaseType.MYSQL:
                package_data["dependencies"]["mysql2"] = "^3.6.0"
            elif database_type == DatabaseType.MONGODB:
                package_data["dependencies"]["mongodb"] = "^6.0.0"
                package_data["dependencies"]["mongoose"] = "^7.5.0"
            elif database_type == DatabaseType.SQLITE:
                package_data["dependencies"]["sqlite3"] = "^5.1.6"

            # Always add ORM
            package_data["dependencies"]["sequelize"] = "^6.32.0"

            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(package_data, f, indent=2)

    async def _add_project_features(self, project_path: Path, config: ProjectConfig):
        """Add additional features to the project."""
        # Implementation for adding features like authentication, testing, etc.
        pass

    async def _setup_dev_tools(self, project_path: Path, config: ProjectConfig):
        """Setup development tools like ESLint, Prettier, etc."""
        # Create .gitignore
        gitignore_content = '''node_modules/
dist/
build/
.env
.env.local
.DS_Store
*.log
coverage/
.nyc_output/
'''

        with open(project_path / ".gitignore", 'w', encoding='utf-8') as f:
            f.write(gitignore_content)

    async def _generate_project_docs(self, project_path: Path, config: ProjectConfig):
        """Generate project documentation."""
        docs_dir = project_path / "docs"

        # Create API documentation template
        api_docs = '''# API Documentation

## Endpoints

### GET /api/health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

## Authentication

This project uses JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```
'''

        with open(docs_dir / "API.md", 'w', encoding='utf-8') as f:
            f.write(api_docs)

    # Component template methods
    async def _react_functional_template(self, spec: ComponentSpec) -> str:
        """Generate React functional component template."""
        imports = ["import React"]

        if spec.hooks:
            hook_imports = [f"use{hook.capitalize()}" for hook in spec.hooks]
            imports[0] += f", {{ {', '.join(hook_imports)} }}"

        imports[0] += " from 'react';"

        if spec.styling == "css":
            imports.append(f"import './{spec.name}.css';")

        props_interface = ""
        if spec.props:
            props_list = [f"{prop}: {prop_type}" for prop, prop_type in spec.props.items()]
            props_interface = f"interface {spec.name}Props {{\n  " + ";\n  ".join(props_list) + ";\n}"

        component_code = f'''
{chr(10).join(imports)}

{props_interface}

const {spec.name} = ({', '.join(spec.props.keys()) if spec.props else ''}) => {{
  // Component implementation
  return (
    <div className="{spec.name.lower()}">
      <h2>{spec.name}</h2>
      <p>Generated component</p>
    </div>
  );
}};

export default {spec.name};
'''

        return component_code.strip()

    async def _vue_composition_template(self, spec: ComponentSpec) -> str:
        """Generate Vue composition API component template."""
        component_code = f'''<template>
  <div class="{spec.name.lower()}">
    <h2>{spec.name}</h2>
    <p>Generated Vue component</p>
  </div>
</template>

<script setup>
import {{ ref, reactive }} from 'vue'

// Props
{chr(10).join([f"const {prop} = defineProps(['{prop}'])" for prop in spec.props.keys()]) if spec.props else "// No props defined"}

// Reactive data
{chr(10).join([f"const {state} = ref({default})" for state, default in spec.state.items()]) if spec.state else "// No reactive state"}

// Component logic here
</script>

<style scoped>
.{spec.name.lower()} {{
  /* Component styles */
  padding: 1rem;
  border: 1px solid #ccc;
  border-radius: 4px;
}}
</style>
'''

        return component_code.strip()

    async def _generate_component_styles(self, spec: ComponentSpec) -> str:
        """Generate component CSS styles."""
        return f'''.{spec.name.lower()} {{
  /* {spec.name} component styles */
  display: block;
  padding: 1rem;
  margin: 0.5rem 0;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #ffffff;
}}

.{spec.name.lower()}:hover {{
  border-color: #007bff;
  box-shadow: 0 2px 4px rgba(0, 123, 255, 0.1);
}}
'''

    # Additional template methods would be implemented here...
    async def _react_class_template(self, spec: ComponentSpec) -> str:
        """Generate React class component template."""
        return "// React class component template"

    async def _vue_options_template(self, spec: ComponentSpec) -> str:
        """Generate Vue options API component template."""
        return "// Vue options API component template"

    async def _generate_component_test(self, component_dir: Path, spec: ComponentSpec, framework: str) -> Optional[str]:
        """Generate component test file."""
        return None  # Implementation placeholder

    async def _generate_component_story(self, component_dir: Path, spec: ComponentSpec, framework: str) -> Optional[str]:
        """Generate Storybook story file."""
        return None  # Implementation placeholder

    async def _generate_express_route(self, endpoint_name: str, method: str, database_table: Optional[str], auth_required: bool) -> str:
        """Generate Express.js route file."""
        return f'''const express = require('express');
const router = express.Router();
const {endpoint_name}Controller = require('../controllers/{endpoint_name}Controller');

// {method} /{endpoint_name}
router.{method.lower()}('/', {endpoint_name}Controller.{method.lower()}{endpoint_name.capitalize()});

module.exports = router;
'''

    async def _generate_express_controller(self, endpoint_name: str, database_table: Optional[str]) -> str:
        """Generate Express.js controller file."""
        return f'''const {endpoint_name}Controller = {{
  // GET {endpoint_name}
  get{endpoint_name.capitalize()}: async (req, res) => {{
    try {{
      // Implementation here
      res.json({{ message: 'Get {endpoint_name} endpoint' }});
    }} catch (error) {{
      res.status(500).json({{ error: error.message }});
    }}
  }},

  // POST {endpoint_name}
  post{endpoint_name.capitalize()}: async (req, res) => {{
    try {{
      // Implementation here
      res.json({{ message: 'Create {endpoint_name} endpoint' }});
    }} catch (error) {{
      res.status(500).json({{ error: error.message }});
    }}
  }}
}};

module.exports = {endpoint_name}Controller;
'''

    async def _generate_database_model(self, endpoint_name: str, database_table: str) -> str:
        """Generate database model file."""
        return f'''const {{ DataTypes }} = require('sequelize');
const sequelize = require('../database/config');

const {endpoint_name.capitalize()} = sequelize.define('{endpoint_name}', {{
  id: {{
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  }},
  // Add more fields here
  createdAt: {{
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW
  }},
  updatedAt: {{
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW
  }}
}}, {{
  tableName: '{database_table}',
  timestamps: true
}});

module.exports = {endpoint_name.capitalize()};
'''

    async def _generate_api_tests(self, endpoint_name: str, method: str, auth_required: bool) -> str:
        """Generate API test file."""
        return f'''const request = require('supertest');
const app = require('../../src/app');

describe('{endpoint_name.capitalize()} API', () => {{
  test('{method} /{endpoint_name} should return 200', async () => {{
    const response = await request(app)
      .{method.lower()}('/api/{endpoint_name}');

    expect(response.status).toBe(200);
  }});
}});
'''

    # Database-related methods
    async def _generate_database_config(self, database_type: DatabaseType, schema_name: str) -> str:
        """Generate database configuration."""
        if database_type == DatabaseType.POSTGRESQL:
            return f'''const {{ Sequelize }} = require('sequelize');

const sequelize = new Sequelize(
  process.env.DB_NAME || '{schema_name}',
  process.env.DB_USER || 'postgres',
  process.env.DB_PASS || 'password',
  {{
    host: process.env.DB_HOST || 'localhost',
    port: process.env.DB_PORT || 5432,
    dialect: 'postgres',
    logging: false
  }}
);

module.exports = sequelize;
'''
        else:
            return "// Database configuration placeholder"

    async def _generate_migration_sql(self, table: Dict[str, Any], database_type: DatabaseType) -> str:
        """Generate SQL migration."""
        return f'''-- Migration for {table['name']} table
CREATE TABLE IF NOT EXISTS {table['name']} (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

    async def _generate_orm_model(self, table: Dict[str, Any], database_type: DatabaseType) -> str:
        """Generate ORM model."""
        return f'''// ORM model for {table['name']}
module.exports = {table['name']};
'''

    async def _generate_database_init(self, database_type: DatabaseType, tables: List[Dict[str, Any]]) -> str:
        """Generate database initialization script."""
        return '''// Database initialization script
const sequelize = require('./config');

async function initDatabase() {
  try {
    await sequelize.authenticate();
    console.log('Database connection established');

    await sequelize.sync();
    console.log('Database synchronized');
  } catch (error) {
    console.error('Database initialization failed:', error);
  }
}

initDatabase();
'''

    # Docker-related methods
    async def _generate_dockerfile(self, project_root: Path, production_ready: bool) -> str:
        """Generate Dockerfile."""
        return '''FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
'''

    async def _generate_docker_compose(self, project_root: Path, include_database: bool) -> str:
        """Generate docker-compose.yml."""
        compose_content = '''version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    volumes:
      - .:/app
      - /app/node_modules
'''

        if include_database:
            compose_content += '''
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
'''

        return compose_content

    async def _generate_dockerignore(self) -> str:
        """Generate .dockerignore file."""
        return '''node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.nyc_output
coverage
.DS_Store
'''

    async def _generate_env_template(self, include_database: bool) -> str:
        """Generate environment variables template."""
        env_content = '''# Application
NODE_ENV=development
PORT=3000

# Security
JWT_SECRET=your-jwt-secret-here
'''

        if include_database:
            env_content += '''
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=postgres
DB_PASS=password
'''

        return env_content


# Export app builder toolkit
app_builder = AppBuilderToolkit()

async def create_app_project(
    name: str,
    project_type: str,
    path: str = ".",
    **kwargs
) -> Dict[str, Any]:
    """
    Claude Code compatible app project creation function.

    Args:
        name: Project name
        project_type: Type of project (react, vue, node-api, etc.)
        path: Directory path for the project
        **kwargs: Additional configuration options

    Returns:
        Project creation result
    """
    config = ProjectConfig(
        name=name,
        type=ProjectType(project_type),
        path=path,
        description=kwargs.get('description', ''),
        author=kwargs.get('author', ''),
        database=DatabaseType(kwargs.get('database')) if kwargs.get('database') else None,
        features=kwargs.get('features', []),
        dependencies=kwargs.get('dependencies', []),
        dev_dependencies=kwargs.get('dev_dependencies', [])
    )

    return await app_builder.create_project(config)

async def generate_app_component(
    project_path: str,
    component_name: str,
    component_type: str = "functional",
    framework: str = "react",
    **kwargs
) -> Dict[str, Any]:
    """
    Claude Code compatible component generation function.

    Args:
        project_path: Path to the project
        component_name: Name of the component
        component_type: Type of component
        framework: Target framework
        **kwargs: Additional component options

    Returns:
        Component generation result
    """
    component_spec = ComponentSpec(
        name=component_name,
        type=component_type,
        props=kwargs.get('props', {}),
        state=kwargs.get('state', {}),
        hooks=kwargs.get('hooks', []),
        styling=kwargs.get('styling', 'css'),
        tests=kwargs.get('tests', True)
    )

    return await app_builder.generate_component(project_path, component_spec, framework)

async def generate_app_api(
    project_path: str,
    endpoint_name: str,
    method: str = "GET",
    **kwargs
) -> Dict[str, Any]:
    """
    Claude Code compatible API generation function.

    Args:
        project_path: Path to the project
        endpoint_name: Name of the API endpoint
        method: HTTP method
        **kwargs: Additional API options

    Returns:
        API generation result
    """
    return await app_builder.generate_api_endpoint(
        project_path,
        endpoint_name,
        method,
        kwargs.get('database_table'),
        kwargs.get('auth_required', False)
    )