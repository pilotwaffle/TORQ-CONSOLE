# How to Build Apps in TORQ Console

## 🚀 Complete Guide to Building Apps with TORQ Console

TORQ Console has a powerful **App Builder Toolkit** that helps you scaffold full-stack applications with React, Vue, Next.js, Express APIs, databases, and Docker containerization.

---

## 📋 Quick Start

### Method 1: Via TORQ Console Web Interface (Recommended)

1. **Open TORQ Console** - Already running at http://127.0.0.1:8899
2. **Use Prince Flowers Enhanced Agent** - Ask natural language questions:

```
"Create a React app called my-portfolio with PostgreSQL database"

"Build a Next.js e-commerce site with authentication and MongoDB"

"Generate a Vue 3 app with Tailwind CSS and Vite"
```

Prince Flowers will use the app builder automatically and guide you through the process!

---

### Method 2: Via Python API (Direct)

For programmatic access, use the app builder directly:

```python
import sys
sys.path.insert(0, 'E:/TORQ-CONSOLE')

from torq_console.utils.app_builder import (
    create_app_project,
    generate_app_component,
    generate_app_api,
    ProjectType,
    DatabaseType
)

# Example: Create a React app with PostgreSQL
result = await create_app_project(
    name="my-awesome-app",
    project_type="react",
    path="E:/my-projects",
    description="My awesome React application",
    author="King Flowers",
    database="postgresql",
    features=["authentication", "api"],
    dependencies=["axios", "react-router-dom"],
    dev_dependencies=["eslint", "prettier"]
)

print(result)
```

---

## 🎯 Supported Project Types

| Type | Description | Command |
|------|-------------|---------|
| **react** | React 18 with Create React App | `project_type="react"` |
| **vue** | Vue 3 with Vue CLI | `project_type="vue"` |
| **nextjs** | Next.js 14 (SSR/SSG) | `project_type="nextjs"` |
| **vite** | Vite + React/Vue (fast dev) | `project_type="vite"` |
| **node-api** | Node.js REST API | `project_type="node-api"` |
| **express-api** | Express.js API server | `project_type="express-api"` |
| **static** | Static HTML/CSS/JS site | `project_type="static"` |
| **fullstack** | Full-stack (Frontend + Backend) | `project_type="fullstack"` |

---

## 💾 Database Support

Supported databases:
- **PostgreSQL** - `database="postgresql"`
- **MySQL** - `database="mysql"`
- **MongoDB** - `database="mongodb"`
- **SQLite** - `database="sqlite"`
- **Redis** - `database="redis"` (caching layer)

The app builder automatically:
✅ Adds database dependencies to package.json
✅ Generates ORM models (Sequelize/Mongoose)
✅ Creates database configuration files
✅ Sets up migrations

---

## 🛠️ App Builder Features

### 1. **Full Project Scaffolding**

```python
from torq_console.utils.app_builder import create_app_project

result = await create_app_project(
    name="blog-platform",
    project_type="nextjs",
    path="E:/projects",
    database="postgresql",
    features=[
        "authentication",  # JWT/OAuth setup
        "api",            # REST API routes
        "testing",        # Jest + Testing Library
        "docker"          # Docker + docker-compose
    ]
)
```

**What you get:**
```
blog-platform/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components/routes
│   ├── api/            # API routes
│   │   ├── routes/     # Express routes
│   │   └── controllers/ # Request handlers
│   ├── models/         # Database models
│   └── utils/          # Helper functions
├── tests/              # Test files
├── database/
│   ├── migrations/     # Database migrations
│   ├── schemas/        # DB schema definitions
│   ├── config.js       # DB configuration
│   └── init.js         # DB initialization
├── docs/
│   ├── API.md          # API documentation
│   └── README.md       # Project docs
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Multi-container setup
├── package.json        # Dependencies
├── .gitignore          # Git ignore rules
├── .env.example        # Environment template
└── README.md           # Getting started guide
```

---

### 2. **Generate Components**

```python
from torq_console.utils.app_builder import generate_app_component, ComponentSpec

# React functional component
result = await generate_app_component(
    project_path="E:/projects/blog-platform",
    component_name="BlogPost",
    component_type="functional",  # or "class"
    framework="react",
    props={"title": "string", "content": "string", "author": "string"},
    state={"likes": "0", "isLiked": "false"},
    hooks=["state", "effect"],
    styling="css",  # or "scss", "styled-components", "tailwind"
    tests=True      # Generates test file
)
```

**Generated files:**
```
src/components/BlogPost/
├── BlogPost.jsx        # Component code
├── BlogPost.css        # Styles
├── BlogPost.test.js    # Unit tests
└── BlogPost.stories.js # Storybook stories
```

---

### 3. **Generate API Endpoints**

```python
from torq_console.utils.app_builder import generate_app_api

# Create a complete API endpoint with CRUD
result = await generate_app_api(
    project_path="E:/projects/blog-platform",
    endpoint_name="posts",
    method="ALL",  # Creates GET, POST, PUT, DELETE
    database_table="blog_posts",
    auth_required=True
)
```

