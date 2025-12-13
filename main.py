import sys
import signal
import os
import time
import subprocess
import json
import logging

logging.basicConfig(level=logging.DEBUG)
# Fuerza a Python a no usar buffer en la salida (todo sale al instante)
os.environ["PYTHONUNBUFFERED"] = "1"

# --- ⚠️ PARCHE CRÍTICO PARA WINDOWS ⚠️ ---
if sys.platform.startswith('win'):
    def _patch_signal(sig_name):
        if not hasattr(signal, sig_name):
            setattr(signal, sig_name, signal.SIGTERM if hasattr(signal, 'SIGTERM') else 1)

    unix_signals = ['SIGHUP', 'SIGQUIT', 'SIGTRAP', 'SIGIOT', 'SIGBUS', 'SIGFPE', 
                    'SIGUSR1', 'SIGSEGV', 'SIGUSR2', 'SIGPIPE', 'SIGALRM', 'SIGTERM',
                    'SIGCHLD', 'SIGCONT', 'SIGSTOP', 'SIGTSTP', 'SIGTTIN', 'SIGTTOU', 
                    'SIGURG', 'SIGXCPU', 'SIGXFSZ', 'SIGVTALRM', 'SIGPROF', 'SIGWINCH', 
                    'SIGIO', 'SIGPWR', 'SIGSYS']
    for sig in unix_signals:
        _patch_signal(sig)

# --- IMPORTACIONES ---
from github import Github
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from dotenv import load_dotenv
from crewai_tools import FileWriterTool, FileReadTool
from crewai.tools import BaseTool

load_dotenv()

# --- 🎭 PARCHE ANTI-OPENAI 🎭 ---
os.environ["OPENAI_API_KEY"] = "NA"

# --- CONFIGURACIÓN ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO_NAME") 

if not GITHUB_TOKEN or not REPO_NAME:
    print("❌ ERROR: Faltan variables en .env")
    sys.exit(1)

g = Github(GITHUB_TOKEN)

# --- CONFIGURACIÓN DE MODELOS ---
safety_settings = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}

llm_pro = ChatGoogleGenerativeAI(
    model="gemini-pro-latest",
    verbose=True,
    temperature=0.2,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    max_retries=5,
    safety_settings=safety_settings
)

llm_flash = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    verbose=True,
    temperature=0.1,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    max_retries=10,
    safety_settings=safety_settings
)

