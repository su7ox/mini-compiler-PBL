import streamlit as st
import subprocess
import graphviz
from vm import MiniCompilerVM
import json  
from pathlib import Path
from shutil import which
import platform

# Set up page config
st.set_page_config(page_title="Mini-C Compiler Pipeline", layout="wide")

BASE_DIR = Path(__file__).resolve().parent

# Determine executable name based on OS
EXE_NAME = "a.exe" if platform.system() == "Windows" else "a.out"
EXE_PATH = BASE_DIR / EXE_NAME

def build_compiler():
    """Explicitly runs Bison, Flex, and GCC and returns the status."""
    missing_tools = []
    if not which("bison"): missing_tools.append("Bison")
    if not which("flex"): missing_tools.append("Flex")
    if not which("gcc"): missing_tools.append("GCC")
    
    if missing_tools:
        return False, f"Missing tools in System PATH: {', '.join(missing_tools)}. Please install them."

    try:
        # Run Bison
        st.sidebar.text("Running: bison -y lang.y -d")
        subprocess.run(["bison", "-y", "lang.y", "-d"], check=True, cwd=str(BASE_DIR), capture_output=True, text=True)
        
        # Run Flex
        st.sidebar.text("Running: flex lang.l")
        subprocess.run(["flex", "lang.l"], check=True, cwd=str(BASE_DIR), capture_output=True, text=True)
        
        # Run GCC
        st.sidebar.text("Running: gcc lang.c y.tab.c lex.yy.c")
        subprocess.run(["gcc", "lang.c", "y.tab.c", "lex.yy.c"], check=True, cwd=str(BASE_DIR), capture_output=True, text=True)
        
        return True, f"Successfully built {EXE_NAME}!"
    except subprocess.CalledProcessError as e:
        return False, f"Build failed!\nError: {e.stderr}"

def draw_ast(json_data):
    graph = graphviz.Digraph()
    graph.attr(rankdir='TB', size='8,8') 
    node_counter = [0]

    def add_nodes(node_data, parent_id=None):
        if not node_data: return
        current_id = str(node_counter[0])
        node_counter[0] += 1
        
        label = f"{node_data.get('type')}"
        if 'value' in node_data: label += f"\n({node_data['value']})"
             
        graph.node(current_id, label, shape='box', style='filled', fillcolor='#f8f9fa', color="#ced4da")
        
        if parent_id is not None:
            graph.edge(parent_id, current_id, color="#6c757d")
            
        if 'children' in node_data:
            for child in node_data['children']:
                if child and isinstance(child, dict):
                    add_nodes(child, current_id)

    add_nodes(json_data)
    return graph

# Initialize State
if "code" not in st.session_state: st.session_state.code = ""
if "errors" not in st.session_state: st.session_state.errors = ""
if "tokens" not in st.session_state: st.session_state.tokens = ""
if "quadruples" not in st.session_state: st.session_state.quadruples = ""
if "symtable" not in st.session_state: st.session_state.symtable = ""
if "ast_json" not in st.session_state: st.session_state.ast_json = None

# --- Sidebar: Compiler Build Tools ---
with st.sidebar:
    st.header("⚙️ Backend Builder")
    st.markdown("Compile the C/Flex/Bison backend before running your code.")
    
    if st.button("🛠️ Build Compiler", type="secondary", use_container_width=True):
        with st.spinner("Building backend..."):
            success, message = build_compiler()
            if success:
                st.success(message)
            else:
                st.error(message)
                
    st.divider()
    if EXE_PATH.exists():
        st.success(f"✅ Backend ready ({EXE_NAME} found)")
    else:
        st.warning(f"⚠️ Backend missing ({EXE_NAME} not found). Please click Build Compiler.")

# --- App Header ---
st.title("🖥️ Mini-C Compiler Visualizer")
st.markdown("Write C-like code on the left and inspect the step-by-step compilation pipeline on the right.")

# --- File Uploader ---
uploaded_file = st.file_uploader("Import a file (.c or .txt)", type=["txt", "py", "c"])
if uploaded_file is not None:
    if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
        st.session_state.code = uploaded_file.getvalue().decode("utf-8")
        st.session_state.last_uploaded = uploaded_file.name

