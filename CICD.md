# CI/CD — Backend (Mi Punto API)

Pipeline de integración y despliegue continuo con **GitHub Actions**.
Despliegue en **Render**.

## Workflows

| Archivo | Cuándo se ejecuta | Qué hace |
|---|---|---|
| `.github/workflows/ci.yml` | En cada **Pull Request** hacia `main` y en cada **push** a `main` | **Lint** (`ruff check`), **Pruebas** (`pytest`) y **Build** (`compileall` + smoke import) |
| `.github/workflows/deploy.yml` | Solo al hacer **merge / push a `main`** | Dispara el despliegue a producción en Render vía *Deploy Hook* |

El job de `build` depende de que `lint` y `test` pasen (`needs: [lint, test]`).

## Ejecutar localmente

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt

ruff check .        # lint
python -m pytest    # pruebas
python -m compileall app   # build
```

## Despliegue en Render

1. En [render.com](https://render.com) → **New** → **Blueprint** y conecta el repo
   `NataBravo/mi-punto-backend`. Render leerá `render.yaml` y creará el servicio
   web + la base de datos PostgreSQL automáticamente.
2. El servicio queda con `autoDeploy: false`: **no** despliega solo. El pipeline
   (`deploy.yml`) lo dispara al hacer merge a `main`.
3. Copia el **Deploy Hook** del servicio:
   *Render → servicio → Settings → Deploy Hook* (una URL del tipo
   `https://api.render.com/deploy/srv-XXXX?key=YYYY`).

### Secret requerido en GitHub

*GitHub → repo → Settings → Secrets and variables → Actions → New repository secret:*

| Secret | Valor |
|---|---|
| `RENDER_DEPLOY_HOOK_URL` | La URL del Deploy Hook de Render |

### Variables de entorno (Render)

`render.yaml` ya define `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `UPLOAD_DIR` y `PUBLIC_BASE_URL`.
Configura manualmente en el dashboard de Render:

- `CORS_ORIGINS` → la URL pública del frontend en Vercel
  (ej. `https://mi-punto-frontend.vercel.app`).

> Nota: la app normaliza la `DATABASE_URL` de Render (`postgresql://`) al driver
> `postgresql+psycopg://` automáticamente (ver `app/core/config.py`).

## Evidencia de ejecuciones

Las ejecuciones quedan registradas en la pestaña **Actions** del repositorio.
Para tres ejecuciones exitosas: abrir 2–3 Pull Requests (o pushes a `main`) y
capturar los runs en verde de los workflows **CI** y **Deploy**.