# --- CARGA DE AGENTES ---
def load_agents_config():
    try:
        with open('agents.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ ERROR: No se encuentra 'agents.json'.")
        sys.exit(1)

agents_config = load_agents_config()

# --- HERRAMIENTAS PERSONALIZADAS ---

class UTF8FileWriterTool(FileWriterTool):
    name: str = "Save File UTF-8"
    description: str = "Saves content to a file. You can specify the directory separately. Input: filename, content, directory (optional)."
    
    # 👇 CAMBIO CRÍTICO: 'directory' ahora es un argumento explícito con valor por defecto None
    def _run(self, filename: str, content: str, directory: str = None, **kwargs) -> str:
        forbidden_files = ['main.py', '.env', 'agents.json', 'Procfile', 'Dockerfile']
        
        # 1. Construcción de la ruta
        if directory:
            # Si el agente envía "app" y "routes.py", creamos "app/routes.py"
            file_path = os.path.join(directory, filename)
        else:
            file_path = filename

        clean_name = os.path.basename(file_path)

        # 2. Seguridad
        if clean_name in forbidden_files:
            return f"❌ SECURITY ERROR: Modification of '{clean_name}' is forbidden."

        try:
            # 3. Creación de carpetas (Auto-Healing)
            target_folder = os.path.dirname(file_path)
            if target_folder and not os.path.exists(target_folder):
                try:
                    os.makedirs(target_folder)
                    print(f"📁 Carpeta creada automáticamente: {target_folder}")
                except OSError as e:
                    return f"Error creating directory {target_folder}: {e}"
            
            # 4. Escritura
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File {file_path} saved successfully."
            
        except Exception as e:
            return f"Error saving: {e}"

class FileDeleteTool(BaseTool):
    name: str = "Delete File"
    # 👇 CAMBIO CLAVE: Le decimos explícitamente que acepta múltiples archivos
    description: str = "PERMANENTLY deletes one or multiple files. Input: 'file1.py' or 'file1.py, file2.py, file3.py'."
    
    def _run(self, file_path: str) -> str:
        forbidden_files = ['main.py', '.env', 'agents.json', '.git', 'requirements.txt']
        
        # 1. Separamos por comas si vienen varios archivos
        files_to_delete = [f.strip() for f in file_path.split(',')]
        results = []

        for current_file in files_to_delete:
            clean_name = os.path.basename(current_file)
            
            # Bloqueo de seguridad
            if clean_name in forbidden_files or '.git' in current_file:
                results.append(f"❌ SECURITY ERROR: Deletion of '{clean_name}' is strictly forbidden.")
                continue
            
            if not os.path.exists(current_file):
                results.append(f"⚠️ File {current_file} does not exist.")
                continue
                
            try:
                os.remove(current_file)
                results.append(f"🗑️ File {current_file} DELETED.")
            except Exception as e:
                results.append(f"❌ Error deleting {current_file}: {e}")

        return "\n".join(results)

class SmartFileLister(FileReadTool):
    name: str = "List Project Files"
    description: str = "Lists relevant files. IMPORTANT: Provide dummy argument file_path='.'."

    def _run(self, file_path: str = '.', **kwargs) -> str:
        ignored_folders = {'.git', 'venv', 'env', '__pycache__', '.idea', '.vscode', 'git'}
        hidden_files = {'main.py', '.env', 'agents.json'}

        files = []
        try:
            for item in os.listdir('.'):
                if (item not in ignored_folders) and (item not in hidden_files) and (not item.startswith('.')):
                    files.append(item)
            
            if not files:
                return "Directory is empty (New Project)."
            return "\n".join(files)
        except Exception as e:
            return f"Error listing files: {str(e)}"

# Instancias
file_writer = UTF8FileWriterTool()
file_reader = FileReadTool()
file_deleter = FileDeleteTool()
smart_directory_reader = SmartFileLister()

# --- FUNCIONES AUXILIARES ---

def get_ai_tasks():
    try:
        repo = g.get_repo(REPO_NAME)
        issues = repo.get_issues(state='open', labels=['ai-agent'])
        return issues
    except Exception as e:
        print(f"⚠️ Error leyendo issues: {e}")
        return []

def create_pull_request(issue_number, issue_title):
    print(f"🚀 Creando Pull Request para Issue #{issue_number}...")
    try:
        current_dir = os.getcwd()
        safe_title = "".join([c if c.isalnum() else "-" for c in issue_title]).lower()[:30]
        branch_name = f"feature/issue-{issue_number}-{safe_title}"
        
        subprocess.run(f"git checkout -b {branch_name}", shell=True, cwd=current_dir)
        subprocess.run("git add .", shell=True, cwd=current_dir)
        subprocess.run(f'git commit -m "AI Fix: {issue_title}"', shell=True, cwd=current_dir)
        subprocess.run(f"git push origin {branch_name}", shell=True, cwd=current_dir)
        
        repo = g.get_repo(REPO_NAME)
        body = f"Resolves #{issue_number}\n\nGenerated by Autonomous AI Agent 🤖"
        pr = repo.create_pull(title=f"AI Implementation: {issue_title}", body=body, head=branch_name, base="main")
        
        print(f"✅ PR Creada: {pr.html_url}")
        subprocess.run("git checkout main", shell=True, cwd=current_dir)
        return True
    except Exception as e:
        print(f"❌ Error creando PR: {e}")
        subprocess.run("git checkout main", shell=True) 
        return False

def run_docker_tests():
    print("🧪 Ejecutando Tests en Docker...")
    
    # Añadimos PYTHONPATH=. para que los tests encuentren la carpeta 'app'
    docker_command = (
        'if [ -f requirements.txt ]; then pip install -r requirements.txt; fi && '
        'export PYTHONPATH=$PYTHONPATH:. && '
        'python -m unittest discover -s tests -p "test_*.py"'
    )

    cmd = f'docker run --rm -v "{os.getcwd()}":/app -w /app python:3.10-slim bash -c "{docker_command}"'
    
    # ⚠️ CAMBIO IMPORTANTE: Eliminamos text=True para manejar bytes manualmente
    result = subprocess.run(cmd, shell=True, capture_output=True)
    
    # Decodificamos con seguridad (ignorando errores de caracteres raros)
    stdout = result.stdout.decode('utf-8', errors='replace')
    stderr = result.stderr.decode('utf-8', errors='replace')
    
    full_output = stdout + "\n" + stderr

    if result.returncode == 0:
        return True, stderr # A veces unittest escribe en stderr aunque pase
    else:
        return False, full_output

# --- LÓGICA DE RESOLUCIÓN ---

def solve_issue_with_retries(issue):
    MAX_RETRIES = 3
    attempt = 0
    
    # 1. Definición de Agentes (Igual que antes)
    arch_conf = agents_config['architect']
    manager_conf = agents_config['manager']
    dev_conf = agents_config['developer']
    qa_conf = agents_config['qa']

    # 1. Definición de Agentes con LIMITES INDIVIDUALES
    
    # --- EQUIPO PRO (Lentos y Pensadores) ---
    # Gemini Pro suele tener límites estrictos (ej: 2-60 RPM según tu plan)
    architect = Agent(
        role=arch_conf['role'], goal=arch_conf['goal'], backstory=arch_conf['backstory'],
        llm=llm_pro, 
        verbose=True, 
        allow_delegation=False, 
        tools=[smart_directory_reader, file_reader],
        max_rpm=5  # 🐢 Límite estricto para que no explote la API del Pro
    )

    manager = Agent(
        role=manager_conf['role'], goal=manager_conf['goal'], backstory=manager_conf['backstory'],
        llm=llm_pro, 
        verbose=True, 
        allow_delegation=False,
        tools=[smart_directory_reader, file_reader],
        max_rpm=5  # 🐢 Límite estricto
    )
    
    # --- EQUIPO FLASH (Rápidos y Ejecutores) ---
    # Gemini Flash aguanta mucho más castigo (ej: 15-60+ RPM)
    dev = Agent(
        role=dev_conf['role'], goal=dev_conf['goal'], backstory=dev_conf['backstory'],
        llm=llm_flash, 
        verbose=True, 
        allow_delegation=False,
        tools=[file_reader, file_writer, file_deleter],
        max_rpm=30 # 🐇 Velocidad alta para picar código y borrar archivos
    )
    
    qa = Agent(
        role=qa_conf['role'], goal=qa_conf['goal'], backstory=qa_conf['backstory'],
        llm=llm_flash, 
        verbose=True, 
        allow_delegation=False,
        tools=[file_writer],
        max_rpm=30 # 🐇 Velocidad alta
    )

    print("🤖 Iniciando el Consejo de Arquitectura...")

    # TAREA 1: Arquitectura
    task_arch = Task(
        description=f"""
        CONTEXT: "{issue.title}: {issue.body}".
        1. LIST files.
        2. DESIGN target structure using the CURRENT ROOT directory (do not create a parent folder like 'my_project/').
           - Use 'app/' for code.
           - Use 'tests/' for tests.
        3. DEFINE obsolete files.
        """,
        agent=architect,
        expected_output="Architecture Design."
    )

    # TAREA 2: Planificación
    task_plan = Task(
        description="""
        Based on the Architect's design:
        1. Create a step-by-step Technical Plan.
        2. EXPLICITLY list the files that the Developer MUST DELETE.
        3. EXPLICITLY list the files that the Developer MUST CREATE.
        """,
        agent=manager,
        expected_output="Actionable Plan with DELETE/CREATE instructions."
    )

    # TAREA 3: Ejecución
    task_code = Task(
        description="""
        Execute the Plan.
        1. DELETE obsolete files using the 'Delete File' tool first.
        2. CREATE/UPDATE the new code files.
        3. UPDATE 'requirements.txt' if the Stack requires new libraries.
        """,
        agent=dev,
        expected_output="Clean codebase with new features."
    )

    # TAREA 4: Testing
    task_test = Task(
        description="Create tests for the new stack. Ensure they pass in a CI environment.",
        agent=qa,
        expected_output="Tests saved."
    )

    # Ejecución de la Fase 1
    crew = Crew(
        agents=[architect, manager, dev, qa], 
        tasks=[task_arch, task_plan, task_code, task_test], 
        verbose=True, 
        process=Process.sequential, 
        memory=False
    )
    
    crew.kickoff()

    # 👇 CAPTURA DE CONTEXTO (LA MAGIA) ✨
    # Guardamos lo que pensaron los "jefes" para usarlo si algo falla
    original_design = task_arch.output
    original_plan = task_plan.output

    # BUCLE DE AUTO-CORRECCIÓN (Solo Dev)
    while attempt < MAX_RETRIES:
        print(f"\n🔄 Validación {attempt + 1}/{MAX_RETRIES}...")
        tests_passed, error_log = run_docker_tests()
        
        if tests_passed:
            print("✅ Tests pasados.")
            return True, None
        else:
            print(f"❌ Fallo en Tests. Reparando...")
            attempt += 1
            if attempt < MAX_RETRIES:
                
                # 👇 INYECCIÓN DE CONTEXTO EN LA TAREA DE REPARACIÓN
                # El Dev recibe el error Y el plan original para no perder el norte
                fix_task = Task(
                    description=f"""
                    CRITICAL: Tests FAILED.
                    
                    ERROR LOG:
                    {error_log}
                    
                    CONTEXT (ORIGINAL PLAN):
                    The Architect and Manager originally requested this structure. DO NOT DEVIATE from the design unless necessary to fix the bug:
                    ---
                    {original_plan}
                    ---
                    
                    INSTRUCTIONS:
                    1. Analyze the error.
                    2. Fix the code or the tests to comply with the Original Plan.
                    3. Update requirements.txt if it's a 'ModuleNotFoundError'.
                    """,
                    agent=dev,
                    expected_output="Fixed files."
                )
                
                # Solo despertamos al Developer (Flash) para ahorrar costes
                fix_crew = Crew(
                    agents=[dev], 
                    tasks=[fix_task], 
                    verbose=True,
                    memory=False
                )
                fix_crew.kickoff()
            
    return False, error_log

# --- BUCLE PRINCIPAL ---

if __name__ == "__main__":
    print("==========================================")
    print(f"👀 VIGILANTE ACTIVO EN: {REPO_NAME}")
    print("  - Roles: Architect + Manager (Pro) / Dev + QA (Flash)")
    print("  - NO DELEGATION / NO MEMORY / NO INTERNAL MANAGER")
    print("==========================================")

    while True:
        try:
            issues = get_ai_tasks()
            
            if issues.totalCount > 0:
                for issue in issues:
                    print(f"\n🔔 TAREA DETECTADA: {issue.title} (#{issue.number})")
                    
                    success, final_error = solve_issue_with_retries(issue)
                    
                    if success:
                        if create_pull_request(issue.number, issue.title):
                            issue.create_comment("✅ Tarea completada.")
                            issue.remove_from_labels("ai-agent")
                    else:
                        print("💀 Se acabaron los intentos.")
                        issue.create_comment(f"❌ Error:\n```\n{final_error}\n```")
                        issue.remove_from_labels("ai-agent")
                        issue.add_to_labels("help-wanted")

                    print("💤 Descansando...")
                    time.sleep(10)
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(30)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error General: {e}")
            time.sleep(30)