# --- Main Layout ---
col_code, col_viz = st.columns([1, 1.5])

with col_code:
    st.subheader("📝 Source Code")
    code_input = st.text_area("Code", value=st.session_state.code, height=600, label_visibility="collapsed")
    st.session_state.code = code_input
    
    run_button = st.button("▶ Compile & Execute Code", type="primary", use_container_width=True)

# --- Run Logic (Moved up so states update before rendering the right column) ---
if run_button:
    if not EXE_PATH.exists():
        st.error("Cannot run code: Compiler backend is not built. Please use the sidebar to build the compiler first.")
    else:
        for file in ["errors.txt", "quadruples.txt", "SymbolTable.txt", "tokens.txt"]:
            (BASE_DIR / file).write_text("")
        if (BASE_DIR / "ast.json").exists(): (BASE_DIR / "ast.json").unlink()

        try:
            p = subprocess.Popen(str(EXE_PATH), stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=str(BASE_DIR))
            p.communicate(code_input.encode('utf-8'))
            
            st.session_state.errors = (BASE_DIR / "errors.txt").read_text() if (BASE_DIR / "errors.txt").exists() else ""
            st.session_state.tokens = (BASE_DIR / "tokens.txt").read_text() if (BASE_DIR / "tokens.txt").exists() else ""
            
            if not st.session_state.errors.strip():
                st.session_state.quadruples = (BASE_DIR / "quadruples.txt").read_text() if (BASE_DIR / "quadruples.txt").exists() else ""
                st.session_state.symtable = (BASE_DIR / "SymbolTable.txt").read_text() if (BASE_DIR / "SymbolTable.txt").exists() else ""
                ast_path = BASE_DIR / "ast.json"
                st.session_state.ast_json = json.loads(ast_path.read_text()) if ast_path.exists() else None
            else:
                st.session_state.quadruples = ""
                st.session_state.symtable = ""
                st.session_state.ast_json = None
                
        except Exception as e:
            st.session_state.errors = f"Execution failed: {e}"

with col_viz:
    st.subheader("🔍 Pipeline Inspector")
    st.markdown("Follow the compilation process top-to-bottom.")

    # 1. Lexer
    with st.expander("🧩 1. Lexical Analysis (Tokens)", expanded=False):
        if st.session_state.tokens: 
            st.code(st.session_state.tokens, language="text")
        else: 
            st.info("Tokens will appear here after compilation.")

    # 2. Parser
    with st.expander("🌳 2. Syntax Analysis (AST)", expanded=False):
        if st.session_state.ast_json:
            st.graphviz_chart(draw_ast(st.session_state.ast_json), use_container_width=True)
        else:
            st.info("AST will be drawn here if there are no syntax errors.")

    # 3. Semantic
    with st.expander("📖 3. Semantic Analysis (Symbol Table)", expanded=False):
        if st.session_state.symtable: 
            st.code(st.session_state.symtable, language="text")
        else: 
            st.info("Symbol Table populated during semantic analysis.")

    # 4. IR
    with st.expander("⚙️ 4. Intermediate Representation (Quadruples)", expanded=False):
        if st.session_state.quadruples: 
            st.code(st.session_state.quadruples, language="assembly")
        else: 
            st.info("Intermediate Representation (IR) generation.")

    # 5. Output (Expanded by default so users immediately see results)
    with st.expander("💻 5. Virtual Machine (Execution Output)", expanded=True):
        if st.session_state.errors.strip():
            st.error("🚨 Compilation Failed:")
            st.code(st.session_state.errors, language="text")
        elif st.session_state.quadruples.strip():
            try:
                vm = MiniCompilerVM(st.session_state.quadruples)
                output = vm.execute()
                if output:
                    st.success("✅ Execution Successful")
                    st.code(output, language="console")
                else:
                    st.warning("⚠️ Program finished but did not output anything.")
            except Exception as e:
                st.error(f" VM Crash: {e}")
        else:
            st.info("Run your code to see the output here.")
