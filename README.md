# Mi Punto – Backend

## 📌 Descripción del proyecto

Mi Punto es una plataforma orientada a la gestión y visualización de negocios locales.
Este repositorio contiene el backend del sistema, encargado de la lógica de negocio, gestión de datos, autenticación y exposición de servicios mediante una API REST.

---

## 🚀 Tecnologías utilizadas

* **FastAPI** → Framework para la construcción de APIs
* **Pydantic** → Validación de datos y definición de DTOs
* **SQLAlchemy** → ORM para modelado de base de datos
* **Uvicorn** → Servidor ASGI para ejecución del backend

---

## 🧠 Arquitectura

El proyecto implementa una **arquitectura monolítica modular**, lo que significa que todo el sistema se encuentra en un solo repositorio, pero organizado en módulos independientes.

Se aplica el enfoque de **Screaming Architecture**, donde la estructura del proyecto refleja directamente las funcionalidades del negocio.

### 📦 Módulos principales

* **auth** → Autenticación y gestión de usuarios
* **business** → Gestión de negocios
* **reviews** → Gestión de reseñas

Cada módulo contiene:

* `router.py` → Definición de endpoints (API)
* `service.py` → Lógica de negocio
* `models.py` → Modelos de base de datos (SQLAlchemy)
* `schemas.py` → DTOs (Pydantic)

---

## 📁 Estructura del proyecto

```
app/
│
├── modules/
│   ├── auth/
│   ├── business/
│   └── reviews/
│
├── core/
│   ├── config.py
│   └── database.py
│
└── main.py
```

---

## 🗄️ Base de datos

El proyecto utiliza **SQLAlchemy** como ORM para la gestión de la base de datos.
Actualmente se configura con SQLite para desarrollo, pero puede escalarse fácilmente a PostgreSQL.

---

## 🔄 Flujo de funcionamiento

1. El cliente (frontend) realiza una petición HTTP
2. El router recibe la solicitud
3. El servicio procesa la lógica de negocio
4. Se interactúa con la base de datos mediante modelos (SQLAlchemy)
5. Se devuelve una respuesta validada con Pydantic

---

## ⚙️ Instalación y ejecución

### 1. Clonar el repositorio

```
git clone <URL_DEL_REPOSITORIO>
cd mi-punto-backend
```

---

### 2. Crear entorno virtual

```
python -m venv venv
```

---

### 3. Activar entorno virtual

**Windows (PowerShell):**

```
.\venv\Scripts\Activate.ps1
```

**Linux / Mac:**

```
source venv/bin/activate
```

---

### 4. Instalar dependencias

```
pip install -r requirements.txt
```

---

### 5. Ejecutar servidor

```
uvicorn app.main:app --reload
```

---

## 🌐 Endpoints de prueba

* **Inicio:** http://127.0.0.1:8000
* **Documentación Swagger:** http://127.0.0.1:8000/docs

---

## 🧪 Estado del proyecto

En desarrollo bajo metodología ágil (Scrum), organizado por sprints y gestionado mediante herramientas como Jira.

---

## 👥 Equipo de desarrollo

* Natalia Andrea Bravo Castro
* Juan Camilo Campo Tangarife

---

## 📄 Notas adicionales

* El backend expone una API REST que será consumida por el frontend del proyecto.
* La arquitectura modular facilita la escalabilidad y el mantenimiento del sistema.
* Se recomienda seguir la estructura definida para mantener consistencia en el desarrollo.

---

## 📞 Contact o
Para cualquier consulta o colaboración, no dudes en contactarnos a través de:
* **Email:**
    * Juan Camilo: Juanccampo95@gmail.com  