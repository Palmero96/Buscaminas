import os
import sys
import signal
import subprocess # <--- Necesario para ejecutar Docker desde Python

# --- PARCHE PARA WINDOWS ---
if sys.platform.startswith('win'):
    unix_signals = ['SIGHUP', 'SIGQUIT', 'SIGTRAP', 'SIGIOT', 'SIGBUS', 'SIGFPE', 
                    'SIGUSR1', 'SIGSEGV', 'SIGUSR2', 'SIGPIPE', 'SIGALRM', 'SIGTERM',
                    'SIGCHLD', 'SIGCONT', 'SIGSTOP', 'SIGTSTP', 'SIGTTIN', 'SIGTTOU', 
                    'SIGURG', 'SIGXCPU', 'SIGXFSZ', 'SIGVTALRM', 'SIGPROF', 'SIGWINCH', 
                    'SIGIO', 'SIGPWR', 'SIGSYS']
    for sig_name in unix_signals:
        if not hasattr(signal, sig_name):
            setattr(signal, sig_name, getattr(signal, 'SIGTERM', 1))

# --- IMPORTACIONES ---
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from crewai_tools import FileWriterTool 

load_dotenv()

# --- CONFIGURACIÓN DEL CEREBRO ---
llm = ChatGoogleGenerativeAI(
    model="gemini-pro-latest", # Usamos Pro (cuidado con el límite de velocidad)
    verbose=True,
    temperature=0.1,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    max_retries=10,
    request_timeout=120
)

# --- HERRAMIENTA UTF-8 ---
class UTF8FileWriterTool(FileWriterTool):
    name: str = "Save File UTF-8"
    description: str = "Saves content to a file using UTF-8 encoding."

    def _run(self, filename: str, content: str, **kwargs) -> str:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File {filename} saved successfully in UTF-8."
        except Exception as e:
            return f"Error saving file: {e}"

file_writer_tool = UTF8FileWriterTool()

# --- AGENTES ---
product_owner = Agent(
    role='Technical Product Owner',
    goal='Define technical requirements.',
    backstory='Expert PO.',
    llm=llm,
    verbose=True,
    allow_delegation=False
)

developer = Agent(
    role='Senior Python Developer',
    goal='Write code and FIX errors based on feedback.', # Actualizado
    backstory='Expert Python dev. You fix bugs quickly.',
    llm=llm,
    verbose=True,
    allow_delegation=False,
    tools=[file_writer_tool]
)

qa_engineer = Agent(
    role='QA Automation Engineer',
    goal='Write unit tests.',
    backstory='Expert QA engineer.',
    llm=llm,
    verbose=True,
    allow_delegation=False,
    tools=[file_writer_tool]
)

# --- TAREAS INICIALES ---
task_1_specs = Task(
    description='Analyze: "Create a simple calculator in Python (add, subtract) and save history to a text file". Define requirements in English.',
    agent=product_owner,
    expected_output='Requirements list.'
)

task_2_code = Task(
    description='Write Python code. Use "Save File UTF-8" tool to create "calculator.py". All messages in ENGLISH. Ensure you implement the save history logic inside the add/subtract functions.',
    agent=developer,
    expected_output='File saved confirmation.'
)

task_3_test_plan = Task(
    description='Write unittest code. Use "Save File UTF-8" tool to create "test_calculator.py". Use "unittest.mock.mock_open" to avoid file permission errors with Docker.',
    agent=qa_engineer,
    expected_output='File saved confirmation.'
)

# --- INICIALIZACIÓN DEL EQUIPO ---
crew = Crew(
    agents=[product_owner, developer, qa_engineer],
    tasks=[task_1_specs, task_2_code, task_3_test_plan],
    verbose=True,
    process=Process.sequential,
    max_rpm=2 # Freno de mano activado
)

# =================================================================
# 🔄 EL BUCLE DE AUTOCORRECCIÓN (THE FEEDBACK LOOP)
# =================================================================

if __name__ == "__main__":
    print("🚀 Starting Autonomous AI Team...")
    
    # 1. Primera ejecución (Creación desde cero)
    crew.kickoff()
    
    MAX_RETRIES = 3
    current_try = 0
    success = False

    while current_try < MAX_RETRIES and not success:
        print(f"\n\n🧪 TESTING PHASE (Attempt {current_try + 1}/{MAX_RETRIES})")
        print("--------------------------------------------------")
        
        # 2. Ejecutar Docker desde Python
        # Usamos os.getcwd() para obtener la ruta correcta en Windows
        docker_cmd = f'docker run --rm -v "{os.getcwd()}":/app -w /app python:3.10-slim python -m unittest test_calculator.py'
        
        try:
            # Ejecutamos el comando y capturamos la salida (stdout) y errores (stderr)
            result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True)
            
            print(result.stderr) # Imprimir lo que dijo Docker
            
            if result.returncode == 0:
                print("\n✅ SUCCESS! All tests passed.")
                success = True
            else:
                print("\n❌ TESTS FAILED. Initiating self-correction protocol...")
                current_try += 1
                
                if current_try < MAX_RETRIES:
                    # 3. CREAR TAREA DE REPARACIÓN
                    # Le pasamos el error exacto de Docker al agente
                    error_log = result.stderr
                    
                    fix_task = Task(
                        description=f"""
                        CRITICAL FAILURE IN TESTS.
                        
                        Here is the error output from Docker:
                        {error_log}
                        
                        YOUR GOAL: Analyze the error and FIX the code in 'calculator.py' or 'test_calculator.py'.
                        Overwrite the files with the corrected version using the tool.
                        """,
                        agent=developer, # Se lo asignamos al Dev
                        expected_output="Confirmation that files were fixed and saved."
                    )
                    
                    # 4. REINICIAR LA CREW SOLO CON LA TAREA DE FIX
                    crew.tasks = [fix_task]
                    print("🤖 Developer is fixing the code...")
                    crew.kickoff()
                    
        except Exception as e:
            print(f"Error running Docker subprocess: {e}")
            break

    if not success:
        print("\n💀 Maximum retries reached. Human intervention required.")