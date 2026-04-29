# vm.py
class MiniCompilerVM:
    def __init__(self, ir_code):
        # Clean up and split the instructions
        raw_lines = [line.strip() for line in ir_code.strip().split('\n') if line.strip()]
        self.instructions = []
        self.labels = {}
        
        # Pass 1: Map all labels to their instruction index
        for line in raw_lines:
            if line.endswith(':'):
                self.labels[line[:-1]] = len(self.instructions)
            else:
                parts = line.split()
                opcode = parts[0]
                arg = parts[1] if len(parts) > 1 else None
                self.instructions.append((opcode, arg))

        self.stack = []
        self.variables = {}
        self.call_stack = []
        self.output = []
        self.ip = 0 # Instruction Pointer

    def execute(self):
        while self.ip < len(self.instructions):
            opcode, arg = self.instructions[self.ip]
            
            try:
                if opcode == 'push':
                    self._handle_push(arg)
                elif opcode == 'pop':
                    if arg: # Pop into a variable
                        self.variables[arg] = self.stack.pop()
                    else:
                        self.stack.pop() # Discard top of stack
                
                # Arithmetic
                elif opcode == 'add':
                    b = self.stack.pop(); a = self.stack.pop()
                    self.stack.append(a + b)
                elif opcode == 'sub':
                    b = self.stack.pop(); a = self.stack.pop()
                    self.stack.append(a - b)
                elif opcode == 'mul':
                    b = self.stack.pop(); a = self.stack.pop()
                    self.stack.append(a * b)
                elif opcode == 'div':
                    b = self.stack.pop(); a = self.stack.pop()
                    self.stack.append(a / b if b != 0 else 0)
                elif opcode == 'neg':
                    self.stack.append(-self.stack.pop())
                    
                # Print
                elif opcode == 'print':
                    self.output.append(str(self.stack.pop()))
                    
                # Jumps and Control Flow
                elif opcode == 'jmp':
                    self.ip = self.labels[arg]
                    continue
                elif opcode == 'jz': # Jump if Zero
                    if not self.stack.pop():
                        self.ip = self.labels[arg]
                        continue
                elif opcode == 'jnz': # Jump if Not Zero
                    if self.stack.pop():
                        self.ip = self.labels[arg]
                        continue
                        
                # Comparisons
                elif opcode.startswith('comp'):
                    self._handle_comp(opcode)
                
                # Functions
                elif opcode == 'call':
                    self.call_stack.append(self.ip)
                    self.ip = self.labels[arg]
                    continue
                elif opcode == 'ret':
                    self.ip = self.call_stack.pop()

            except Exception as e:
                self.output.append(f"RUNTIME ERROR at instruction {self.ip} ({opcode}): {str(e)}")
                break
                
            self.ip += 1
            
        return "\n".join(self.output)

    def _handle_push(self, arg):
        # Determine data type and push to stack
        if arg.isdigit() or (arg.startswith('-') and arg[1:].isdigit()):
            self.stack.append(int(arg))
        elif arg.replace('.', '', 1).isdigit():
            self.stack.append(float(arg))
        elif arg == 'true': self.stack.append(True)
        elif arg == 'false': self.stack.append(False)
        elif arg.startswith('"') or arg.startswith("'"): 
            self.stack.append(arg.strip('"\''))
        else:
            # It's a variable
            self.stack.append(self.variables.get(arg, 0))

    def _handle_comp(self, opcode):
        b = self.stack.pop()
        a = self.stack.pop()
        if opcode == 'compGT': self.stack.append(a > b)
        elif opcode == 'compLT': self.stack.append(a < b)
        elif opcode == 'compGE': self.stack.append(a >= b)
        elif opcode == 'compLE': self.stack.append(a <= b)
        elif opcode == 'compEQ': self.stack.append(a == b)
        elif opcode == 'compNE': self.stack.append(a != b)
        elif opcode == 'compAND': self.stack.append(a and b)
        elif opcode == 'compOR': self.stack.append(a or b)