**Generated files:**
```
src/api/
├── routes/
│   └── posts.js              # Express routes
├── controllers/
│   └── postsController.js    # Business logic
src/models/
    └── postsModel.js         # ORM model
tests/api/
    └── posts.test.js         # API tests
```

**Endpoint example:**
```javascript
// Auto-generated controller with CRUD
const postsController = {
  // GET /api/posts
  getPosts: async (req, res) => { /* ... */ },

  // POST /api/posts
  createPost: async (req, res) => { /* ... */ },

  // PUT /api/posts/:id
  updatePost: async (req, res) => { /* ... */ },

  // DELETE /api/posts/:id
  deletePost: async (req, res) => { /* ... */ }
};
```

---

### 4. **Database Schema Management**

```python
from torq_console.utils.app_builder import setup_database_schema, DatabaseType

result = await app_builder.setup_database_schema(
    project_path="E:/projects/blog-platform",
    schema_name="blog_db",
    database_type=DatabaseType.POSTGRESQL,
    tables=[
        {
            "name": "users",
            "columns": {
                "id": {"type": "INTEGER", "primaryKey": True},
                "email": {"type": "STRING", "unique": True},
                "password": {"type": "STRING"},
                "created_at": {"type": "DATE"}
            }
        },
        {
            "name": "posts",
            "columns": {
                "id": {"type": "INTEGER", "primaryKey": True},
                "title": {"type": "STRING"},
                "content": {"type": "TEXT"},
                "author_id": {"type": "INTEGER", "foreignKey": "users.id"},
                "created_at": {"type": "DATE"}
            }
        }
    ]
)
```

**What you get:**
- Migration files for each table
- Sequelize/Mongoose models
- Database initialization script
- Automatic relationships setup

---

### 5. **Docker Containerization**

```python
from torq_console.utils.app_builder import containerize_project

result = await app_builder.containerize_project(
    project_path="E:/projects/blog-platform",
    include_database=True,
    production_ready=True
)
```

**Generated files:**
```
Dockerfile              # App container
docker-compose.yml      # Multi-container orchestration
.dockerignore          # Exclude files from image
.env.example           # Environment variables template
```

**Example docker-compose.yml:**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: blog_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🎨 Example: Complete E-Commerce App

Here's a complete example building an e-commerce platform:

```python
import asyncio
import sys
sys.path.insert(0, 'E:/TORQ-CONSOLE')

from torq_console.utils.app_builder import (
    create_app_project,
    generate_app_component,
    generate_app_api,
    DatabaseType,
    app_builder
)

async def build_ecommerce_app():
    # Step 1: Create Next.js project with PostgreSQL
    print("Creating e-commerce platform...")
    project = await create_app_project(
        name="ecommerce-platform",
        project_type="nextjs",
        path="E:/projects",
        description="Modern e-commerce platform with Next.js",
        author="King Flowers",
        database="postgresql",
        features=["authentication", "api", "testing"],
        dependencies=[
            "next-auth",      # Authentication
            "stripe",         # Payments
            "swr",            # Data fetching
            "zustand"         # State management
        ]
    )

    print(f"✅ Project created: {project['project_path']}")

    # Step 2: Setup database schema
    print("\nSetting up database schema...")
    db_result = await app_builder.setup_database_schema(
        project_path=project['project_path'],
        schema_name="ecommerce_db",
        database_type=DatabaseType.POSTGRESQL,
        tables=[
            {
                "name": "products",
                "columns": {
                    "id": "INTEGER PRIMARY KEY",
                    "name": "STRING",
                    "description": "TEXT",
                    "price": "DECIMAL",
                    "stock": "INTEGER",
                    "image_url": "STRING",
                    "category": "STRING"
                }
            },
            {
                "name": "orders",
                "columns": {
                    "id": "INTEGER PRIMARY KEY",
                    "user_id": "INTEGER",
                    "total_amount": "DECIMAL",
                    "status": "STRING",
                    "created_at": "TIMESTAMP"
                }
            },
            {
                "name": "cart_items",
                "columns": {
                    "id": "INTEGER PRIMARY KEY",
                    "user_id": "INTEGER",
                    "product_id": "INTEGER",
                    "quantity": "INTEGER"
                }
            }
        ]
    )

    print(f"✅ Database schema created: {db_result['tables_count']} tables")

    # Step 3: Generate UI components
    print("\nGenerating UI components...")

    components = [
        ("ProductCard", {"name": "string", "price": "number", "image": "string"}),
        ("ShoppingCart", {"items": "array", "total": "number"}),
        ("CheckoutForm", {"onSubmit": "function"}),
        ("ProductList", {"products": "array", "loading": "boolean"})
    ]

    for comp_name, props in components:
        comp_result = await generate_app_component(
            project_path=project['project_path'],
            component_name=comp_name,
            component_type="functional",
            framework="react",
            props=props,
            hooks=["state", "effect"],
            styling="tailwind",
            tests=True
        )
        print(f"  ✅ Generated component: {comp_name}")

    # Step 4: Generate API endpoints
    print("\nGenerating API endpoints...")

    endpoints = [
        ("products", "ALL", "products"),
        ("orders", "ALL", "orders"),
        ("cart", "ALL", "cart_items"),
        ("checkout", "POST", None)
    ]

    for endpoint, method, table in endpoints:
        api_result = await generate_app_api(
            project_path=project['project_path'],
            endpoint_name=endpoint,
            method=method,
            database_table=table,
            auth_required=(endpoint != "products")
        )
        print(f"  ✅ Generated API: /api/{endpoint}")

    # Step 5: Docker containerization
    print("\nContainerizing application...")
    docker_result = await app_builder.containerize_project(
        project_path=project['project_path'],
        include_database=True,
        production_ready=True
    )

    print(f"✅ Docker configuration created")

    # Summary
    print("\n" + "="*60)
    print("🎉 E-COMMERCE PLATFORM READY!")
    print("="*60)
    print(f"\nProject location: {project['project_path']}")
    print("\nNext steps:")
    print("  1. cd", project['project_path'])
    print("  2. npm install")
    print("  3. cp .env.example .env")
    print("  4. Edit .env with your database credentials")
    print("  5. docker-compose up -d  (start database)")
    print("  6. npm run dev  (start development server)")
    print("\nAccess your app at: http://localhost:3000")
    print("\n📚 Documentation: docs/API.md")

# Run the builder
asyncio.run(build_ecommerce_app())
```

