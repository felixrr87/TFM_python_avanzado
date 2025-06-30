# ⚽ SPORTALYZE - Plataforma Avanzada de Análisis de Fútbol


**Sportalyze** es una herramienta integral de análisis deportivo especializada en fútbol, diseñada para ayudar a **entrenadores**, **scouts**, **analistas** y **clubes** a tomar decisiones basadas en datos. Combina **datos en tiempo real vía API**, **scraping avanzado de estadísticas históricas**, **modelos de Machine Learning para scouting de talento**, y una interfaz profesional con capacidad de **generar reportes en PDF listos para presentar**.

Desarrollado con un enfoque profesional, es ideal tanto para **trabajo académico** como para **uso comercial** en entornos deportivos reales.

---

## 🧠 Características Clave

- 📊 **Dashboard Interactivo**: Visualiza estadísticas clave de equipos y jugadores.
- 🤖 **Scouting con Machine Learning**: Descubre jóvenes talentos (16-22 años) mediante modelos ML personalizados.
- 🌐 **Datos Multifuente**:
  - API Football Data: Resultados, clasificaciones y datos en vivo (Premier League).
  - Scraping de FBref: Métricas avanzadas de las 5 grandes ligas europeas.
- 📄 **Generación de Reportes PDF**: Exportación profesional para compartir análisis con cuerpo técnico o directivos.
- 🔐 **Sistema de Login**: Acceso seguro mediante credenciales.

---

## 🗂️ Estructura del Proyecto

sportalyze/
├── app.py # Punto de entrada de la app (Streamlit)
├── requirements.txt # Lista de dependencias
├── .env # API Keys y configuración oculta
├── assets/ # Imágenes y elementos visuales
│ ├── sportalyze.png # Logo
│ └── background.jpg # Imagen de fondo
├── frontend/ # Interfaz de usuario
│ ├── login.py
│ ├── home.py
│ ├── loading.py
│ ├── api_data.py
│ ├── scraping_data.py
│ ├── ml_scouting.py
│ └── pdf_reports.py
└── backend/ # Lógica de negocio
├── api_handler.py
├── fbref_scraper.py
├── ml_model.py
└── pdf_generator.py


---

## 🛠️ Instalación Paso a Paso

> 💡 Requisitos: Python 3.9+ y Git instalado en tu máquina.

1. **Clona el repositorio**:
```bash
git clone https://github.com/tu_usuario/sportalyze.git
cd sportalyze
Crea un entorno virtual (opcional pero recomendado):
# En Windows
python -m venv venv
venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
Instala las dependencias:
pip install -r requirements.txt

Ejecuta la aplicación:
streamlit run app.py

🚀 Cómo Usar Sportalyze

🔐 Login
Usuario por defecto: admin
Contraseña por defecto: admin

📊 Sección de Estadísticas (Stats)
Visualiza:
Clasificación de la Premier League
Resultados recientes
Estadísticas detalladas por equipo
Datos obtenidos vía API Football Data y scraping de FBref

🤖 Sección de Scouting (Machine Learning)
Modelos de ML entrenados para:
Detectar talento joven (16-22 años)
Filtrar por posición, minutos jugados, edad, etc.
Comparar métricas clave de rendimiento
Implementado con Scikit-learn, Pandas y lógica personalizada

📄 Sección de Reportes (PDF Export)
Exporta tu análisis actual como un PDF profesional
Incluye:
Gráficos
Tablas estadísticas
Comparativas personalizadas
El archivo generado se guarda en la sesión del usuario

🧪 Tecnologías Usadas

Frontend:
Streamlit: Interfaz web moderna
Plotly, Matplotlib: Visualizaciones interactivas y gráficas estáticas
Backend:
Python 3.9+
Pandas, Requests, BeautifulSoup: Procesamiento y scraping
Scikit-learn: Modelos de Machine Learning
ReportLab / FPDF: Generación de PDFs

📌 Notas Técnicas

Se respeta el "robots.txt" de FBref con delays aleatorios para evitar bloqueos al hacer scraping.

Los modelos de Machine Learning están optimizados para scouting joven. 

📈 Roadmap Futuro

 Integración con más ligas y competiciones
 Dashboard táctico en tiempo real
 Modelos predictivos de rendimiento por posición
 Integración con GPS y datos físicos
 Sistema de recomendaciones automáticas por IA


🤝 Colaboraciones

¿Te interesa colaborar, aportar datos o mejorar los modelos?
Abre un pull request o contáctame directamente.
Este proyecto está pensado para evolucionar y profesionalizar el análisis deportivo.

