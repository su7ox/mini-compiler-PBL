import streamlit as st

import subprocess

import graphviz

from vm import MiniCompilerVM

import json  

from pathlib import Path

from shutil import which



# Set up page config

st.set_page_config(page_title="Mini-C Compiler Pipeline", layout="wide")



BASE_DIR = Path(__file__).resolve().parent



@st.cache_resource

def build_compiler_if_possible():

    bison = which("bison")

    flex = which("flex")

    gcc = which("gcc")

    if not (bison and flex and gcc): return False

    try:

        subprocess.run([bison, "-y", str(BASE_DIR / "lang.y"), "-d"], check=True)

        subprocess.run([flex, str(BASE_DIR / "lang.l")], check=True)

        subprocess.run([gcc, str(BASE_DIR / "lang.c"), str(BASE_DIR / "y.tab.c"), str(BASE_DIR / "lex.yy.c")], check=True)

        return True

    except subprocess.CalledProcessError:

        return False



def draw_ast(json_data):

    graph = graphviz.Digraph()

    # Left to right layout often looks better for deep trees, but TB works too

    graph.attr(rankdir='TB', size='8,8') 

    node_counter = [0]



    def add_nodes(node_data, parent_id=None):

        if not node_data: return

        current_id = str(node_counter[0])

        node_counter[0] += 1

        

        label = f"{node_data.get('type')}"

        if 'value' in node_data: label += f"\n({node_data['value']})"

             

        # Modern, plain background to keep it clean

        graph.node(current_id, label, shape='box', style='filled', fillcolor='#f8f9fa', color="#ced4da")

        

        if parent_id is not None:

            graph.edge(parent_id, current_id, color="#6c757d")

            

        if 'children' in node_data:

            for child in node_data['children']:

                if child and isinstance(child, dict):

                    add_nodes(child, current_id)



    add_nodes(json_data)

    return graph



build_success = build_compiler_if_possible()



if "code" not in st.session_state: st.session_state.code = ""

if "errors" not in st.session_state: st.session_state.errors = ""

if "tokens" not in st.session_state: st.session_state.tokens = ""

if "quadruples" not in st.session_state: st.session_state.quadruples = ""

if "symtable" not in st.session_state: st.session_state.symtable = ""

if "ast_json" not in st.session_state: st.session_state.ast_json = None



# --- App Header ---

st.title("⚙️ Mini-C Compiler Visualizer")

st.markdown("Write code on the left and inspect the 5-step compilation pipeline on the right.")



# --- Main Layout ---

col_code, col_viz = st.columns([1, 1.5])



with col_code:

    st.subheader("Source Code")

    code_input = st.text_area("Code", value=st.session_state.code, height=500, label_visibility="collapsed")

    st.session_state.code = code_input

    

    run_button = st.button("▶ Compile & Execute", type="primary", use_container_width=True)



with col_viz:

    st.subheader("Pipeline Inspector")

    tab_tok, tab_ast, tab_sym, tab_ir, tab_out = st.tabs([

        "1. Lexer (Tokens)", 

        "2. Parser (AST)", 

        "3. Semantic (Symbols)", 

        "4. IR (Quadruples)", 

        "5. VM (Output)"

    ])



# --- Run Logic ---

if run_button:

    # 1. Clear all previous artifacts

    for file in ["errors.txt", "quadruples.txt", "SymbolTable.txt", "tokens.txt"]:

        (BASE_DIR / file).write_text("")

    if (BASE_DIR / "ast.json").exists(): (BASE_DIR / "ast.json").unlink()



    exe_path = BASE_DIR / "a.exe"

    if exe_path.exists():

        try:

            # 2. Run Compiler

            p = subprocess.Popen(str(exe_path), stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=str(BASE_DIR))

            p.communicate(code_input.encode('utf-8'))

            

            # 3. Read Output State

            st.session_state.errors = (BASE_DIR / "errors.txt").read_text()

            st.session_state.tokens = (BASE_DIR / "tokens.txt").read_text()

            

            if not st.session_state.errors.strip():

                st.session_state.quadruples = (BASE_DIR / "quadruples.txt").read_text()

                st.session_state.symtable = (BASE_DIR / "SymbolTable.txt").read_text()

                ast_path = BASE_DIR / "ast.json"

                st.session_state.ast_json = json.loads(ast_path.read_text()) if ast_path.exists() else None

            else:

                st.session_state.quadruples = ""

                st.session_state.symtable = ""

                st.session_state.ast_json = None

                

            st.rerun()



        except Exception as e:

            st.session_state.errors = f"Execution failed: {e}"

            st.rerun()

    else:

        st.error("Compiler executable not found.")



# --- Tab Content Rendering ---

with tab_tok:

    if st.session_state.tokens: st.code(st.session_state.tokens, language="text")

    else: st.info("Tokens will appear here after compilation.")



with tab_ast:

    if st.session_state.ast_json:

        st.graphviz_chart(draw_ast(st.session_state.ast_json), use_container_width=True)

    else:

        st.info("AST will be drawn here if there are no syntax errors.")



with tab_sym:

    if st.session_state.symtable: st.code(st.session_state.symtable, language="text")

    else: st.info("Symbol Table populated during semantic analysis.")



with tab_ir:

    if st.session_state.quadruples: st.code(st.session_state.quadruples, language="assembly")

    else: st.info("Intermediate Representation (IR) generation.")



with tab_out:

    if st.session_state.errors.strip():

        st.error("Compilation Failed:")

        st.code(st.session_state.errors, language="text")

    elif st.session_state.quadruples.strip():

        try:

            vm = MiniCompilerVM(st.session_state.quadruples)

            output = vm.execute()

            if output:

                st.success("Execution Successful")

                st.code(output, language="console")

            else:

                st.warning("Program finished but did not output anything.")

        except Exception as e:

            st.error(f"VM Crash: {e}")