---

## 💡 Using with Prince Flowers (Natural Language)

The easiest way is to ask Prince Flowers in natural language:

**Via Web Interface (http://127.0.0.1:8899):**

```
"Build me a blog platform with Next.js and PostgreSQL.
Include user authentication, post creation/editing,
comments system, and tag management."
```

Prince Flowers will:
1. Create the Next.js project
2. Setup PostgreSQL database with appropriate tables
3. Generate all necessary components (BlogPost, CommentList, etc.)
4. Create API endpoints for posts, comments, users, tags
5. Add authentication middleware
6. Setup Docker containers
7. Generate comprehensive documentation

---

## 🔧 Advanced Configuration

### Custom Component Templates

Create custom component templates for your team:

```python
# In your project
from torq_console.utils.app_builder import app_builder

# Add custom template
app_builder.component_templates['react_hooks'] = custom_template_function
```

### Project Features

Available features you can enable:

```python
features=[
    "authentication",   # JWT/OAuth setup
    "api",             # REST API structure
    "testing",         # Jest + Testing Library
    "docker",          # Docker containerization
    "ci-cd",           # GitHub Actions/GitLab CI
    "analytics",       # Analytics integration
    "seo",             # SEO optimization
    "pwa"              # Progressive Web App
]
```

### Framework-Specific Options

**React:**
```python
dependencies=["react-router-dom", "axios", "react-query", "zustand"]
dev_dependencies=["@testing-library/react", "@testing-library/jest-dom"]
```

**Vue:**
```python
dependencies=["vue-router", "pinia", "axios"]
dev_dependencies=["@vue/test-utils", "vitest"]
```

**Next.js:**
```python
dependencies=["next-auth", "swr", "@vercel/analytics"]
```

---

## 📚 Documentation Generation

All projects include auto-generated documentation:

- **README.md** - Getting started guide
- **docs/API.md** - API endpoint documentation
- **Component docs** - Storybook stories for each component
- **Database docs** - Schema and migration documentation

---

## 🚀 Deployment

### Deploy to Production

```bash
# Build for production
cd your-project
npm run build

# Using Docker
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to Vercel/Netlify (for Next.js/React)
vercel deploy
# or
netlify deploy --prod
```

---

## 🎯 Best Practices

1. **Use TypeScript** - Add `typescript` to dev_dependencies
2. **Enable ESLint + Prettier** - Automatic code quality
3. **Write Tests** - All generated components include test files
4. **Use Environment Variables** - Never commit .env files
5. **Docker for Development** - Consistent environment across team
6. **API Documentation** - Keep docs/API.md updated

---

## 🆘 Troubleshooting

**Issue: Project creation fails**
- Check Node.js is installed: `node --version`
- Ensure npm is available: `npm --version`
- Verify path permissions

**Issue: Database connection fails**
- Check database is running: `docker-compose ps`
- Verify credentials in .env file
- Test connection: `npm run test:db`

**Issue: Component generation fails**
- Ensure project was created first
- Check src/components directory exists
- Verify framework matches project type

---

## 📞 Get Help

Ask Prince Flowers in TORQ Console:
```
"Help me build an app with [your requirements]"
"How do I add authentication to my React app?"
"Generate a REST API for my blog posts"
"Setup PostgreSQL database with user and post tables"
```

Or use the comprehensive App Builder API directly for full control!

---

**Happy Building! 🚀**

Built with TORQ Console App Builder Toolkit
