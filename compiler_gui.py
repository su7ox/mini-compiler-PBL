import streamlit as st
import subprocess
import graphviz
from vm import MiniCompilerVM
import json  
from pathlib import Path
from shutil import which

# Set up page config
st.set_page_config(page_title="Mini Compiler IDE", layout="wide")

BASE_DIR = Path(__file__).resolve().parent

@st.cache_resource
def build_compiler_if_possible():
    """Builds the compiler only once per session if the tools are available."""
    bison = which("bison")
    flex = which("flex")
    gcc = which("gcc")

    if not (bison and flex and gcc):
        return False

    try:
        subprocess.run([bison, "-y", str(BASE_DIR / "lang.y"), "-d"], check=True)
        subprocess.run([flex, str(BASE_DIR / "lang.l")], check=True)
        subprocess.run(
            [gcc, str(BASE_DIR / "lang.c"), str(BASE_DIR / "y.tab.c"), str(BASE_DIR / "lex.yy.c")],
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def draw_ast(json_data):
    graph = graphviz.Digraph()
    graph.attr(rankdir='TB', size='8,8') # Top to Bottom layout
    
    node_counter = [0] # Use a list to mutate inside recursive function

    def add_nodes(node_data, parent_id=None):
        if not node_data:
            return
            
        current_id = str(node_counter[0])
        node_counter[0] += 1
        
        # Determine the label based on if it has a value
        label = f"{node_data.get('type')}"
        if 'value' in node_data:
             label += f"\n({node_data['value']})"
             
        # Add the physical node to the graph
        graph.node(current_id, label, shape='box', style='filled', fillcolor='#f0f2f6')
        
        # Connect to parent if this isn't the root
        if parent_id is not None:
            graph.edge(parent_id, current_id)
            
        # Recursively process children
        if 'children' in node_data:
            for child in node_data['children']:
                if child and isinstance(child, dict):
                    add_nodes(child, current_id)

    add_nodes(json_data)
    return graph

# Initialize build
build_success = build_compiler_if_possible()

# Session State Initialization (to keep data between reruns)
if "code" not in st.session_state:
    st.session_state.code = ""
if "errors" not in st.session_state:
    st.session_state.errors = ""
if "quadruples" not in st.session_state:
    st.session_state.quadruples = ""
if "symtable" not in st.session_state:
    st.session_state.symtable = ""
if "ast_json" not in st.session_state:
    st.session_state.ast_json = None

# --- App Header ---
st.title("Mini Compiler GUI")

if not build_success and not (BASE_DIR / "a.exe").exists():
    st.warning("⚠️ Compiler tools (Bison, Flex, GCC) not found in PATH. Make sure 'a.exe' exists.")

# --- File Uploader ---
uploaded_file = st.file_uploader("Import a File", type=["txt", "py", "c"])
if uploaded_file is not None:
    # Read the file and update the code if a new file is uploaded
    if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
        st.session_state.code = uploaded_file.getvalue().decode("utf-8")
        st.session_state.last_uploaded = uploaded_file.name

# --- Main Layout (3 Columns) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("My IDE")
    # Text area for code input
    code_input = st.text_area("Code", value=st.session_state.code, height=400, label_visibility="collapsed")
    st.session_state.code = code_input # Save changes to state
    
    run_button = st.button("▶ Run Compiler", type="primary", use_container_width=True)

with col2:
    st.subheader("Symbol Table")
    st.text_area("Symbol Table", value=st.session_state.symtable, height=400, disabled=True, label_visibility="collapsed")

with col3:
    st.subheader("Quadruples")
    st.text_area("Quadruples", value=st.session_state.quadruples, height=400, disabled=True, label_visibility="collapsed")

# --- Run Logic ---
if run_button:
    # Clear physical text files before running
    (BASE_DIR / "errors.txt").write_text("")
    (BASE_DIR / "quadruples.txt").write_text("")
    (BASE_DIR / "SymbolTable.txt").write_text("")
    
    # Also clear the old AST file so it doesn't carry over on a syntax error
    ast_path = BASE_DIR / "ast.json"
    if ast_path.exists():
        ast_path.unlink()

    exe_path = BASE_DIR / "a.exe"
    if exe_path.exists():
        try:
            # Run the executable, passing the code input through stdin
            p = subprocess.Popen(str(exe_path), stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=str(BASE_DIR))
            p.communicate(code_input.encode('utf-8'))
            
            # Read errors first
            error_output = (BASE_DIR / "errors.txt").read_text()
            st.session_state.errors = error_output
            
            # If no errors, read quadruples, symbol table, and AST JSON
            if not error_output.strip():
                st.session_state.quadruples = (BASE_DIR / "quadruples.txt").read_text()
                st.session_state.symtable = (BASE_DIR / "SymbolTable.txt").read_text()
                
                # Load the AST JSON
                if ast_path.exists():
                    try:
                        st.session_state.ast_json = json.loads(ast_path.read_text())
                    except Exception as json_e:
                        st.session_state.ast_json = None
                        print(f"JSON Parse Error: {json_e}")
                else:
                    st.session_state.ast_json = None
            else:
                st.session_state.quadruples = ""
                st.session_state.symtable = ""
                st.session_state.ast_json = None
                
            st.rerun() # Refresh the UI to display the newly loaded states

        except Exception as e:
            st.session_state.errors = f"Execution failed: {e}"
            st.rerun()
    else:
        st.session_state.errors = "Error: 'a.exe' not found. Please ensure the compiler is built."
        st.rerun()

# --- Error Console ---
st.divider()
st.subheader("Console / Errors")

if st.session_state.errors.strip():
    st.error(st.session_state.errors)
else:
    st.success("Clean build. No syntax or semantic errors detected.")

# --- Runtime Execution (VM) ---
st.divider()
st.subheader("🖥️ Program Output")

if st.session_state.quadruples.strip():
    # If quadruples exist (meaning it compiled successfully), run the VM!
    try:
        vm = MiniCompilerVM(st.session_state.quadruples)
        program_output = vm.execute()
        
        if program_output:
            st.code(program_output, language="text")
        else:
            st.info("Program finished executing successfully, but did not print anything.")
    except Exception as e:
        st.error(f"Virtual Machine crashed: {e}")
else:
    st.info("Write and run code using the 'print' statement to see output here.")

# --- AST Visualization ---
st.divider()
st.subheader("Abstract Syntax Tree (AST)")

if st.session_state.ast_json:
    try:
        ast_graph = draw_ast(st.session_state.ast_json)
        st.graphviz_chart(ast_graph)
    except Exception as e:
        st.error(f"Could not render AST Graph: {e}")
else:
    st.info("Run a successful, error-free build to generate the AST visualization.")
